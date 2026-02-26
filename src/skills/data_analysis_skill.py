# src/skills/data_analysis_skill.py
"""
数据分析技能 - 提供数据统计和分析能力
可被 Agent 或 API 调用来获取可视化面板数据
"""
from typing import Any, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.skills.base_skill import BaseSkill
from src.database.models import (
    SentimentRecord, ReviewTask, Alert, AnalysisStats,
    SentimentType, RiskLevel, ReviewStatus, AlertStatus
)


class DataAnalysisSkill(BaseSkill):
    """数据分析技能"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @property
    def name(self) -> str:
        return "data_analysis"
    
    @property
    def description(self) -> str:
        return "提供校园情感数据的统计分析能力，包括情感分布、风险趋势、话题热度等"
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "sentiment_distribution",   # 情感分布统计
            "risk_distribution",        # 风险等级分布
            "topic_ranking",            # 话题排行
            "trend_analysis",           # 趋势分析（时间序列）
            "department_comparison",    # 院系对比
            "overview_stats",           # 总览统计（关键指标）
            "emotion_cloud",            # 情绪词云数据
            "grade_analysis",           # 年级分布分析
        ]
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        days = params.get("days", 30)
        start_date = datetime.now() - timedelta(days=days)
        
        actions = {
            "sentiment_distribution": self._sentiment_distribution,
            "risk_distribution": self._risk_distribution,
            "topic_ranking": self._topic_ranking,
            "trend_analysis": self._trend_analysis,
            "department_comparison": self._department_comparison,
            "overview_stats": self._overview_stats,
            "emotion_cloud": self._emotion_cloud,
            "grade_analysis": self._grade_analysis,
        }
        
        handler = actions.get(action)
        if handler:
            return handler(start_date, params)
        return {"error": f"未知动作: {action}"}
    
    def _sentiment_distribution(self, start_date, params) -> dict:
        """情感分布统计"""
        records = self.db.query(
            SentimentRecord.sentiment,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date
        ).group_by(SentimentRecord.sentiment).all()
        
        distribution = {r.sentiment.value: r.count for r in records if r.sentiment}
        total = sum(distribution.values())
        
        return {
            "distribution": distribution,
            "total": total,
            "percentages": {
                k: round(v / total * 100, 1) if total > 0 else 0
                for k, v in distribution.items()
            }
        }
    
    def _risk_distribution(self, start_date, params) -> dict:
        """风险等级分布"""
        records = self.db.query(
            SentimentRecord.risk_level,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date
        ).group_by(SentimentRecord.risk_level).all()
        
        distribution = {r.risk_level.value: r.count for r in records if r.risk_level}
        total = sum(distribution.values())
        
        return {
            "distribution": distribution,
            "total": total,
            "percentages": {
                k: round(v / total * 100, 1) if total > 0 else 0
                for k, v in distribution.items()
            }
        }
    
    def _topic_ranking(self, start_date, params) -> dict:
        """话题排行"""
        limit = params.get("limit", 10)
        
        records = self.db.query(
            SentimentRecord.main_topic,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.main_topic.isnot(None)
        ).group_by(SentimentRecord.main_topic).order_by(
            func.count(SentimentRecord.id).desc()
        ).limit(limit).all()
        
        return {
            "topics": [
                {"topic": r.main_topic, "count": r.count}
                for r in records
            ]
        }
    
    def _trend_analysis(self, start_date, params) -> dict:
        """趋势分析 - 返回每天的情感/风险趋势"""
        records = self.db.query(
            func.date(SentimentRecord.created_at).label("date"),
            SentimentRecord.sentiment,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date
        ).group_by(
            func.date(SentimentRecord.created_at),
            SentimentRecord.sentiment
        ).order_by("date").all()
        
        # 按日期组织数据
        trend_data = {}
        for r in records:
            date_str = str(r.date)
            if date_str not in trend_data:
                trend_data[date_str] = {"date": date_str, "positive": 0, "negative": 0, "neutral": 0, "total": 0}
            if r.sentiment:
                trend_data[date_str][r.sentiment.value] = r.count
                trend_data[date_str]["total"] += r.count
        
        return {
            "trend": list(trend_data.values())
        }
    
    def _department_comparison(self, start_date, params) -> dict:
        """院系对比"""
        records = self.db.query(
            SentimentRecord.author_department,
            SentimentRecord.sentiment,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.author_department.isnot(None)
        ).group_by(
            SentimentRecord.author_department,
            SentimentRecord.sentiment
        ).all()
        
        dept_data = {}
        for r in records:
            dept = r.author_department
            if dept not in dept_data:
                dept_data[dept] = {"department": dept, "positive": 0, "negative": 0, "neutral": 0, "total": 0}
            if r.sentiment:
                dept_data[dept][r.sentiment.value] = r.count
                dept_data[dept]["total"] += r.count
        
        # 按总数排序
        sorted_depts = sorted(dept_data.values(), key=lambda x: -x["total"])
        
        return {
            "departments": sorted_depts[:15]
        }
    
    def _overview_stats(self, start_date, params) -> dict:
        """总览统计 - 可视化面板核心指标"""
        total = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= start_date
        ).scalar() or 0
        
        # 情感计数
        positive = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.sentiment == SentimentType.POSITIVE
        ).scalar() or 0
        
        negative = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.sentiment == SentimentType.NEGATIVE
        ).scalar() or 0
        
        # 风险计数
        high_risk = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        ).scalar() or 0
        
        # 待审核
        pending_review = self.db.query(func.count(ReviewTask.id)).filter(
            ReviewTask.status == ReviewStatus.PENDING
        ).scalar() or 0
        
        # 活跃预警
        active_alerts = self.db.query(func.count(Alert.id)).filter(
            Alert.status == AlertStatus.ACTIVE
        ).scalar() or 0
        
        # 今日新增
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= today_start
        ).scalar() or 0
        
        return {
            "total_records": total,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": total - positive - negative,
            "high_risk_count": high_risk,
            "pending_review": pending_review,
            "active_alerts": active_alerts,
            "today_new": today_count,
            "negative_rate": round(negative / total * 100, 1) if total > 0 else 0,
            "high_risk_rate": round(high_risk / total * 100, 1) if total > 0 else 0,
        }
    
    def _emotion_cloud(self, start_date, params) -> dict:
        """情绪词云数据"""
        records = self.db.query(SentimentRecord.emotions).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.emotions.isnot(None)
        ).all()
        
        emotion_counts = {}
        for r in records:
            for emotion in (r.emotions or []):
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 排序并返回
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: -x[1])
        
        return {
            "emotions": [
                {"word": e, "count": c}
                for e, c in sorted_emotions[:30]
            ]
        }
    
    def _grade_analysis(self, start_date, params) -> dict:
        """年级分布分析"""
        records = self.db.query(
            SentimentRecord.author_grade,
            SentimentRecord.risk_level,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.author_grade.isnot(None)
        ).group_by(
            SentimentRecord.author_grade,
            SentimentRecord.risk_level
        ).all()
        
        grade_data = {}
        for r in records:
            grade = r.author_grade
            if grade not in grade_data:
                grade_data[grade] = {"grade": grade, "total": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
            if r.risk_level:
                grade_data[grade][r.risk_level.value] = r.count
                grade_data[grade]["total"] += r.count
        
        return {
            "grades": list(grade_data.values())
        }
