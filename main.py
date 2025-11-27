#!/usr/bin/env python3
"""
Weibo Crawler Main Entry Point - 微博爬虫主程序

Usage:
    python main.py --user_id USER_ID [--start_date YYYY-MM-DD] [--end_date YYYY-MM-DD]
    
Examples:
    # 爬取指定用户的所有微博
    python main.py --user_id 1234567890
    
    # 爬取指定时间范围内的微博
    python main.py --user_id 1234567890 --start_date 2024-01-01 --end_date 2024-12-31
    
    # 使用cookie访问（某些内容需要登录）
    python main.py --user_id 1234567890 --cookie "SUB=xxx; SUBP=xxx"
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

from weibo_crawler import WeiboCrawler, WeiboAnalyzer


def setup_logging(level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def save_results(weibos: list, output_dir: str, prefix: str):
    """保存爬取结果到JSON文件"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # 将datetime对象转换为字符串
    serializable_weibos = []
    for w in weibos:
        weibo_copy = w.copy()
        if "parsed_date" in weibo_copy and weibo_copy["parsed_date"]:
            weibo_copy["parsed_date"] = weibo_copy["parsed_date"].isoformat()
        serializable_weibos.append(weibo_copy)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(serializable_weibos, f, ensure_ascii=False, indent=2)
    
    return filepath


def save_report(report: dict, output_dir: str, prefix: str):
    """保存分析报告到JSON文件"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_report_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return filepath


def load_config(config_path: str = "config.json") -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(
        description="微博爬虫 - 爬取并分析用户微博内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python main.py --user_id 1234567890
    python main.py --user_id 1234567890 --start_date 2024-01-01 --end_date 2024-06-30
    python main.py --user_id 1234567890 --cookie "SUB=xxx" --max_pages 100
        """
    )
    
    parser.add_argument(
        "--user_id",
        type=str,
        required=True,
        help="微博用户ID"
    )
    parser.add_argument(
        "--cookie",
        type=str,
        default="",
        help="登录Cookie（可选，但某些内容需要登录才能访问）"
    )
    parser.add_argument(
        "--start_date",
        type=str,
        default=None,
        help="开始日期，格式：YYYY-MM-DD"
    )
    parser.add_argument(
        "--end_date",
        type=str,
        default=None,
        help="结束日期，格式：YYYY-MM-DD"
    )
    parser.add_argument(
        "--max_pages",
        type=int,
        default=50,
        help="最大爬取页数（默认50）"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./output",
        help="输出目录（默认./output）"
    )
    parser.add_argument(
        "--no_analysis",
        action="store_true",
        help="不进行内容分析"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="配置文件路径"
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = load_config(args.config)
    
    # 输出配置信息
    logger.info("=" * 60)
    logger.info("微博爬虫启动")
    logger.info("=" * 60)
    logger.info(f"用户ID: {args.user_id}")
    logger.info(f"时间范围: {args.start_date or '不限'} ~ {args.end_date or '不限'}")
    logger.info(f"最大页数: {args.max_pages}")
    logger.info(f"输出目录: {args.output_dir}")
    logger.info("=" * 60)
    
    # 创建爬虫
    crawler = WeiboCrawler(
        user_id=args.user_id,
        cookie=args.cookie,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    
    # 开始爬取
    logger.info("开始爬取微博...")
    weibos = crawler.crawl(max_pages=args.max_pages)
    
    if not weibos:
        logger.warning("未爬取到任何微博")
        return
    
    logger.info(f"成功爬取 {len(weibos)} 条微博")
    
    # 保存原始数据
    output_dir = args.output_dir or config.get("output", {}).get("output_dir", "./output")
    prefix = config.get("output", {}).get("filename_prefix", "weibo_data")
    
    data_file = save_results(weibos, output_dir, prefix)
    logger.info(f"微博数据已保存到: {data_file}")
    
    # 内容分析
    if not args.no_analysis:
        logger.info("开始分析微博内容...")
        analyzer = WeiboAnalyzer(weibos)
        
        # 生成并打印报告
        analyzer.print_report()
        
        # 保存报告
        report = analyzer.generate_report()
        report_file = save_report(report, output_dir, prefix)
        logger.info(f"分析报告已保存到: {report_file}")
    
    logger.info("爬取完成！")


if __name__ == "__main__":
    main()
