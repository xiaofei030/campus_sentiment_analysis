# src/database/models.py
"""
数据库模型定义 - 校园情感分析系统
面向辅导员/管理人员的数据管理
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, Enum, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from src.database.connection import Base
import enum


# ========== 枚举类型 ==========

class SentimentType(str, enum.Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class RiskLevel(str, enum.Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewStatus(str, enum.Enum):
    """审核状态"""
    PENDING = "pending"          # 待审核
    APPROVED = "approved"        # 已通过
    REJECTED = "rejected"        # 已驳回
    ESCALATED = "escalated"      # 已升级（需要更高级别处理）
    PROCESSING = "processing"    # 处理中


class AlertStatus(str, enum.Enum):
    """预警状态"""
    ACTIVE = "active"            # 活跃预警
    ACKNOWLEDGED = "acknowledged"  # 已确认
    RESOLVED = "resolved"        # 已解决
    DISMISSED = "dismissed"      # 已忽略


class DataSource(str, enum.Enum):
    """数据来源"""
    WEIBO = "weibo"              # 微博
    WECHAT = "wechat"            # 微信
    FORUM = "forum"              # 校园论坛
    SURVEY = "survey"            # 问卷调查
    COUNSELING = "counseling"    # 心理咨询记录
    FEEDBACK = "feedback"        # 意见反馈
    OTHER = "other"


# ========== 数据模型 ==========

class User(Base):
    """用户表 - 辅导员/管理员"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    real_name = Column(String(50), nullable=False, comment="真实姓名")
    role = Column(String(20), default="counselor", comment="角色: admin/counselor")
    department = Column(String(100), comment="所属院系")
    phone = Column(String(20), comment="联系电话")
    email = Column(String(100), comment="邮箱")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    review_tasks = relationship("ReviewTask", back_populates="reviewer")
    handled_alerts = relationship("Alert", back_populates="handler")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class SentimentRecord(Base):
    """情感分析记录表 - 核心数据表"""
    __tablename__ = "sentiment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 原始数据
    content = Column(Text, nullable=False, comment="原始文本内容")
    source = Column(Enum(DataSource), default=DataSource.OTHER, comment="数据来源")
    author_id = Column(String(100), comment="原作者ID（脱敏）")
    author_grade = Column(String(20), comment="年级: 大一/大二/大三/大四/研一/研二/研三")
    author_department = Column(String(100), comment="院系")

    # AI分析结果
    sentiment = Column(Enum(SentimentType), comment="情感倾向")
    emotions = Column(JSON, comment="细粒度情绪列表")
    sentiment_confidence = Column(Float, comment="情感分析置信度")

    # 主题分析
    main_topic = Column(String(100), comment="主要话题")
    sub_topics = Column(JSON, comment="子话题列表")
    keywords = Column(JSON, comment="关键词列表")

    # 风险评估
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW, comment="风险等级")
    risk_indicators = Column(JSON, comment="风险信号列表")
    risk_confidence = Column(Float, comment="风险评估置信度")
    suggested_actions = Column(JSON, comment="建议行动")

    # 审核信息
    review_status = Column(
        Enum(ReviewStatus), default=ReviewStatus.PENDING, comment="审核状态"
    )
    ai_summary = Column(Text, comment="AI生成的摘要")

    # 时间信息
    original_time = Column(DateTime, comment="原始发布时间")
    analyzed_at = Column(DateTime, default=datetime.now, comment="分析时间")
    created_at = Column(DateTime, default=datetime.now, comment="入库时间")

    # 关联
    review_tasks = relationship("ReviewTask", back_populates="record")
    alerts = relationship("Alert", back_populates="record")

    # 索引
    __table_args__ = (
        Index("idx_sentiment", "sentiment"),
        Index("idx_risk_level", "risk_level"),
        Index("idx_review_status", "review_status"),
        Index("idx_source", "source"),
        Index("idx_created_at", "created_at"),
        Index("idx_main_topic", "main_topic"),
        Index("idx_author_department", "author_department"),
    )

    def __repr__(self):
        return (
            f"<SentimentRecord(id={self.id}, sentiment='{self.sentiment}', "
            f"risk='{self.risk_level}')>"
        )


