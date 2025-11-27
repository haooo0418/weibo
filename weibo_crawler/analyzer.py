"""
Weibo Analyzer - 微博分析模块

This module provides functionality to analyze Weibo posts content,
including sentiment analysis, word frequency analysis, and more.
"""

import re
import logging
from collections import Counter
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class WeiboAnalyzer:
    """
    微博内容分析器
    
    提供微博内容的各种分析功能：
    - 词频分析
    - 情感分析（简单版本）
    - 发布时间分析
    - 互动数据统计
    """
    
    # 常见停用词
    STOP_WORDS = {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
        "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
        "没有", "看", "好", "自己", "这", "那", "还", "能", "让", "这个",
        "他", "她", "它", "们", "什么", "怎么", "为什么", "哪", "哪里",
        "但是", "而且", "所以", "因为", "如果", "虽然", "然后", "或者",
        "可以", "应该", "需要", "已经", "正在", "还是", "只是", "真的",
        "网页", "链接", "全文", "转发", "评论", "赞", "分享", "收藏",
        "http", "https", "www", "com", "cn",
    }
    
    # 简单情感词典
    POSITIVE_WORDS = {
        "喜欢", "爱", "开心", "快乐", "幸福", "高兴", "美好", "棒", "好",
        "优秀", "赞", "厉害", "感谢", "谢谢", "支持", "加油", "期待",
        "漂亮", "美丽", "帅", "酷", "精彩", "完美", "成功", "胜利",
        "温暖", "感动", "惊喜", "满意", "舒服", "愉快", "兴奋", "激动",
    }
    
    NEGATIVE_WORDS = {
        "讨厌", "恨", "难过", "伤心", "失望", "生气", "愤怒", "烦", "累",
        "糟糕", "差", "坏", "失败", "错误", "问题", "麻烦", "困难",
        "担心", "焦虑", "紧张", "害怕", "恐惧", "悲伤", "痛苦", "后悔",
        "无聊", "郁闷", "烦躁", "沮丧", "绝望", "崩溃", "崩", "哭",
    }
    
    def __init__(self, weibos: list[dict]):
        """
        初始化分析器
        
        Args:
            weibos: 微博列表，每条微博为包含text字段的字典
        """
        self.weibos = weibos
        self._jieba_loaded = False
    
    def _load_jieba(self):
        """延迟加载jieba分词库"""
        if not self._jieba_loaded:
            try:
                import jieba
                self._jieba = jieba
                self._jieba_loaded = True
            except ImportError:
                logger.warning("jieba not installed, using simple tokenization")
                self._jieba = None
                self._jieba_loaded = True
    
    def _tokenize(self, text: str) -> list[str]:
        """
        对文本进行分词
        
        Args:
            text: 输入文本
            
        Returns:
            分词后的词语列表
        """
        self._load_jieba()
        
        # 清理特殊字符和URL
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'@[\w\u4e00-\u9fff]+', '', text)
        text = re.sub(r'#[\w\u4e00-\u9fff]+#', '', text)
        text = re.sub(r'【.*?】', '', text)
        text = re.sub(r'\[.*?\]', '', text)  # 表情
        
        if self._jieba:
            words = self._jieba.lcut(text)
        else:
            # 简单分词：按字符分割
            words = list(text)
        
        # 过滤停用词和短词
        words = [
            w.strip() for w in words 
            if w.strip() and 
               len(w.strip()) > 1 and 
               w.strip() not in self.STOP_WORDS and
               not w.isdigit()
        ]
        
        return words
    
    def word_frequency(self, top_n: int = 20) -> list[tuple[str, int]]:
        """
        统计词频
        
        Args:
            top_n: 返回词频最高的前N个词
            
        Returns:
            (词, 频率) 元组列表
        """
        all_words = []
        for weibo in self.weibos:
            text = weibo.get("text", "")
            words = self._tokenize(text)
            all_words.extend(words)
        
        counter = Counter(all_words)
        return counter.most_common(top_n)
    
    def sentiment_analysis(self) -> dict:
        """
        简单情感分析
        
        Returns:
            包含正面、负面、中性微博数量及比例的字典
        """
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        sentiment_details = []
        
        for weibo in self.weibos:
            text = weibo.get("text", "")
            
            pos_score = sum(1 for word in self.POSITIVE_WORDS if word in text)
            neg_score = sum(1 for word in self.NEGATIVE_WORDS if word in text)
            
            if pos_score > neg_score:
                sentiment = "positive"
                positive_count += 1
            elif neg_score > pos_score:
                sentiment = "negative"
                negative_count += 1
            else:
                sentiment = "neutral"
                neutral_count += 1
            
            sentiment_details.append({
                "id": weibo.get("id"),
                "text": text[:50] + "..." if len(text) > 50 else text,
                "sentiment": sentiment,
                "positive_score": pos_score,
                "negative_score": neg_score,
            })
        
        total = len(self.weibos) or 1  # 避免除零
        
        return {
            "summary": {
                "total": len(self.weibos),
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "positive_ratio": round(positive_count / total * 100, 2),
                "negative_ratio": round(negative_count / total * 100, 2),
                "neutral_ratio": round(neutral_count / total * 100, 2),
            },
            "details": sentiment_details,
        }
    
    def time_distribution(self) -> dict:
        """
        分析发布时间分布
        
        Returns:
            按小时和星期统计的发布数量
        """
        hourly = Counter()
        daily = Counter()
        monthly = Counter()
        
        for weibo in self.weibos:
            parsed_date = weibo.get("parsed_date")
            if isinstance(parsed_date, datetime):
                hourly[parsed_date.hour] += 1
                daily[parsed_date.strftime("%A")] += 1
                monthly[parsed_date.strftime("%Y-%m")] += 1
        
        return {
            "hourly": dict(sorted(hourly.items())),
            "daily": dict(daily),
            "monthly": dict(sorted(monthly.items())),
        }
    
    def engagement_stats(self) -> dict:
        """
        统计互动数据
        
        Returns:
            转发、评论、点赞的统计数据
        """
        reposts = []
        comments = []
        attitudes = []
        
        for weibo in self.weibos:
            reposts.append(weibo.get("reposts_count", 0))
            comments.append(weibo.get("comments_count", 0))
            attitudes.append(weibo.get("attitudes_count", 0))
        
        def calc_stats(data: list) -> dict:
            if not data:
                return {"total": 0, "avg": 0, "max": 0, "min": 0}
            return {
                "total": sum(data),
                "avg": round(sum(data) / len(data), 2),
                "max": max(data),
                "min": min(data),
            }
        
        # 找出互动最多的微博
        top_weibos = sorted(
            self.weibos,
            key=lambda x: (
                x.get("reposts_count", 0) + 
                x.get("comments_count", 0) + 
                x.get("attitudes_count", 0)
            ),
            reverse=True
        )[:5]
        
        return {
            "reposts": calc_stats(reposts),
            "comments": calc_stats(comments),
            "attitudes": calc_stats(attitudes),
            "top_weibos": [
                {
                    "id": w.get("id"),
                    "text": w.get("text", "")[:50] + "..." if len(w.get("text", "")) > 50 else w.get("text", ""),
                    "total_engagement": (
                        w.get("reposts_count", 0) + 
                        w.get("comments_count", 0) + 
                        w.get("attitudes_count", 0)
                    ),
                }
                for w in top_weibos
            ],
        }
    
    def generate_report(self) -> dict:
        """
        生成完整分析报告
        
        Returns:
            包含所有分析结果的字典
        """
        return {
            "total_weibos": len(self.weibos),
            "word_frequency": self.word_frequency(),
            "sentiment": self.sentiment_analysis(),
            "time_distribution": self.time_distribution(),
            "engagement": self.engagement_stats(),
            "generated_at": datetime.now().isoformat(),
        }
    
    def print_report(self):
        """打印分析报告到控制台"""
        report = self.generate_report()
        
        print("\n" + "=" * 60)
        print("微博分析报告")
        print("=" * 60)
        
        print(f"\n📊 总微博数: {report['total_weibos']}")
        
        print("\n📝 词频TOP 20:")
        for word, count in report['word_frequency']:
            print(f"  {word}: {count}")
        
        sentiment = report['sentiment']['summary']
        print("\n😊 情感分析:")
        print(f"  正面: {sentiment['positive']} ({sentiment['positive_ratio']}%)")
        print(f"  负面: {sentiment['negative']} ({sentiment['negative_ratio']}%)")
        print(f"  中性: {sentiment['neutral']} ({sentiment['neutral_ratio']}%)")
        
        time_dist = report['time_distribution']
        print("\n⏰ 发布时间分布 (按小时):")
        for hour, count in sorted(time_dist['hourly'].items()):
            print(f"  {hour:02d}:00 - {count}条")
        
        engagement = report['engagement']
        print("\n💬 互动统计:")
        print(f"  转发 - 总计: {engagement['reposts']['total']}, "
              f"平均: {engagement['reposts']['avg']}")
        print(f"  评论 - 总计: {engagement['comments']['total']}, "
              f"平均: {engagement['comments']['avg']}")
        print(f"  点赞 - 总计: {engagement['attitudes']['total']}, "
              f"平均: {engagement['attitudes']['avg']}")
        
        print("\n🔥 互动最多的微博:")
        for i, w in enumerate(engagement['top_weibos'], 1):
            print(f"  {i}. {w['text']} (互动: {w['total_engagement']})")
        
        print("\n" + "=" * 60)
        print(f"报告生成时间: {report['generated_at']}")
        print("=" * 60 + "\n")
