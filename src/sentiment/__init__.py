# src/sentiment/__init__.py
"""
情感分析模块 - 吸收自 BettaFish SentimentAnalysisModel 的设计模式
统一预测接口 + 多模型集成投票
"""
from src.sentiment.predictor import SentimentPredictor
