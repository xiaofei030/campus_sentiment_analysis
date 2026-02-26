# api/main.py
"""
FastAPI 主入口 - 校园情感分析系统 API v2.0
整合：多智能体、MCP工具、Skill技能、人工审核、可视化面板
"""
import sys
import os
from pathlib import Path

# 确保项目根目录在路径中
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import json

# 导入业务逻辑
from src.tools.sentiment_tool import sentiment_analyzer
from src.tools.topic_cluster import topic_clusterer
from src.tools.risk_screener import risk_screener
from src.tools.knowledge_tool import knowledge_searcher
from src.workflows.risk_alert import run_alert_workflow
from src.data_pipeline import KnowledgeBase

# 数据库
from src.database.connection import get_db, init_db

# 多智能体
from src.agents.coordinator_agent import get_coordinator

# 审核Agent
from src.agents.review_agent import ReviewAgent

# 服务层
from src.services.dashboard_service import DashboardService

# Skill 系统
from src.skills.base_skill import SkillRegistry
from src.skills.data_analysis_skill import DataAnalysisSkill
from src.skills.alert_skill import AlertManagementSkill
from src.skills.report_skill import ReportGenerationSkill

# MCP 工具
from src.mcp_server.server import get_tool_list, call_tool_directly


# ========== FastAPI App ==========

