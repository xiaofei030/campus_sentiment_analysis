# src/skills/report_skill.py
"""
报告生成技能 - 生成各类分析报告
"""
from typing import Any, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.skills.base_skill import BaseSkill
from src.agents.report_agent import ReportAgent


class ReportGenerationSkill(BaseSkill):
    """报告生成技能"""
    
    def __init__(self, db: Session):
        self.db = db
        self.report_agent = ReportAgent(db)
    
    @property
    def name(self) -> str:
        return "report_generation"
    
    @property
    def description(self) -> str:
        return "生成各类分析报告，包括日报、院系报告、AI智能摘要"
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "daily_report",         # 日报
            "department_report",    # 院系报告
            "ai_summary",          # AI智能摘要
        ]
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        actions = {
            "daily_report": self._daily_report,
            "department_report": self._department_report,
            "ai_summary": self._ai_summary,
        }
        
        handler = actions.get(action)
        if handler:
            return handler(params)
        return {"error": f"未知动作: {action}"}
    
    def _daily_report(self, params) -> dict:
        date_str = params.get("date")
        if date_str:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date = None
        return self.report_agent.generate_daily_report(date)
    
    def _department_report(self, params) -> dict:
        department = params.get("department")
        days = params.get("days", 30)
        if not department:
            return {"error": "请指定院系名称 (department)"}
        return self.report_agent.generate_department_report(department, days)
    
    def _ai_summary(self, params) -> dict:
        report_data = params.get("report_data", {})
        if not report_data:
            return {"error": "请提供报告数据 (report_data)"}
        summary = self.report_agent.generate_ai_summary(report_data)
        return {"summary": summary}
