# src/services/dashboard_service.py
"""
可视化面板服务 - 为前端Dashboard提供数据
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models import (
    SentimentRecord, ReviewTask, Alert, AnalysisStats,
    SentimentType, RiskLevel, ReviewStatus, AlertStatus
)


class DashboardService:
    """可视化面板数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_overview(self, days: int = 30) -> dict:
        """获取总览数据"""
        start_date = datetime.now() - timedelta(days=days)
        
        total = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= start_date
        ).scalar() or 0
        
        positive = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.sentiment == SentimentType.POSITIVE
        ).scalar() or 0
        
        negative = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.sentiment == SentimentType.NEGATIVE
        ).scalar() or 0
        
        high_risk = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        ).scalar() or 0
        
        pending_review = self.db.query(func.count(ReviewTask.id)).filter(
            ReviewTask.status == ReviewStatus.PENDING
        ).scalar() or 0
        
        active_alerts = self.db.query(func.count(Alert.id)).filter(
            Alert.status == AlertStatus.ACTIVE
        ).scalar() or 0
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= today
        ).scalar() or 0
        
        # 昨日对比
        yesterday = today - timedelta(days=1)
        yesterday_count = self.db.query(func.count(SentimentRecord.id)).filter(
            SentimentRecord.created_at >= yesterday,
            SentimentRecord.created_at < today
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
            "yesterday_new": yesterday_count,
            "negative_rate": round(negative / total * 100, 1) if total > 0 else 0,
            "high_risk_rate": round(high_risk / total * 100, 1) if total > 0 else 0,
        }
    
    def get_sentiment_trend(self, days: int = 30) -> list:
        """获取情感趋势（按天）"""
        start_date = datetime.now() - timedelta(days=days)
        
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
        
        trend_data = {}
        for r in records:
            date_str = str(r.date)
            if date_str not in trend_data:
                trend_data[date_str] = {
                    "date": date_str, "positive": 0, "negative": 0, "neutral": 0, "total": 0
                }
            if r.sentiment:
                trend_data[date_str][r.sentiment.value] = r.count
                trend_data[date_str]["total"] += r.count
        
        return list(trend_data.values())
    
    def get_risk_trend(self, days: int = 30) -> list:
        """获取风险等级趋势（按天）"""
        start_date = datetime.now() - timedelta(days=days)
        
        records = self.db.query(
            func.date(SentimentRecord.created_at).label("date"),
            SentimentRecord.risk_level,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date
        ).group_by(
            func.date(SentimentRecord.created_at),
            SentimentRecord.risk_level
        ).order_by("date").all()
        
        trend_data = {}
        for r in records:
            date_str = str(r.date)
            if date_str not in trend_data:
                trend_data[date_str] = {
                    "date": date_str, "low": 0, "medium": 0, "high": 0, "critical": 0
                }
            if r.risk_level:
                trend_data[date_str][r.risk_level.value] = r.count
        
        return list(trend_data.values())
    
    def get_topic_distribution(self, days: int = 30) -> list:
        """获取话题分布"""
        start_date = datetime.now() - timedelta(days=days)
        
        records = self.db.query(
            SentimentRecord.main_topic,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.main_topic.isnot(None)
        ).group_by(
            SentimentRecord.main_topic
        ).order_by(
            func.count(SentimentRecord.id).desc()
        ).limit(10).all()
        
        return [{"topic": r.main_topic, "count": r.count} for r in records]
    
    def get_emotion_cloud(self, days: int = 30) -> list:
        """获取情绪词云"""
        start_date = datetime.now() - timedelta(days=days)
        
        records = self.db.query(SentimentRecord.emotions).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.emotions.isnot(None)
        ).all()
        
        emotion_counts = {}
        for r in records:
            for emotion in (r.emotions or []):
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: -x[1])
        return [{"word": e, "count": c} for e, c in sorted_emotions[:30]]
    
    def get_department_stats(self, days: int = 30) -> list:
        """获取院系统计"""
        start_date = datetime.now() - timedelta(days=days)
        
        records = self.db.query(
            SentimentRecord.author_department,
            SentimentRecord.sentiment,
            SentimentRecord.risk_level,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.author_department.isnot(None)
        ).group_by(
            SentimentRecord.author_department,
            SentimentRecord.sentiment,
            SentimentRecord.risk_level
        ).all()
        
        dept_data = {}
        for r in records:
            dept = r.author_department
            if dept not in dept_data:
                dept_data[dept] = {
                    "department": dept,
                    "total": 0,
                    "positive": 0, "negative": 0, "neutral": 0,
                    "high_risk": 0,
                }
            dept_data[dept]["total"] += r.count
            if r.sentiment:
                dept_data[dept][r.sentiment.value] += r.count
            if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                dept_data[dept]["high_risk"] += r.count
        
        return sorted(dept_data.values(), key=lambda x: -x["total"])
    
    def get_recent_alerts(self, limit: int = 10) -> list:
        """获取最近的预警"""
        alerts = self.db.query(Alert).order_by(
            Alert.triggered_at.desc()
        ).limit(limit).all()
        
        result = []
        for a in alerts:
            record = self.db.query(SentimentRecord).get(a.record_id) if a.record_id else None
            result.append({
                "id": a.id,
                "title": a.title,
                "risk_level": a.risk_level.value if a.risk_level else "",
                "status": a.status.value if a.status else "",
                "content": record.content[:100] if record else "",
                "department": record.author_department if record else "",
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            })
        return result

    def get_source_distribution(self, days: int = 30) -> list:
        """获取数据来源（平台）分布"""
        start_date = datetime.now() - timedelta(days=days)
        
        records = self.db.query(
            SentimentRecord.source,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date
        ).group_by(
            SentimentRecord.source
        ).order_by(
            func.count(SentimentRecord.id).desc()
        ).all()
        
        SOURCE_LABELS = {
            "weibo": "微博", "wechat": "微信", "forum": "论坛",
            "survey": "问卷", "counseling": "咨询", "feedback": "反馈", "other": "其他",
        }
        SOURCE_COLORS = {
            "weibo": "#ff4757", "wechat": "#00c48c", "forum": "#3742fa",
            "survey": "#f5a623", "counseling": "#e17055", "feedback": "#70a1ff", "other": "#a0a0b0",
        }
        
        total = sum(r.count for r in records) or 1
        return [
            {
                "name": SOURCE_LABELS.get(r.source.value if r.source else "other", "其他"),
                "value": round(r.count / total * 100),
                "count": r.count,
                "color": SOURCE_COLORS.get(r.source.value if r.source else "other", "#a0a0b0"),
            }
            for r in records
        ]

    def get_platform_sentiment(self, days: int = 30) -> list:
        """获取各平台的情感分布细表"""
        start_date = datetime.now() - timedelta(days=days)
        
        records = self.db.query(
            SentimentRecord.source,
            SentimentRecord.sentiment,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date
        ).group_by(
            SentimentRecord.source,
            SentimentRecord.sentiment
        ).all()
        
        SOURCE_LABELS = {
            "weibo": "微博", "wechat": "微信", "forum": "论坛",
            "survey": "问卷", "counseling": "咨询", "feedback": "反馈", "other": "其他",
        }
        
        platform_data = {}
        for r in records:
            src = r.source.value if r.source else "other"
            label = SOURCE_LABELS.get(src, "其他")
            if label not in platform_data:
                platform_data[label] = {"name": label, "total": 0, "positive": 0, "negative": 0, "neutral": 0}
            sentiment_val = r.sentiment.value if r.sentiment else "neutral"
            platform_data[label][sentiment_val] += r.count
            platform_data[label]["total"] += r.count
        
        result = sorted(platform_data.values(), key=lambda x: -x["total"])
        # 格式化 total 显示
        for item in result:
            t = item["total"]
            item["total_fmt"] = f"{t / 1000:.1f}k" if t >= 1000 else str(t)
        return result

    def get_recent_mentions(self, limit: int = 20) -> list:
        """获取最近的舆情提及记录"""
        records = self.db.query(SentimentRecord).order_by(
            SentimentRecord.created_at.desc()
        ).limit(limit).all()
        
        SOURCE_LABELS = {
            "weibo": "微博", "wechat": "微信", "forum": "论坛",
            "survey": "问卷", "counseling": "咨询", "feedback": "反馈", "other": "其他",
        }
        SENTIMENT_LABELS = {"positive": "正面", "negative": "负面", "neutral": "中性"}
        
        return [
            {
                "id": r.id,
                "user": r.author_id or f"用户{r.id}",
                "text": (r.content[:60] + "..." if len(r.content or "") > 60 else r.content) or "",
                "platform": SOURCE_LABELS.get(r.source.value if r.source else "other", "其他"),
                "sentiment": SENTIMENT_LABELS.get(r.sentiment.value if r.sentiment else "neutral", "中性"),
                "sentiment_raw": r.sentiment.value if r.sentiment else "neutral",
                "topic": r.main_topic or "",
                "time": r.created_at.strftime("%H:%M") if r.created_at else "",
                "time_full": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]

    def get_topic_detail(self, days: int = 30) -> list:
        """获取话题详情（含平台、情感、趋势）"""
        start_date = datetime.now() - timedelta(days=days)
        yesterday = datetime.now() - timedelta(days=1)
        
        # 当前周期话题统计
        records = self.db.query(
            SentimentRecord.main_topic,
            SentimentRecord.source,
            SentimentRecord.sentiment,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= start_date,
            SentimentRecord.main_topic.isnot(None)
        ).group_by(
            SentimentRecord.main_topic,
            SentimentRecord.source,
            SentimentRecord.sentiment
        ).all()
        
        SOURCE_LABELS = {
            "weibo": "微博", "wechat": "微信", "forum": "论坛",
            "survey": "问卷", "counseling": "咨询", "feedback": "反馈", "other": "其他",
        }
        SENTIMENT_LABELS = {"positive": "正面", "negative": "负面", "neutral": "中性"}
        
        topic_data = {}
        for r in records:
            topic = r.main_topic
            if topic not in topic_data:
                topic_data[topic] = {
                    "topic": topic, "count": 0,
                    "sources": {}, "sentiments": {"positive": 0, "negative": 0, "neutral": 0}
                }
            src_label = SOURCE_LABELS.get(r.source.value if r.source else "other", "其他")
            topic_data[topic]["sources"][src_label] = topic_data[topic]["sources"].get(src_label, 0) + r.count
            sent_val = r.sentiment.value if r.sentiment else "neutral"
            topic_data[topic]["sentiments"][sent_val] += r.count
            topic_data[topic]["count"] += r.count
        
        # 上一周期对比（趋势）
        prev_start = start_date - timedelta(days=days)
        prev_records = self.db.query(
            SentimentRecord.main_topic,
            func.count(SentimentRecord.id).label("count")
        ).filter(
            SentimentRecord.created_at >= prev_start,
            SentimentRecord.created_at < start_date,
            SentimentRecord.main_topic.isnot(None)
        ).group_by(SentimentRecord.main_topic).all()
        
        prev_counts = {r.main_topic: r.count for r in prev_records}
        
        result = []
        for topic, data in topic_data.items():
            # 主要平台
            top_src = max(data["sources"].items(), key=lambda x: x[1])[0] if data["sources"] else "其他"
            # 情感标签 - 取占比最大的
            sents = data["sentiments"]
            main_sentiment = max(sents.items(), key=lambda x: x[1])[0]
            # 趋势
            prev_count = prev_counts.get(topic, 0)
            trend = "up" if data["count"] > prev_count else ("down" if data["count"] < prev_count else "flat")
            
            result.append({
                "topic": topic,
                "count": data["count"],
                "platform": top_src,
                "sentiment": SENTIMENT_LABELS.get(main_sentiment, "中性"),
                "sentiment_raw": main_sentiment,
                "trend": trend,
            })
        
        result.sort(key=lambda x: -x["count"])
        return result[:20]
