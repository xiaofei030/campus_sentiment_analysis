# src/agents/review_agent.py
"""
审核智能体 - 管理人工审核工作流
为辅导员提供审核建议、自动分配任务、跟踪处理状态
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from src.database.models import (
    ReviewTask, SentimentRecord, Alert, User,
    ReviewStatus, RiskLevel, AlertStatus
)


class ReviewAgent:
    """
    审核智能体 - 辅导员人工审核管理
    
    能力：
    1. 创建审核任务（从AI分析结果自动创建）
    2. 分配任务给辅导员
    3. 提供审核建议
    4. 管理审核状态流转
    5. 生成审核统计
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===== 审核任务管理 =====
    
    def create_review_task(
        self,
        record_id: int,
        ai_risk_level: str,
        auto_assign: bool = True
    ) -> ReviewTask:
        """从分析记录创建审核任务"""
        # 计算优先级
        priority_map = {"low": 0, "medium": 2, "high": 4, "critical": 5}
        priority = priority_map.get(ai_risk_level, 0)
        
        task = ReviewTask(
            record_id=record_id,
            status=ReviewStatus.PENDING,
            priority=priority,
            ai_risk_level=RiskLevel(ai_risk_level),
            created_at=datetime.now(),
        )
        
        # 自动分配
        if auto_assign and ai_risk_level in ["medium", "high", "critical"]:
            record = self.db.query(SentimentRecord).get(record_id)
            if record and record.author_department:
                reviewer = self._find_best_reviewer(record.author_department)
                if reviewer:
                    task.reviewer_id = reviewer.id
                    task.assigned_at = datetime.now()
                    task.status = ReviewStatus.PROCESSING
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def _find_best_reviewer(self, department: str) -> Optional[User]:
        """找到最适合的审核人（同院系、任务最少的辅导员）"""
        from sqlalchemy import func
        
        # 优先同院系
        reviewer = (
            self.db.query(User)
            .filter(User.role == "counselor", User.department == department, User.is_active == True)
            .outerjoin(ReviewTask, (ReviewTask.reviewer_id == User.id) & 
                       (ReviewTask.status == ReviewStatus.PROCESSING))
            .group_by(User.id)
            .order_by(func.count(ReviewTask.id).asc())
            .first()
        )
        
        if not reviewer:
            # 没有同院系辅导员，选任意空闲辅导员
            reviewer = (
                self.db.query(User)
                .filter(User.role == "counselor", User.is_active == True)
                .outerjoin(ReviewTask, (ReviewTask.reviewer_id == User.id) & 
                           (ReviewTask.status == ReviewStatus.PROCESSING))
                .group_by(User.id)
                .order_by(func.count(ReviewTask.id).asc())
                .first()
            )
        
        return reviewer
    
    def get_pending_tasks(
        self,
        reviewer_id: Optional[int] = None,
        risk_level: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """获取待审核任务列表"""
        query = self.db.query(ReviewTask).join(SentimentRecord)
        
        if reviewer_id:
            query = query.filter(ReviewTask.reviewer_id == reviewer_id)
        
        if risk_level:
            query = query.filter(ReviewTask.ai_risk_level == RiskLevel(risk_level))
        
        # 按优先级降序、创建时间升序排列
        query = query.order_by(
            ReviewTask.priority.desc(),
            ReviewTask.created_at.asc()
        )
        
        total = query.count()
        tasks = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "tasks": [self._task_to_dict(t) for t in tasks]
        }
    
    def review_task(
        self,
        task_id: int,
        reviewer_id: int,
        status: str,
        comment: str = "",
        reviewer_risk_level: Optional[str] = None,
        action_taken: str = "",
        follow_up: bool = False,
        follow_up_note: str = ""
    ) -> ReviewTask:
        """执行审核操作"""
        task = self.db.query(ReviewTask).get(task_id)
        if not task:
            raise ValueError(f"审核任务 {task_id} 不存在")
        
        task.reviewer_id = reviewer_id
        task.status = ReviewStatus(status)
        task.review_comment = comment
        task.action_taken = action_taken
        task.follow_up_required = follow_up
        task.follow_up_note = follow_up_note
        task.reviewed_at = datetime.now()
        
        if reviewer_risk_level:
            task.reviewer_risk_level = RiskLevel(reviewer_risk_level)
        
        # 同步更新关联记录的审核状态
        record = self.db.query(SentimentRecord).get(task.record_id)
        if record:
            record.review_status = ReviewStatus(status)
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def escalate_task(self, task_id: int, note: str = "") -> ReviewTask:
        """升级审核任务（需要更高级别处理）"""
        task = self.db.query(ReviewTask).get(task_id)
        if not task:
            raise ValueError(f"审核任务 {task_id} 不存在")
        
        task.status = ReviewStatus.ESCALATED
        task.priority = 5  # 最高优先级
        task.follow_up_note = note
        task.updated_at = datetime.now()
        
        # 同步更新记录状态
        record = self.db.query(SentimentRecord).get(task.record_id)
        if record:
            record.review_status = ReviewStatus.ESCALATED
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_review_stats(self, reviewer_id: Optional[int] = None) -> dict:
        """获取审核统计"""
        query = self.db.query(ReviewTask)
        if reviewer_id:
            query = query.filter(ReviewTask.reviewer_id == reviewer_id)
        
        total = query.count()
        pending = query.filter(ReviewTask.status == ReviewStatus.PENDING).count()
        processing = query.filter(ReviewTask.status == ReviewStatus.PROCESSING).count()
        approved = query.filter(ReviewTask.status == ReviewStatus.APPROVED).count()
        rejected = query.filter(ReviewTask.status == ReviewStatus.REJECTED).count()
        escalated = query.filter(ReviewTask.status == ReviewStatus.ESCALATED).count()
        
        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "approved": approved,
            "rejected": rejected,
            "escalated": escalated,
            "completion_rate": round(
                (approved + rejected) / total * 100, 1
            ) if total > 0 else 0,
        }
    
    def _task_to_dict(self, task: ReviewTask) -> dict:
        """将审核任务转为字典"""
        record = self.db.query(SentimentRecord).get(task.record_id)
        reviewer = self.db.query(User).get(task.reviewer_id) if task.reviewer_id else None
        
        return {
            "id": task.id,
            "record_id": task.record_id,
            "content": record.content if record else "",
            "source": record.source.value if record and record.source else "",
            "author_department": record.author_department if record else "",
            "author_grade": record.author_grade if record else "",
            "sentiment": record.sentiment.value if record and record.sentiment else "",
            "emotions": record.emotions or [],
            "main_topic": record.main_topic if record else "",
            "ai_risk_level": task.ai_risk_level.value if task.ai_risk_level else "",
            "reviewer_risk_level": task.reviewer_risk_level.value if task.reviewer_risk_level else None,
            "status": task.status.value if task.status else "",
            "priority": task.priority,
            "reviewer_name": reviewer.real_name if reviewer else None,
            "review_comment": task.review_comment,
            "action_taken": task.action_taken,
            "follow_up_required": task.follow_up_required,
            "follow_up_note": task.follow_up_note,
            "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
            "reviewed_at": task.reviewed_at.isoformat() if task.reviewed_at else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }
