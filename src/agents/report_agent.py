# src/agents/report_agent.py
"""
报告生成智能体 - 为辅导员生成各类分析报告
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models import (
    SentimentRecord, ReviewTask, Alert,
    SentimentType, RiskLevel, ReviewStatus, AlertStatus
)
from src.config import get_deepseek_llm


class ReportAgent:
    """
    报告生成智能体
    
    能力：
    1. 生成日报/周报/月报
    2. 生成院系分析报告
    3. 生成风险预警摘要
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> dict:
        """生成日报"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        next_day = date + timedelta(days=1)
        
        records = self.db.query(SentimentRecord).filter(
            SentimentRecord.created_at >= date,
            SentimentRecord.created_at < next_day
        ).all()
        
        total = len(records)
        if total == 0:
            return {"date": date.strftime("%Y-%m-%d"), "total": 0, "message": "当天无数据"}
        
        # 统计
        sentiment_dist = self._count_sentiments(records)
        risk_dist = self._count_risks(records)
        topic_dist = self._count_topics(records)
        dept_dist = self._count_departments(records)
        
        high_risk = [r for r in records if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "total": total,
            "sentiment_distribution": sentiment_dist,
            "risk_distribution": risk_dist,
            "topic_distribution": topic_dist,
            "department_distribution": dept_dist,
            "high_risk_count": len(high_risk),
            "high_risk_samples": [
                {
                    "content": r.content[:100],
                    "risk_level": r.risk_level.value,
                    "department": r.author_department,
                    "emotions": r.emotions,
                }
                for r in high_risk[:10]
            ],
        }
    
    def generate_department_report(self, department: str, days: int = 30) -> dict:
        """生成院系分析报告"""
        start_date = datetime.now() - timedelta(days=days)
        
        records = self.db.query(SentimentRecord).filter(
            SentimentRecord.author_department == department,
            SentimentRecord.created_at >= start_date
        ).all()
        
        total = len(records)
        if total == 0:
            return {"department": department, "total": 0, "message": "无数据"}
        
        return {
            "department": department,
            "period_days": days,
            "total": total,
            "sentiment_distribution": self._count_sentiments(records),
            "risk_distribution": self._count_risks(records),
            "topic_distribution": self._count_topics(records),
            "grade_distribution": self._count_grades(records),
            "avg_sentiment_confidence": round(
                sum(r.sentiment_confidence or 0 for r in records) / total, 3
            ),
        }
    
    def generate_ai_summary(self, report_data: dict) -> str:
        """使用LLM生成报告的自然语言摘要"""
        try:
            llm = get_deepseek_llm()
            
            prompt = f"""你是校园情感分析系统的报告生成专家，请根据以下统计数据生成一份简洁的中文分析摘要。
目标读者是高校辅导员和学生管理人员。

统计数据：
{report_data}

请生成：
1. 整体概况（2-3句话）
2. 需要关注的问题（如果有高风险情况）
3. 建议措施
"""
            response = llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"AI摘要生成失败: {str(e)}"
    
    # ===== 工具方法 =====
    
    def _count_sentiments(self, records) -> dict:
        counts = {"positive": 0, "negative": 0, "neutral": 0}
        for r in records:
            if r.sentiment:
                counts[r.sentiment.value] = counts.get(r.sentiment.value, 0) + 1
        return counts
    
    def _count_risks(self, records) -> dict:
        counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for r in records:
            if r.risk_level:
                counts[r.risk_level.value] = counts.get(r.risk_level.value, 0) + 1
        return counts
    
    def _count_topics(self, records) -> dict:
        counts = {}
        for r in records:
            if r.main_topic:
                counts[r.main_topic] = counts.get(r.main_topic, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))
    
    def _count_departments(self, records) -> dict:
        counts = {}
        for r in records:
            if r.author_department:
                counts[r.author_department] = counts.get(r.author_department, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1])[:10])
    
    def _count_grades(self, records) -> dict:
        counts = {}
        for r in records:
            if r.author_grade:
                counts[r.author_grade] = counts.get(r.author_grade, 0) + 1
        return counts
