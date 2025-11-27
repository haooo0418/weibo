"""
Tests for Weibo Analyzer
"""

import unittest
from datetime import datetime

from weibo_crawler.analyzer import WeiboAnalyzer


class TestWeiboAnalyzer(unittest.TestCase):
    """测试微博分析器类"""
    
    def setUp(self):
        """设置测试数据"""
        self.sample_weibos = [
            {
                "id": "001",
                "text": "今天天气真好，心情很开心，出去玩了一天",
                "created_at": "2024-06-15 10:00",
                "parsed_date": datetime(2024, 6, 15, 10, 0),
                "reposts_count": 10,
                "comments_count": 20,
                "attitudes_count": 50,
            },
            {
                "id": "002",
                "text": "工作太累了，感觉很烦躁，今天又加班到很晚",
                "created_at": "2024-06-14 22:00",
                "parsed_date": datetime(2024, 6, 14, 22, 0),
                "reposts_count": 5,
                "comments_count": 15,
                "attitudes_count": 30,
            },
            {
                "id": "003",
                "text": "分享一篇文章，关于人工智能的发展",
                "created_at": "2024-06-13 14:00",
                "parsed_date": datetime(2024, 6, 13, 14, 0),
                "reposts_count": 100,
                "comments_count": 50,
                "attitudes_count": 200,
            },
        ]
        self.analyzer = WeiboAnalyzer(self.sample_weibos)
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(len(self.analyzer.weibos), 3)
    
    def test_tokenize_basic(self):
        """测试基本分词"""
        text = "今天天气很好"
        result = self.analyzer._tokenize(text)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
    
    def test_tokenize_removes_urls(self):
        """测试分词时移除URL"""
        text = "查看链接 https://example.com/page 了解更多"
        result = self.analyzer._tokenize(text)
        # URL应该被移除
        self.assertNotIn("https", " ".join(result))
        self.assertNotIn("example", " ".join(result))
    
    def test_tokenize_removes_mentions(self):
        """测试分词时移除@提及"""
        text = "感谢@用户名 的支持"
        result = self.analyzer._tokenize(text)
        # @提及应该被移除
        self.assertNotIn("@用户名", result)
    
    def test_word_frequency(self):
        """测试词频统计"""
        result = self.analyzer.word_frequency(top_n=10)
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) <= 10)
        
        # 每个元素应该是 (词, 频率) 元组
        for item in result:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)
            self.assertIsInstance(item[0], str)
            self.assertIsInstance(item[1], int)
    
    def test_sentiment_analysis(self):
        """测试情感分析"""
        result = self.analyzer.sentiment_analysis()
        
        # 检查返回结构
        self.assertIn("summary", result)
        self.assertIn("details", result)
        
        summary = result["summary"]
        self.assertEqual(summary["total"], 3)
        self.assertIn("positive", summary)
        self.assertIn("negative", summary)
        self.assertIn("neutral", summary)
        self.assertIn("positive_ratio", summary)
        self.assertIn("negative_ratio", summary)
        self.assertIn("neutral_ratio", summary)
        
        # 检查比例之和约等于100%
        total_ratio = (
            summary["positive_ratio"] + 
            summary["negative_ratio"] + 
            summary["neutral_ratio"]
        )
        self.assertAlmostEqual(total_ratio, 100.0, places=1)
    
    def test_sentiment_with_positive_text(self):
        """测试包含正面词汇的微博"""
        positive_weibos = [
            {"id": "p1", "text": "今天真开心，太幸福了，感谢大家的支持！"}
        ]
        analyzer = WeiboAnalyzer(positive_weibos)
        result = analyzer.sentiment_analysis()
        
        self.assertEqual(result["summary"]["positive"], 1)
        self.assertEqual(result["summary"]["negative"], 0)
    
    def test_sentiment_with_negative_text(self):
        """测试包含负面词汇的微博"""
        negative_weibos = [
            {"id": "n1", "text": "太难过了，讨厌这种失望的感觉"}
        ]
        analyzer = WeiboAnalyzer(negative_weibos)
        result = analyzer.sentiment_analysis()
        
        self.assertEqual(result["summary"]["negative"], 1)
        self.assertEqual(result["summary"]["positive"], 0)
    
    def test_time_distribution(self):
        """测试时间分布分析"""
        result = self.analyzer.time_distribution()
        
        self.assertIn("hourly", result)
        self.assertIn("daily", result)
        self.assertIn("monthly", result)
        
        # 检查小时分布
        hourly = result["hourly"]
        self.assertIn(10, hourly)  # 第一条微博在10点
        self.assertIn(22, hourly)  # 第二条微博在22点
        self.assertIn(14, hourly)  # 第三条微博在14点
    
    def test_engagement_stats(self):
        """测试互动数据统计"""
        result = self.analyzer.engagement_stats()
        
        self.assertIn("reposts", result)
        self.assertIn("comments", result)
        self.assertIn("attitudes", result)
        self.assertIn("top_weibos", result)
        
        # 检查转发统计
        reposts = result["reposts"]
        self.assertEqual(reposts["total"], 115)  # 10 + 5 + 100
        self.assertEqual(reposts["max"], 100)
        self.assertEqual(reposts["min"], 5)
        
        # 检查TOP微博
        top_weibos = result["top_weibos"]
        self.assertTrue(len(top_weibos) <= 5)
        # 第三条微博互动最多，应该排第一
        self.assertEqual(top_weibos[0]["id"], "003")
    
    def test_generate_report(self):
        """测试生成完整报告"""
        result = self.analyzer.generate_report()
        
        self.assertIn("total_weibos", result)
        self.assertIn("word_frequency", result)
        self.assertIn("sentiment", result)
        self.assertIn("time_distribution", result)
        self.assertIn("engagement", result)
        self.assertIn("generated_at", result)
        
        self.assertEqual(result["total_weibos"], 3)
    
    def test_empty_weibos(self):
        """测试空微博列表"""
        analyzer = WeiboAnalyzer([])
        
        # 词频分析
        word_freq = analyzer.word_frequency()
        self.assertEqual(word_freq, [])
        
        # 情感分析
        sentiment = analyzer.sentiment_analysis()
        self.assertEqual(sentiment["summary"]["total"], 0)
        
        # 时间分布
        time_dist = analyzer.time_distribution()
        self.assertEqual(time_dist["hourly"], {})
        
        # 互动统计
        engagement = analyzer.engagement_stats()
        self.assertEqual(engagement["reposts"]["total"], 0)
    
    def test_weibo_without_parsed_date(self):
        """测试没有解析日期的微博"""
        weibos = [
            {
                "id": "001",
                "text": "测试微博",
                "created_at": "刚刚",
                "parsed_date": None,
                "reposts_count": 0,
                "comments_count": 0,
                "attitudes_count": 0,
            }
        ]
        analyzer = WeiboAnalyzer(weibos)
        
        # 时间分布分析应该能处理None日期
        result = analyzer.time_distribution()
        self.assertEqual(result["hourly"], {})


class TestWeiboAnalyzerEdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    def test_very_long_text(self):
        """测试非常长的文本"""
        long_text = "测试" * 1000
        weibos = [{"id": "001", "text": long_text}]
        analyzer = WeiboAnalyzer(weibos)
        
        # 应该能正常处理
        result = analyzer.word_frequency()
        self.assertIsInstance(result, list)
    
    def test_special_characters(self):
        """测试特殊字符"""
        special_text = "测试！@#$%^&*()_+{}|:\"<>?~`-=[]\\;',./"
        weibos = [{"id": "001", "text": special_text}]
        analyzer = WeiboAnalyzer(weibos)
        
        # 应该能正常处理
        result = analyzer.word_frequency()
        self.assertIsInstance(result, list)
    
    def test_emoji_text(self):
        """测试包含表情的文本"""
        emoji_text = "今天[开心]很高兴[鲜花]"
        weibos = [{"id": "001", "text": emoji_text}]
        analyzer = WeiboAnalyzer(weibos)
        
        # 应该能正常处理，表情会被过滤
        result = analyzer.word_frequency()
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
