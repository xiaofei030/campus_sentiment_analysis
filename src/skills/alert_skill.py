# src/skills/alert_skill.py
"""
预警管理技能 - 预警创建、查询、处理
"""
from typing import Any, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.skills.base_skill import BaseSkill
from src.database.models import (
    Alert, SentimentRecord, User,
    RiskLevel, AlertStatus
)


class AlertManagementSkill(BaseSkill):
    """预警管理技能"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @property
    def name(self) -> str:
        return "alert_management"
    
    @property
    def description(self) -> str:
        return "管理风险预警，包括创建预警、查询预警列表、处理预警、预警统计"
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "list_alerts",          # 查询预警列表
            "get_alert_detail",     # 获取预警详情
            "handle_alert",         # 处理预警
            "alert_stats",          # 预警统计
            "create_alert",         # 创建预警
        ]
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        actions = {
            "list_alerts": self._list_alerts,
            "get_alert_detail": self._get_alert_detail,
            "handle_alert": self._handle_alert,
            "alert_stats": self._alert_stats,
            "create_alert": self._create_alert,
        }
        
        handler = actions.get(action)
        if handler:
            return handler(params)
        return {"error": f"未知动作: {action}"}
    
    def _list_alerts(self, params) -> dict:
        """查询预警列表"""
        status = params.get("status")
        risk_level = params.get("risk_level")
        page = params.get("page", 1)
        page_size = params.get("page_size", 20)
        
        query = self.db.query(Alert).join(SentimentRecord)
        
        if status:
            query = query.filter(Alert.status == AlertStatus(status))
        if risk_level:
            query = query.filter(Alert.risk_level == RiskLevel(risk_level))
        
        query = query.order_by(Alert.triggered_at.desc())
        
        total = query.count()
        alerts = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "alerts": [self._alert_to_dict(a) for a in alerts]
        }
    
    def _get_alert_detail(self, params) -> dict:
        """获取预警详情"""
        alert_id = params.get("alert_id")
        alert = self.db.query(Alert).get(alert_id)
        if not alert:
            return {"error": f"预警 {alert_id} 不存在"}
        return self._alert_to_dict(alert)
    
    def _handle_alert(self, params) -> dict:
        """处理预警"""
        alert_id = params.get("alert_id")
        handler_id = params.get("handler_id")
        status = params.get("status", "acknowledged")
        note = params.get("note", "")
        
        alert = self.db.query(Alert).get(alert_id)
        if not alert:
            return {"error": f"预警 {alert_id} 不存在"}
        
        alert.handler_id = handler_id
        alert.status = AlertStatus(status)
        alert.handler_note = note
        alert.updated_at = datetime.now()
        
        if status == "resolved":
            alert.resolved_at = datetime.now()
        
        self.db.commit()
        return {"success": True, "alert": self._alert_to_dict(alert)}
    
    def _alert_stats(self, params) -> dict:
        """预警统计"""
        days = params.get("days", 30)
        start_date = datetime.now() - timedelta(days=days)
        
        total = self.db.query(func.count(Alert.id)).filter(
            Alert.created_at >= start_date
        ).scalar() or 0
        
        active = self.db.query(func.count(Alert.id)).filter(
            Alert.status == AlertStatus.ACTIVE
        ).scalar() or 0
        
        acknowledged = self.db.query(func.count(Alert.id)).filter(
            Alert.status == AlertStatus.ACKNOWLEDGED,
            Alert.created_at >= start_date
        ).scalar() or 0
        
        resolved = self.db.query(func.count(Alert.id)).filter(
            Alert.status == AlertStatus.RESOLVED,
            Alert.created_at >= start_date
        ).scalar() or 0
        
        return {
            "total": total,
            "active": active,
            "acknowledged": acknowledged,
            "resolved": resolved,
            "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
        }
    
    def _create_alert(self, params) -> dict:
        """创建预警"""
        alert = Alert(
            record_id=params["record_id"],
            alert_type=params.get("alert_type", "risk"),
            risk_level=RiskLevel(params["risk_level"]),
            status=AlertStatus.ACTIVE,
            title=params.get("title", "系统预警"),
            description=params.get("description", ""),
            ai_suggestion=params.get("ai_suggestion", ""),
            triggered_at=datetime.now(),
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return {"success": True, "alert_id": alert.id}
    
    def _alert_to_dict(self, alert: Alert) -> dict:
        record = self.db.query(SentimentRecord).get(alert.record_id) if alert.record_id else None
        handler = self.db.query(User).get(alert.handler_id) if alert.handler_id else None
        
        return {
            "id": alert.id,
            "record_id": alert.record_id,
            "content": record.content[:200] if record else "",
            "alert_type": alert.alert_type,
            "risk_level": alert.risk_level.value if alert.risk_level else "",
            "status": alert.status.value if alert.status else "",
            "title": alert.title,
            "description": alert.description,
            "ai_suggestion": alert.ai_suggestion,
            "handler_name": handler.real_name if handler else None,
            "handler_note": alert.handler_note,
            "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        }