app = FastAPI(
    title="校园情感分析系统 API",
    description="""
    基于多智能体 + MCP + Skill 架构的校园情感分析平台
    
    功能模块：
    - 情感分析 / 主题聚类 / 风险筛查
    - 多Agent协作分析
    - 人工审核工作流
    - 可视化数据面板
    - MCP 工具接口
    - Skill 技能系统
    """,
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 启动事件 ==========

@app.on_event("startup")
def startup():
    """应用启动时初始化数据库"""
    try:
        init_db()
        print("[API] 数据库初始化完成")
    except Exception as e:
        print(f"[API] 数据库初始化警告: {e}")
        print("[API] 如果MySQL未配置，仅AI分析功能可用")


# ========== 请求/响应模型 ==========

class TextInput(BaseModel):
    text: str = Field(..., description="要分析的文本")

class QueryInput(BaseModel):
    query: str = Field(..., description="查询关键词")
    top_k: Optional[int] = Field(3, description="返回结果数量")

class AnalyzeInput(BaseModel):
    text: str = Field(..., description="要分析的文本")
    mode: Optional[str] = Field("full", description="分析模式: full/sentiment/topic/risk")

class ReviewInput(BaseModel):
    """审核操作"""
    task_id: int
    reviewer_id: int
    status: str = Field(..., description="审核状态: approved/rejected/escalated")
    comment: Optional[str] = ""
    reviewer_risk_level: Optional[str] = None
    action_taken: Optional[str] = ""
    follow_up: Optional[bool] = False
    follow_up_note: Optional[str] = ""

class SkillInvokeInput(BaseModel):
    """Skill调用"""
    skill_name: str
    action: str
    params: Optional[dict] = {}

class MCPToolInput(BaseModel):
    """MCP工具调用"""
    tool_name: str
    arguments: dict


# ========================================
# 1. 原有 AI 分析 API（保持兼容）
# ========================================

@app.get("/")
def root():
    return {"status": "ok", "message": "校园情感分析系统 API v2.0", "version": "2.0.0"}


@app.post("/api/sentiment")
def analyze_sentiment(data: TextInput):
    try:
        result = sentiment_analyzer.invoke(data.text)
        return {"success": True, "data": json.loads(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/topic")
def analyze_topic(data: TextInput):
    try:
        result = topic_clusterer.invoke(data.text)
        return {"success": True, "data": json.loads(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/risk")
def analyze_risk(data: TextInput):
    try:
        result = risk_screener.invoke(data.text)
        return {"success": True, "data": json.loads(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge")
def search_knowledge(data: QueryInput):
    try:
        result = knowledge_searcher.invoke(data.query)
        return {"success": True, "data": json.loads(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
def full_analyze(data: AnalyzeInput):
    try:
        results = {}
        if data.mode in ["sentiment", "full"]:
            results["sentiment"] = json.loads(sentiment_analyzer.invoke(data.text))
        if data.mode in ["topic", "full"]:
            results["topic"] = json.loads(topic_clusterer.invoke(data.text))
        if data.mode in ["risk", "full"]:
            results["risk"] = json.loads(risk_screener.invoke(data.text))
        return {"success": True, "mode": data.mode, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/alert")
def run_workflow(data: TextInput):
    try:
        result = run_alert_workflow(data.text)
        return {
            "success": True,
            "data": {
                "input_text": result["input_text"],
                "sentiment": result["sentiment_result"],
                "risk": result["risk_result"],
                "risk_level": result["risk_level"],
                "alert_triggered": result["alert_triggered"],
                "knowledge_results": result["knowledge_results"],
                "response": result["final_response"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/build")
def build_knowledge():
    try:
        kb = KnowledgeBase()
        success = kb.add_documents_from_directory()
        if success:
            return {"success": True, "message": "知识库构建完成"}
        else:
            return {"success": False, "message": "知识库构建失败"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 2. 多智能体 API
# ========================================

@app.post("/api/multi-agent/analyze")
def multi_agent_analyze(data: TextInput):
    """多Agent协作分析"""
    try:
        coordinator = get_coordinator()
        result = coordinator.analyze(data.text)
        return {
            "success": True,
            "data": {
                "sentiment": result.get("sentiment_result", {}),
                "topic": result.get("topic_result", {}),
                "risk": result.get("risk_result", {}),
                "risk_level": result.get("risk_level", "unknown"),
                "needs_review": result.get("needs_review", False),
                "alert_triggered": result.get("alert_triggered", False),
                "review_priority": result.get("review_priority", 0),
                "review_suggestion": result.get("review_suggestion", ""),
                "report": result.get("final_report", ""),
                "agent_logs": result.get("agent_logs", []),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/multi-agent/agents")
def list_agents():
    """获取所有注册的Agent"""
    coordinator = get_coordinator()
    return {"agents": coordinator.get_agent_names()}


# ========================================
# 3. 人工审核 API
# ========================================

@app.get("/api/review/tasks")
def get_review_tasks(
    reviewer_id: Optional[int] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取审核任务列表"""
    try:
        agent = ReviewAgent(db)
        result = agent.get_pending_tasks(
            reviewer_id=reviewer_id,
            risk_level=risk_level,
            page=page,
            page_size=page_size
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/review/submit")
def submit_review(data: ReviewInput, db: Session = Depends(get_db)):
    """提交审核结果"""
    try:
        agent = ReviewAgent(db)
        task = agent.review_task(
            task_id=data.task_id,
            reviewer_id=data.reviewer_id,
            status=data.status,
            comment=data.comment,
            reviewer_risk_level=data.reviewer_risk_level,
            action_taken=data.action_taken,
            follow_up=data.follow_up,
            follow_up_note=data.follow_up_note,
        )
        return {"success": True, "message": "审核完成", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/review/escalate/{task_id}")
def escalate_review(task_id: int, db: Session = Depends(get_db)):
    """升级审核任务"""
    try:
        agent = ReviewAgent(db)
        task = agent.escalate_task(task_id)
        return {"success": True, "message": "任务已升级", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/review/stats")
def get_review_stats(
    reviewer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取审核统计"""
    try:
        agent = ReviewAgent(db)
        stats = agent.get_review_stats(reviewer_id)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 4. 可视化面板 API
# ========================================

@app.get("/api/dashboard/overview")
def dashboard_overview(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 总览数据"""
    try:
        service = DashboardService(db)
        data = service.get_overview(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/sentiment-trend")
def dashboard_sentiment_trend(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 情感趋势"""
    try:
        service = DashboardService(db)
        data = service.get_sentiment_trend(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/risk-trend")
def dashboard_risk_trend(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 风险趋势"""
    try:
        service = DashboardService(db)
        data = service.get_risk_trend(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/topics")
def dashboard_topics(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 话题分布"""
    try:
        service = DashboardService(db)
        data = service.get_topic_distribution(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/emotions")
def dashboard_emotions(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 情绪词云"""
    try:
        service = DashboardService(db)
        data = service.get_emotion_cloud(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/departments")
def dashboard_departments(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 院系统计"""
    try:
        service = DashboardService(db)
        data = service.get_department_stats(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/recent-alerts")
def dashboard_recent_alerts(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """可视化面板 - 最近预警"""
    try:
        service = DashboardService(db)
        data = service.get_recent_alerts(limit)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/sources")
def dashboard_sources(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 数据来源分布"""
    try:
        service = DashboardService(db)
        data = service.get_source_distribution(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/platform-sentiment")
def dashboard_platform_sentiment(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 平台情感细表"""
    try:
        service = DashboardService(db)
        data = service.get_platform_sentiment(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/recent-mentions")
def dashboard_recent_mentions(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """可视化面板 - 最近舆情提及"""
    try:
        service = DashboardService(db)
        data = service.get_recent_mentions(limit)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/topic-detail")
def dashboard_topic_detail(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """可视化面板 - 话题详情（含平台、情感、趋势）"""
    try:
        service = DashboardService(db)
        data = service.get_topic_detail(days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 5. Skill 技能系统 API
# ========================================

@app.get("/api/skills")
def list_skills(db: Session = Depends(get_db)):
    """获取所有已注册技能"""
    registry = _get_skill_registry(db)
    return {"success": True, "skills": registry.list_skills()}


@app.post("/api/skills/invoke")
def invoke_skill(data: SkillInvokeInput, db: Session = Depends(get_db)):
    """调用技能"""
    try:
        registry = _get_skill_registry(db)
        result = registry.invoke(data.skill_name, data.action, data.params)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_skill_registry(db: Session) -> SkillRegistry:
    """构建技能注册中心"""
    registry = SkillRegistry()
    registry.register(DataAnalysisSkill(db))
    registry.register(AlertManagementSkill(db))
    registry.register(ReportGenerationSkill(db))
    return registry


# ========================================
# 6. MCP 工具 API（HTTP 方式暴露）
# ========================================

@app.get("/api/mcp/tools")
def list_mcp_tools():
    """列出所有 MCP 工具"""
    tools = get_tool_list()
    return {"success": True, "tools": tools}


@app.post("/api/mcp/call")
def call_mcp_tool(data: MCPToolInput):
    """调用 MCP 工具"""
    try:
        result = call_tool_directly(data.tool_name, data.arguments)
        return {"success": True, "data": json.loads(result)}
    except json.JSONDecodeError:
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 7. 预警管理 API
# ========================================

@app.get("/api/alerts")
def get_alerts(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取预警列表"""
    try:
        from src.skills.alert_skill import AlertManagementSkill
        skill = AlertManagementSkill(db)
        result = skill.execute("list_alerts", {
            "status": status,
            "risk_level": risk_level,
            "page": page,
            "page_size": page_size,
        })
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/{alert_id}/handle")
def handle_alert(
    alert_id: int,
    handler_id: int = Query(...),
    status: str = Query("acknowledged"),
    note: str = Query(""),
    db: Session = Depends(get_db)
):
    """处理预警"""
    try:
        from src.skills.alert_skill import AlertManagementSkill
        skill = AlertManagementSkill(db)
        result = skill.execute("handle_alert", {
            "alert_id": alert_id,
            "handler_id": handler_id,
            "status": status,
            "note": note,
        })
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/stats")
def alert_stats(days: int = Query(30), db: Session = Depends(get_db)):
    """预警统计"""
    try:
        from src.skills.alert_skill import AlertManagementSkill
        skill = AlertManagementSkill(db)
        result = skill.execute("alert_stats", {"days": days})
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 8. 数据采集 API（吸收自 BettaFish MindSpider）
# ========================================

@app.get("/api/collector/status")
def collector_status():
    """获取数据采集器状态"""
    from src.crawler.crawler_pipeline import CrawlerPipeline
    pipeline = CrawlerPipeline()
    return {"success": True, "data": pipeline.get_status()}


@app.get("/api/collector/sources")
def collector_sources():
    """获取支持的新闻源列表"""
    from src.crawler.news_collector import NewsCollector
    return {"success": True, "data": NewsCollector.get_available_sources()}


@app.post("/api/collector/extract-topics")
async def extract_topics():
    """话题提取（从热点新闻中提取校园相关话题和关键词）"""
    try:
        from src.crawler.crawler_pipeline import CrawlerPipeline
        pipeline = CrawlerPipeline()
        result = await pipeline.run_topic_extraction()
        result.pop("_news_list", None)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collector/collect-news")
async def collect_news(
    sources: Optional[str] = Query(None, description="新闻源ID,逗号分隔: weibo,zhihu,tieba"),
):
    """采集热点新闻（不做AI分析，仅采集原始新闻）"""
    try:
        from src.crawler.news_collector import NewsCollector
        collector = NewsCollector()
        source_list = sources.split(",") if sources else None
        result = await collector.collect_news(sources=source_list)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collector/analyze-pending")
async def analyze_pending():
    """对数据库中尚未进行情感分析的记录执行补充分析"""
    try:
        from src.crawler.crawler_pipeline import CrawlerPipeline
        pipeline = CrawlerPipeline()
        result = pipeline.analyze_pending_records()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class KeywordCrawlInput(BaseModel):
    """自定义关键词爬取请求"""
    keywords: Optional[List[str]] = Field(None, description="搜索关键词列表，为空则使用默认校园关键词")
    platforms: Optional[List[str]] = Field(None, description="平台列表: wb/zhihu/xhs/dy/ks/bili/tieba")
    max_notes: int = Field(20, description="每个平台最大爬取内容数")
    enable_comments: bool = Field(True, description="是否爬取评论")
    headless: bool = Field(True, description="无头模式（首次登录设False以便扫码）")
    import_to_db: bool = Field(True, description="是否自动做情感分析并入库")


@app.post("/api/collector/keyword-crawl")
def keyword_crawl(data: KeywordCrawlInput):
    """
    自定义关键词深度爬取（核心功能）
    跳过热点提取，直接用校园关键词在微博/知乎等平台搜索爬取。
    爬取结果自动做情感分析 + 风险评估后入库。

    首次使用须将 headless 设为 false，以便扫码登录各平台。
    """
    try:
        from src.crawler.crawler_pipeline import CrawlerPipeline
        pipeline = CrawlerPipeline()
        result = pipeline.run_keyword_crawling(
            keywords=data.keywords,
            platforms=data.platforms,
            max_notes=data.max_notes,
            enable_comments=data.enable_comments,
            headless=data.headless,
            import_to_db=data.import_to_db,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/collector/clear-test-data")
def clear_test_data():
    """
    清空所有测试/模拟数据，保留表结构。
    清空顺序：alerts → review_tasks → analysis_stats → sentiment_records
    （遵守外键约束）
    """
    try:
        from src.database.connection import SessionLocal
        from src.database.models import Alert, SentimentRecord, AnalysisStats
        session = SessionLocal()
        try:
            from src.database.models import ReviewTask
            has_review = True
        except ImportError:
            has_review = False

        counts = {}
        counts["alerts"] = session.query(Alert).delete()
        if has_review:
            counts["review_tasks"] = session.query(ReviewTask).delete()
        counts["analysis_stats"] = session.query(AnalysisStats).delete()
        counts["sentiment_records"] = session.query(SentimentRecord).delete()
        session.commit()
        session.close()
        return {
            "success": True,
            "data": {
                "message": "已清空所有数据，可重新采集",
                "deleted": counts,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collector/full-pipeline")
async def full_pipeline(
    sources: Optional[str] = Query(None, description="新闻源ID,逗号分隔"),
    import_db: bool = Query(False, description="是否导入数据库"),
    max_keywords: int = Query(60, description="最大关键词数量"),
):
    """运行完整采集管道（采集→话题提取→可选入库）"""
    try:
        from src.crawler.crawler_pipeline import CrawlerPipeline
        pipeline = CrawlerPipeline()
        source_list = sources.split(",") if sources else None
        result = await pipeline.run_full_pipeline(
            news_sources=source_list,
            max_keywords=max_keywords,
            import_to_db=import_db,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 8b. 情感分析模型 API（吸收自 BettaFish SentimentPredictor）
# ========================================

@app.post("/api/sentiment/analyze-batch")
def analyze_batch(data: dict):
    """批量情感分析"""
    try:
        from src.sentiment.predictor import SentimentPredictor
        texts = data.get("texts", [])
        model_name = data.get("model", None)
        predictor = SentimentPredictor()
        results = predictor.predict_batch(texts, model_name=model_name)
        return {"success": True, "data": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment/models")
def list_sentiment_models():
    """获取可用的情感分析模型列表"""
    from src.sentiment.predictor import SentimentPredictor
    predictor = SentimentPredictor()
    return {"success": True, "models": predictor.get_available_models()}


@app.post("/api/sentiment/ensemble")
def ensemble_predict(data: TextInput):
    """集成预测（多模型投票）"""
    try:
        from src.sentiment.predictor import SentimentPredictor
        predictor = SentimentPredictor()
        result = predictor.ensemble_predict(data.text)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reports/generate")
def generate_report_legacy(data: dict, db: Session = Depends(get_db)):
    """生成舆情分析报告（兼容旧接口）"""
    try:
        from src.agents.report_agent import ReportAgent
        agent = ReportAgent(db)
        report_data = data.get("report_data", {})
        summary = agent.generate_ai_summary(report_data)
        return {"success": True, "data": {"report": summary, "source": "local_llm"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 9. 系统设置 API
# ========================================

# 内存缓存系统设置（也可用数据库/文件持久化）
_system_settings = {
    "notification": True,
    "alertThreshold": "10%",
    "keywords": "食堂,宿舍,热水,教务,考试,图书馆",
    "crawlInterval": "30",
    "autoAnalysis": True,
    "emailAlert": False,
}


@app.get("/api/settings")
def get_settings():
    """获取系统设置"""
    return {"success": True, "data": _system_settings}


@app.post("/api/settings")
def save_settings(data: dict):
    """保存系统设置"""
    global _system_settings
    for key, value in data.items():
        if key in _system_settings:
            _system_settings[key] = value
    return {"success": True, "message": "设置已保存", "data": _system_settings}


# ========================================
# 10. 报告生成 API（增强版）
# ========================================

@app.post("/api/reports/generate-enhanced")
def generate_enhanced_report(data: dict, db: Session = Depends(get_db)):
    """
    增强版报告生成 - 支持日报/周报/月报/AI智能报告
    """
    report_type = data.get("type", "daily")  # daily/weekly/monthly/ai
    
    try:
        service = DashboardService(db)
        
        # 根据报告类型确定时间范围
        days_map = {"daily": 1, "weekly": 7, "monthly": 30, "ai": 30}
        days = days_map.get(report_type, 1)
        
        # 获取统计数据
        overview = service.get_overview(days)
        trend = service.get_sentiment_trend(days)
        topics = service.get_topic_distribution(days)
        departments = service.get_department_stats(days)
        alerts_data = service.get_recent_alerts(20)
        sources = service.get_source_distribution(days)
        
        report_data = {
            "type": report_type,
            "period_days": days,
            "overview": overview,
            "trend": trend,
            "topics": topics,
            "departments": departments,
            "alerts": alerts_data,
            "sources": sources,
            "generated_at": datetime.now().isoformat() if True else None,
        }
        
        # AI 报告需要额外生成摘要
        if report_type == "ai":
            try:
                from src.agents.report_agent import ReportAgent
                agent = ReportAgent(db)
                ai_summary = agent.generate_ai_summary({
                    "overview": overview,
                    "topics": topics,
                    "departments": departments,
                })
                report_data["ai_summary"] = ai_summary
            except Exception as e:
                report_data["ai_summary"] = f"AI摘要生成失败: {str(e)}"
        else:
            # 普通报告生成文本摘要
            type_labels = {"daily": "日报", "weekly": "周报", "monthly": "月报"}
            label = type_labels.get(report_type, "报告")
            
            from datetime import datetime as dt
            report_data["title"] = f"校园舆情{label} - {dt.now().strftime('%Y年%m月%d日')}"
            report_data["summary"] = (
                f"统计周期内共监测到 {overview['total_records']} 条舆情记录，"
                f"正面占比 {round(overview['positive_count'] / max(overview['total_records'], 1) * 100, 1)}%，"
                f"负面占比 {overview['negative_rate']}%，"
                f"高风险记录 {overview['high_risk_count']} 条（{overview['high_risk_rate']}%），"
                f"活跃预警 {overview['active_alerts']} 条。"
            )
            if topics:
                top3 = ", ".join(t["topic"] for t in topics[:3])
                report_data["summary"] += f" 热门话题：{top3}。"
        
        return {"success": True, "data": report_data}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))


# ========== 启动入口 ==========
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  校园舆情监测系统 API v2.1.0")
    print("  文档: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=["**/MediaCrawler/**"],
    )
