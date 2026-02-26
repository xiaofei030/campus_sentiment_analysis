# src/tools/__init__.py
"""
工具集合 - 导出所有可用工具
"""
from src.tools.sentiment_tool import sentiment_analyzer
from src.tools.topic_cluster import topic_clusterer
from src.tools.risk_screener import risk_screener
from src.tools.knowledge_tool import knowledge_searcher

# 所有可用工具列表
ALL_TOOLS = [
    sentiment_analyzer,
    topic_clusterer,
    risk_screener,
    knowledge_searcher,
]

__all__ = [
    'sentiment_analyzer',
    'topic_clusterer', 
    'risk_screener',
    'knowledge_searcher',
    'ALL_TOOLS',
]