class ReviewTask(Base):
    """审核任务表 - 辅导员人工审核"""
    __tablename__ = "review_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(
        Integer, ForeignKey("sentiment_records.id"), nullable=False, comment="关联记录ID"
    )
    reviewer_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID"
    )

    # 审核信息
    status = Column(
        Enum(ReviewStatus), default=ReviewStatus.PENDING, comment="审核状态"
    )
    priority = Column(Integer, default=0, comment="优先级 0-5, 5最高")
    ai_risk_level = Column(Enum(RiskLevel), comment="AI判定的风险等级")
    reviewer_risk_level = Column(Enum(RiskLevel), comment="审核人判定的风险等级")

    # 审核内容
    review_comment = Column(Text, comment="审核意见")
    action_taken = Column(Text, comment="已采取的措施")
    follow_up_required = Column(Boolean, default=False, comment="是否需要后续跟进")
    follow_up_note = Column(Text, comment="跟进备注")

    # 时间
    assigned_at = Column(DateTime, comment="分配时间")
    reviewed_at = Column(DateTime, comment="审核完成时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    record = relationship("SentimentRecord", back_populates="review_tasks")
    reviewer = relationship("User", back_populates="review_tasks")

    # 索引
    __table_args__ = (
        Index("idx_review_status", "status"),
        Index("idx_review_priority", "priority"),
        Index("idx_reviewer_id", "reviewer_id"),
    )

    def __repr__(self):
        return f"<ReviewTask(id={self.id}, status='{self.status}', priority={self.priority})>"


class Alert(Base):
    """预警记录表"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(
        Integer, ForeignKey("sentiment_records.id"), nullable=False, comment="关联记录ID"
    )
    handler_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="处理人ID"
    )

    # 预警信息
    alert_type = Column(String(50), comment="预警类型: risk/trend/anomaly")
    risk_level = Column(Enum(RiskLevel), nullable=False, comment="风险等级")
    status = Column(
        Enum(AlertStatus), default=AlertStatus.ACTIVE, comment="预警状态"
    )
    title = Column(String(200), comment="预警标题")
    description = Column(Text, comment="预警描述")
    ai_suggestion = Column(Text, comment="AI建议的处理方案")

    # 处理信息
    handler_note = Column(Text, comment="处理备注")
    resolved_at = Column(DateTime, comment="解决时间")

    # 时间
    triggered_at = Column(DateTime, default=datetime.now, comment="触发时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    record = relationship("SentimentRecord", back_populates="alerts")
    handler = relationship("User", back_populates="handled_alerts")

    # 索引
    __table_args__ = (
        Index("idx_alert_status", "status"),
        Index("idx_alert_risk_level", "risk_level"),
        Index("idx_alert_triggered_at", "triggered_at"),
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, risk='{self.risk_level}', status='{self.status}')>"


class AnalysisStats(Base):
    """分析统计表 - 用于可视化面板（按天/周/月汇总）"""
    __tablename__ = "analysis_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(DateTime, nullable=False, comment="统计日期")
    period_type = Column(String(10), default="daily", comment="统计周期: daily/weekly/monthly")

    # 情感分布统计
    total_records = Column(Integer, default=0, comment="总记录数")
    positive_count = Column(Integer, default=0, comment="积极数")
    negative_count = Column(Integer, default=0, comment="消极数")
    neutral_count = Column(Integer, default=0, comment="中性数")

    # 风险分布统计
    low_risk_count = Column(Integer, default=0, comment="低风险数")
    medium_risk_count = Column(Integer, default=0, comment="中风险数")
    high_risk_count = Column(Integer, default=0, comment="高风险数")
    critical_risk_count = Column(Integer, default=0, comment="危急数")

    # 审核统计
    pending_review_count = Column(Integer, default=0, comment="待审核数")
    completed_review_count = Column(Integer, default=0, comment="已完成审核数")

    # 热门话题
    top_topics = Column(JSON, comment="热门话题 Top10")
    top_emotions = Column(JSON, comment="热门情绪 Top10")

    # 平均值
    avg_sentiment_confidence = Column(Float, comment="平均情感置信度")
    avg_risk_confidence = Column(Float, comment="平均风险置信度")

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_stat_date", "stat_date"),
        Index("idx_period_type", "period_type"),
    )
