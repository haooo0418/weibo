"""
Tests for Weibo Crawler
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from weibo_crawler.crawler import WeiboCrawler


class TestWeiboCrawler(unittest.TestCase):
    """测试微博爬虫类"""
    
    def setUp(self):
        """设置测试环境"""
        self.crawler = WeiboCrawler(
            user_id="1234567890",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.crawler.user_id, "1234567890")
        self.assertEqual(self.crawler.start_date, datetime(2024, 1, 1))
        self.assertEqual(self.crawler.end_date, datetime(2024, 12, 31))
    
    def test_parse_date(self):
        """测试日期解析"""
        crawler = WeiboCrawler(user_id="test")
        
        # 测试标准日期格式
        result = crawler._parse_date("2024-06-15")
        self.assertEqual(result, datetime(2024, 6, 15))
    
    def test_parse_weibo_date_now(self):
        """测试解析'刚刚'"""
        result = self.crawler._parse_weibo_date("刚刚")
        self.assertIsNotNone(result)
        self.assertEqual(result.date(), datetime.now().date())
    
    def test_parse_weibo_date_minutes_ago(self):
        """测试解析'X分钟前'"""
        result = self.crawler._parse_weibo_date("5分钟前")
        self.assertIsNotNone(result)
    
    def test_parse_weibo_date_hours_ago(self):
        """测试解析'X小时前'"""
        result = self.crawler._parse_weibo_date("3小时前")
        self.assertIsNotNone(result)
    
    def test_parse_weibo_date_full_format(self):
        """测试解析完整日期格式"""
        result = self.crawler._parse_weibo_date("2024-06-15 14:30")
        self.assertEqual(result, datetime(2024, 6, 15, 14, 30))
    
    def test_parse_weibo_date_invalid(self):
        """测试解析无效日期"""
        result = self.crawler._parse_weibo_date("invalid date")
        self.assertIsNone(result)
    
    def test_parse_weibo_date_empty(self):
        """测试解析空字符串"""
        result = self.crawler._parse_weibo_date("")
        self.assertIsNone(result)
    
    def test_is_in_date_range(self):
        """测试日期范围检查"""
        # 在范围内
        date_in_range = datetime(2024, 6, 15)
        self.assertTrue(self.crawler._is_in_date_range(date_in_range))
        
        # 在开始日期之前
        date_before = datetime(2023, 12, 31)
        self.assertFalse(self.crawler._is_in_date_range(date_before))
        
        # 在结束日期之后
        date_after = datetime(2025, 1, 1)
        self.assertFalse(self.crawler._is_in_date_range(date_after))
        
        # None日期默认包含
        self.assertTrue(self.crawler._is_in_date_range(None))
    
    def test_is_before_start_date(self):
        """测试是否早于开始日期"""
        date_before = datetime(2023, 12, 31)
        self.assertTrue(self.crawler._is_before_start_date(date_before))
        
        date_after = datetime(2024, 6, 15)
        self.assertFalse(self.crawler._is_before_start_date(date_after))
    
    def test_extract_weibo_content(self):
        """测试提取微博内容"""
        card = {
            "mblog": {
                "id": "12345",
                "text": "<p>测试微博内容</p>",
                "created_at": "2024-06-15 10:00",
                "reposts_count": 10,
                "comments_count": 20,
                "attitudes_count": 30,
                "source": "iPhone客户端",
            }
        }
        
        result = self.crawler._extract_weibo_content(card)
        
        self.assertEqual(result["id"], "12345")
        self.assertEqual(result["text"], "测试微博内容")  # HTML标签被清理
        self.assertEqual(result["reposts_count"], 10)
        self.assertEqual(result["comments_count"], 20)
        self.assertEqual(result["attitudes_count"], 30)
    
    def test_extract_weibo_content_with_pics(self):
        """测试提取带图片的微博内容"""
        card = {
            "mblog": {
                "id": "12345",
                "text": "带图片的微博",
                "created_at": "2024-06-15 10:00",
                "pics": [
                    {"url": "http://example.com/pic1.jpg"},
                    {"url": "http://example.com/pic2.jpg"},
                ],
            }
        }
        
        result = self.crawler._extract_weibo_content(card)
        
        self.assertEqual(len(result["pics"]), 2)
        self.assertEqual(result["pics"][0], "http://example.com/pic1.jpg")
    
    def test_extract_weibo_content_empty_mblog(self):
        """测试空mblog"""
        card = {}
        result = self.crawler._extract_weibo_content(card)
        self.assertIsNone(result)
    
    def test_create_session_with_cookie(self):
        """测试带cookie创建会话"""
        crawler = WeiboCrawler(
            user_id="test",
            cookie="test_cookie=value"
        )
        
        self.assertIn("Cookie", crawler.session.headers)
        self.assertEqual(crawler.session.headers["Cookie"], "test_cookie=value")
    
    def test_crawl_no_container_id(self):
        """测试获取不到container_id的情况"""
        with patch.object(self.crawler, '_get_container_id', return_value=None):
            result = self.crawler.crawl()
        
        self.assertEqual(result, [])


class TestWeiboCrawlerIntegration(unittest.TestCase):
    """集成测试（模拟API响应）"""
    
    def test_crawl_with_mock_response(self):
        """测试完整爬取流程（使用模拟响应）"""
        # 模拟获取微博列表的响应
        weibo_response = MagicMock()
        weibo_response.json.return_value = {
            "ok": 1,
            "data": {
                "cards": [
                    {
                        "card_type": 9,
                        "mblog": {
                            "id": "001",
                            "text": "第一条微博",
                            "created_at": "2024-06-15 10:00",
                            "reposts_count": 5,
                            "comments_count": 10,
                            "attitudes_count": 20,
                        }
                    },
                    {
                        "card_type": 9,
                        "mblog": {
                            "id": "002",
                            "text": "第二条微博",
                            "created_at": "2024-06-14 09:00",
                            "reposts_count": 3,
                            "comments_count": 8,
                            "attitudes_count": 15,
                        }
                    }
                ],
                "cardlistInfo": {
                    "since_id": ""
                }
            }
        }
        
        crawler = WeiboCrawler(
            user_id="test_user",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        
        # Mock the session.get method and _get_container_id
        with patch.object(crawler, '_get_container_id', return_value="107603123456"):
            with patch.object(crawler.session, 'get', return_value=weibo_response):
                with patch('time.sleep'):  # 跳过延迟
                    result = crawler.crawl(max_pages=1)
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "001")
        self.assertEqual(result[1]["id"], "002")


if __name__ == "__main__":
    unittest.main()
