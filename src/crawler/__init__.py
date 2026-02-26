# src/crawler/__init__.py
"""
数据采集模块 - 吸收自 BettaFish MindSpider 的优秀设计
包含：热点新闻采集、AI话题提取、多平台爬虫管道
"""
from src.crawler.news_collector import NewsCollector
from src.crawler.topic_extractor import TopicExtractor
from src.crawler.crawler_pipeline import CrawlerPipeline
