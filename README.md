# Weibo Crawler - 微博爬虫

一个用于爬取微博用户发布内容并进行分析的Python工具。

## 功能特性

- 🕷️ **微博爬取**：爬取指定用户在特定时间段内发布的微博
- 📊 **内容分析**：
  - 词频统计
  - 情感分析（正面/负面/中性）
  - 发布时间分布分析
  - 互动数据统计（转发/评论/点赞）
- 💾 **数据导出**：支持JSON格式导出

## 安装

```bash
# 克隆仓库
git clone https://github.com/haooo0418/weibo.git
cd weibo

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 命令行使用

```bash
# 基本用法：爬取指定用户的微博
python main.py --user_id 1234567890

# 指定时间范围
python main.py --user_id 1234567890 --start_date 2024-01-01 --end_date 2024-06-30

# 使用cookie（访问需要登录的内容）
python main.py --user_id 1234567890 --cookie "SUB=xxx; SUBP=xxx"

# 指定最大爬取页数
python main.py --user_id 1234567890 --max_pages 100

# 只爬取不分析
python main.py --user_id 1234567890 --no_analysis
```

### 作为Python模块使用

```python
from weibo_crawler import WeiboCrawler, WeiboAnalyzer

# 创建爬虫
crawler = WeiboCrawler(
    user_id="1234567890",
    start_date="2024-01-01",
    end_date="2024-06-30"
)

# 爬取微博
weibos = crawler.crawl(max_pages=50)

# 分析内容
analyzer = WeiboAnalyzer(weibos)

# 获取词频
word_freq = analyzer.word_frequency(top_n=20)

# 情感分析
sentiment = analyzer.sentiment_analysis()

# 生成完整报告
report = analyzer.generate_report()

# 打印报告到控制台
analyzer.print_report()
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--user_id` | 微博用户ID（必填） | - |
| `--cookie` | 登录Cookie | 空 |
| `--start_date` | 开始日期 (YYYY-MM-DD) | 不限 |
| `--end_date` | 结束日期 (YYYY-MM-DD) | 不限 |
| `--max_pages` | 最大爬取页数 | 50 |
| `--output_dir` | 输出目录 | ./output |
| `--no_analysis` | 不进行内容分析 | False |
| `--config` | 配置文件路径 | config.json |
| `--log_level` | 日志级别 | INFO |

## 输出文件

爬取完成后，会在输出目录生成两个文件：

1. `weibo_data_YYYYMMDD_HHMMSS.json` - 原始微博数据
2. `weibo_data_report_YYYYMMDD_HHMMSS.json` - 分析报告

## 配置文件

可以通过 `config.json` 配置默认参数：

```json
{
    "crawler": {
        "user_id": "",
        "cookie": "",
        "start_date": "",
        "end_date": "",
        "max_pages": 50
    },
    "output": {
        "save_json": true,
        "output_dir": "./output"
    },
    "analysis": {
        "enable_sentiment": true,
        "enable_word_freq": true,
        "word_freq_top_n": 20
    }
}
```

## 获取用户ID

微博用户ID可以通过以下方式获取：

1. 打开用户主页，URL中的数字即为用户ID
   - 例如：`https://weibo.com/u/1234567890` 中的 `1234567890`
2. 在移动版微博中查看用户主页的URL

## 获取Cookie（可选）

某些内容可能需要登录才能访问。获取Cookie的方法：

1. 在浏览器中登录微博
2. 打开开发者工具 (F12)
3. 在Network标签中找到任意请求
4. 复制Request Headers中的Cookie值

## 注意事项

⚠️ **免责声明**：本工具仅供学习和研究使用，请遵守微博的使用条款和相关法律法规。

- 请合理设置爬取间隔，避免对服务器造成过大压力
- 不要爬取他人隐私内容
- 爬取的数据仅供个人学习使用，请勿用于商业目的

## 项目结构

```
weibo/
├── main.py              # 主入口
├── config.json          # 配置文件
├── requirements.txt     # 依赖
├── README.md            # 说明文档
├── weibo_crawler/       # 爬虫模块
│   ├── __init__.py
│   ├── crawler.py       # 爬虫核心
│   └── analyzer.py      # 分析模块
└── tests/               # 测试
    ├── __init__.py
    ├── test_crawler.py
    └── test_analyzer.py
```

## 运行测试

```bash
python -m pytest tests/ -v
```

## License

MIT License