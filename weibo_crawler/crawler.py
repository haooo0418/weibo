"""
Weibo Crawler - 微博爬虫模块

This module provides functionality to crawl Weibo posts from users
within a specified time range.
"""

import time
import random
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)


class WeiboCrawler:
    """
    微博爬虫类
    
    用于爬取指定用户在特定时间段内发布的微博内容。
    
    Attributes:
        user_id: 目标用户的微博ID
        cookie: 登录后的cookie，用于访问需要登录的内容
        start_date: 开始日期
        end_date: 结束日期
    """
    
    BASE_URL = "https://m.weibo.cn/api/container/getIndex"
    
    def __init__(
        self,
        user_id: str,
        cookie: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        初始化微博爬虫
        
        Args:
            user_id: 微博用户ID
            cookie: 登录cookie（可选，但某些内容需要登录才能访问）
            start_date: 开始日期，格式为 YYYY-MM-DD
            end_date: 结束日期，格式为 YYYY-MM-DD
        """
        self.user_id = user_id
        self.cookie = cookie
        self.start_date = self._parse_date(start_date) if start_date else None
        self.end_date = self._parse_date(end_date) if end_date else None
        self.session = self._create_session()
        
    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        return datetime.strptime(date_str, "%Y-%m-%d")
    
    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                          "Mobile/15E148 MicroMessenger/7.0.18(0x17001229)",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://m.weibo.cn/",
            "X-Requested-With": "XMLHttpRequest",
        })
        if self.cookie:
            session.headers["Cookie"] = self.cookie
        return session
    
    def _get_container_id(self) -> Optional[str]:
        """获取用户微博容器ID"""
        params = {
            "type": "uid",
            "value": self.user_id
        }
        try:
            resp = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("ok") != 1:
                logger.error("Failed to get user info: %s", data.get("msg"))
                return None
            
            # 查找微博容器
            tabs = data.get("data", {}).get("tabsInfo", {}).get("tabs", [])
            for tab in tabs:
                if tab.get("tabKey") == "weibo":
                    return tab.get("containerid")
            
            return None
        except requests.RequestException as e:
            logger.error("Request failed: %s", e)
            return None
    
    def _parse_weibo_date(self, date_str: str) -> Optional[datetime]:
        """
        解析微博时间字符串
        
        微博时间格式可能是：
        - "刚刚"
        - "X分钟前"
        - "X小时前"
        - "昨天 HH:MM"
        - "MM-DD"
        - "YYYY-MM-DD HH:MM"
        """
        now = datetime.now()
        
        if not date_str:
            return None
            
        try:
            if "刚刚" in date_str:
                return now
            elif "分钟前" in date_str:
                minutes = int(date_str.replace("分钟前", ""))
                return datetime(now.year, now.month, now.day, now.hour, 
                              max(0, now.minute - minutes))
            elif "小时前" in date_str:
                hours = int(date_str.replace("小时前", ""))
                return datetime(now.year, now.month, now.day, 
                              max(0, now.hour - hours), now.minute)
            elif "昨天" in date_str:
                time_part = date_str.replace("昨天 ", "")
                hour, minute = map(int, time_part.split(":"))
                yesterday = now.replace(day=now.day - 1)
                return datetime(yesterday.year, yesterday.month, yesterday.day, 
                              hour, minute)
            elif "-" in date_str and ":" in date_str:
                # YYYY-MM-DD HH:MM 或 MM-DD HH:MM
                if date_str.count("-") == 2:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                else:
                    return datetime.strptime(f"{now.year}-{date_str}", "%Y-%m-%d %H:%M")
            elif "-" in date_str:
                # MM-DD
                return datetime.strptime(f"{now.year}-{date_str}", "%Y-%m-%d")
            else:
                return None
        except (ValueError, TypeError) as e:
            logger.warning("Failed to parse date '%s': %s", date_str, e)
            return None
    
    def _extract_weibo_content(self, card: dict) -> Optional[dict]:
        """
        从卡片数据中提取微博内容
        
        Args:
            card: 微博卡片数据
            
        Returns:
            提取的微博信息字典，包含id、文本、图片、创建时间等
        """
        mblog = card.get("mblog")
        if not mblog:
            return None
        
        weibo_id = mblog.get("id")
        text = mblog.get("text", "")
        
        # 清理HTML标签
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        created_at = mblog.get("created_at", "")
        parsed_date = self._parse_weibo_date(created_at)
        
        # 提取图片URL
        pics = []
        if "pics" in mblog:
            pics = [pic.get("url", "") for pic in mblog.get("pics", [])]
        
        # 提取转发/评论/点赞数
        reposts_count = mblog.get("reposts_count", 0)
        comments_count = mblog.get("comments_count", 0)
        attitudes_count = mblog.get("attitudes_count", 0)
        
        return {
            "id": weibo_id,
            "text": clean_text,
            "raw_text": text,
            "created_at": created_at,
            "parsed_date": parsed_date,
            "pics": pics,
            "reposts_count": reposts_count,
            "comments_count": comments_count,
            "attitudes_count": attitudes_count,
            "source": mblog.get("source", ""),
        }
    
    def _is_in_date_range(self, weibo_date: Optional[datetime]) -> bool:
        """检查微博日期是否在指定范围内"""
        if weibo_date is None:
            return True  # 无法解析日期时默认包含
        
        if self.start_date and weibo_date < self.start_date:
            return False
        if self.end_date and weibo_date > self.end_date:
            return False
        return True
    
    def _is_before_start_date(self, weibo_date: Optional[datetime]) -> bool:
        """检查微博日期是否早于开始日期"""
        if weibo_date is None or self.start_date is None:
            return False
        return weibo_date < self.start_date
    
    def crawl(self, max_pages: int = 50) -> list[dict]:
        """
        爬取用户微博
        
        Args:
            max_pages: 最大爬取页数，默认50页
            
        Returns:
            微博列表，每条微博为一个字典
        """
        container_id = self._get_container_id()
        if not container_id:
            logger.error("Cannot get container_id for user %s", self.user_id)
            return []
        
        weibos = []
        page = 1
        since_id = ""
        
        while page <= max_pages:
            logger.info("Crawling page %d for user %s", page, self.user_id)
            
            params = {
                "type": "uid",
                "value": self.user_id,
                "containerid": container_id,
            }
            if since_id:
                params["since_id"] = since_id
            
            try:
                resp = self.session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                
                if data.get("ok") != 1:
                    logger.warning("API returned error: %s", data.get("msg"))
                    break
                
                cards = data.get("data", {}).get("cards", [])
                if not cards:
                    logger.info("No more cards found")
                    break
                
                # 获取下一页的since_id
                card_info = data.get("data", {}).get("cardlistInfo", {})
                since_id = card_info.get("since_id", "")
                
                stop_crawling = False
                for card in cards:
                    if card.get("card_type") != 9:
                        continue
                    
                    weibo = self._extract_weibo_content(card)
                    if weibo:
                        # 检查日期范围
                        if self._is_before_start_date(weibo.get("parsed_date")):
                            logger.info("Reached weibos before start date, stopping")
                            stop_crawling = True
                            break
                        
                        if self._is_in_date_range(weibo.get("parsed_date")):
                            weibos.append(weibo)
                            logger.debug("Found weibo: %s", weibo.get("id"))
                
                if stop_crawling:
                    break
                
                page += 1
                
                # 添加随机延迟，避免被封
                time.sleep(random.uniform(1, 3))
                
            except requests.RequestException as e:
                logger.error("Request failed on page %d: %s", page, e)
                break
            except ValueError as e:
                logger.error("Failed to parse response: %s", e)
                break
        
        logger.info("Crawled %d weibos for user %s", len(weibos), self.user_id)
        return weibos
    
    def crawl_by_keyword(self, keyword: str, max_pages: int = 10) -> list[dict]:
        """
        根据关键词搜索微博
        
        Args:
            keyword: 搜索关键词
            max_pages: 最大搜索页数
            
        Returns:
            搜索到的微博列表
        """
        weibos = []
        search_url = "https://m.weibo.cn/api/container/getIndex"
        
        for page in range(1, max_pages + 1):
            logger.info("Searching page %d for keyword '%s'", page, keyword)
            
            params = {
                "containerid": f"100103type=1&q={keyword}",
                "page_type": "searchall",
                "page": page,
            }
            
            try:
                resp = self.session.get(search_url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                
                if data.get("ok") != 1:
                    break
                
                cards = data.get("data", {}).get("cards", [])
                if not cards:
                    break
                
                for card in cards:
                    if card.get("card_type") == 9:
                        weibo = self._extract_weibo_content(card)
                        if weibo and self._is_in_date_range(weibo.get("parsed_date")):
                            weibos.append(weibo)
                    elif card.get("card_type") == 11:
                        # 卡片组
                        for inner_card in card.get("card_group", []):
                            if inner_card.get("card_type") == 9:
                                weibo = self._extract_weibo_content(inner_card)
                                if weibo and self._is_in_date_range(weibo.get("parsed_date")):
                                    weibos.append(weibo)
                
                time.sleep(random.uniform(1, 3))
                
            except requests.RequestException as e:
                logger.error("Search request failed: %s", e)
                break
        
        return weibos
