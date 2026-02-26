# src/agents/coordinator_agent.py
"""
协调者智能体 - 多智能体系统的核心调度器
负责接收任务、分发给子Agent、汇总结果

架构：
  用户请求 → CoordinatorAgent
      ├→ SentimentAgent（情感分析）
      ├→ RiskAgent（风险评估）
      ├→ ReviewAgent（人工审核调度）
      └→ ReportAgent（报告生成）
"""
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
import json
from datetime import datetime

from src.config import get_deepseek_llm
from src.tools.sentiment_tool import sentiment_analyzer
from src.tools.topic_cluster import topic_clusterer
from src.tools.risk_screener import risk_screener
from src.tools.knowledge_tool import knowledge_searcher


# ========== 多Agent状态定义 ==========

class MultiAgentState(TypedDict):
    """多智能体协作状态"""
    # 输入
    input_text: str
    task_type: str              # analyze / review / report / auto
    
    # Agent 结果
    sentiment_result: dict
    topic_result: dict
    risk_result: dict
    knowledge_results: list
    
    # 协调信息
    risk_level: str
    needs_review: bool
    alert_triggered: bool
    
    # 审核
    review_suggestion: str
    review_priority: int
    
    # 最终输出
    final_report: str
    agent_logs: list           # 多Agent执行日志


# ========== 子Agent节点 ==========

def sentiment_agent_node(state: MultiAgentState) -> MultiAgentState:
    """情感分析Agent"""
    log_entry = {
        "agent": "SentimentAgent",
        "action": "情感分析",
        "time": datetime.now().isoformat(),
        "status": "running"
    }
    
    try:
        result = sentiment_analyzer.invoke(state["input_text"])
        parsed = json.loads(result)
        state["sentiment_result"] = parsed
        log_entry["status"] = "success"
        log_entry["detail"] = f"情感: {parsed.get('sentiment', 'unknown')}"
    except Exception as e:
        state["sentiment_result"] = {"sentiment": "neutral", "emotions": [], "confidence": 0}
        log_entry["status"] = "error"
        log_entry["detail"] = str(e)
    
    state["agent_logs"] = state.get("agent_logs", []) + [log_entry]
    return state


def topic_agent_node(state: MultiAgentState) -> MultiAgentState:
    """主题分析Agent"""
    log_entry = {
        "agent": "TopicAgent",
        "action": "主题聚类",
        "time": datetime.now().isoformat(),
        "status": "running"
    }
    
    try:
        result = topic_clusterer.invoke(state["input_text"])
        parsed = json.loads(result)
        state["topic_result"] = parsed
        log_entry["status"] = "success"
        log_entry["detail"] = f"主题: {parsed.get('main_topic', 'unknown')}"
    except Exception as e:
        state["topic_result"] = {"main_topic": "未知", "sub_topics": [], "keywords": []}
        log_entry["status"] = "error"
        log_entry["detail"] = str(e)
    
    state["agent_logs"] = state.get("agent_logs", []) + [log_entry]
    return state


def risk_agent_node(state: MultiAgentState) -> MultiAgentState:
    """风险评估Agent"""
    log_entry = {
        "agent": "RiskAgent",
        "action": "风险评估",
        "time": datetime.now().isoformat(),
        "status": "running"
    }
    
    try:
        result = risk_screener.invoke(state["input_text"])
        parsed = json.loads(result)
        state["risk_result"] = parsed
        state["risk_level"] = parsed.get("risk_level", "low")
        state["alert_triggered"] = state["risk_level"] in ["high", "critical"]
        state["needs_review"] = state["risk_level"] in ["medium", "high", "critical"]
        
        log_entry["status"] = "success"
        log_entry["detail"] = f"风险等级: {state['risk_level']}"
    except Exception as e:
        state["risk_result"] = {"risk_level": "low", "risk_indicators": []}
        state["risk_level"] = "low"
        state["needs_review"] = False
        log_entry["status"] = "error"
        log_entry["detail"] = str(e)
    
    state["agent_logs"] = state.get("agent_logs", []) + [log_entry]
    return state


def review_decision_node(state: MultiAgentState) -> MultiAgentState:
    """审核决策Agent - 决定是否需要人工审核以及优先级"""
    log_entry = {
        "agent": "ReviewDecisionAgent",
        "action": "审核决策",
        "time": datetime.now().isoformat(),
        "status": "running"
    }
    
    risk_level = state.get("risk_level", "low")
    sentiment = state.get("sentiment_result", {}).get("sentiment", "neutral")
    
    # 计算审核优先级 (0-5)
    priority = 0
    if risk_level == "critical":
        priority = 5
        state["review_suggestion"] = "紧急：需要立即人工干预，建议24小时内联系学生"
    elif risk_level == "high":
        priority = 4
        state["review_suggestion"] = "高优先级：建议48小时内安排辅导员约谈"
    elif risk_level == "medium":
        priority = 2
        state["review_suggestion"] = "中等优先级：建议一周内关注该学生动态"
    else:
        priority = 0
        state["review_suggestion"] = "低风险，可归档"
    
    state["review_priority"] = priority
    
    log_entry["status"] = "success"
    log_entry["detail"] = f"优先级: {priority}, 需审核: {state['needs_review']}"
    state["agent_logs"] = state.get("agent_logs", []) + [log_entry]
    return state


def knowledge_agent_node(state: MultiAgentState) -> MultiAgentState:
    """知识检索Agent（仅高风险时触发）"""
    log_entry = {
        "agent": "KnowledgeAgent",
        "action": "知识检索",
        "time": datetime.now().isoformat(),
        "status": "running"
    }
    
    try:
        emotions = state.get("sentiment_result", {}).get("emotions", [])
        risk_indicators = state.get("risk_result", {}).get("risk_indicators", [])
        query_terms = emotions + risk_indicators
        if not query_terms:
            query_terms = ["心理健康", "情绪调节"]
        
        query = " ".join(query_terms[:3])
        result = knowledge_searcher.invoke(query)
        knowledge_data = json.loads(result)
        state["knowledge_results"] = knowledge_data.get("results", [])
        
        log_entry["status"] = "success"
        log_entry["detail"] = f"检索到 {len(state['knowledge_results'])} 条知识"
    except Exception as e:
        state["knowledge_results"] = []
        log_entry["status"] = "error"
        log_entry["detail"] = str(e)
    
    state["agent_logs"] = state.get("agent_logs", []) + [log_entry]
    return state


def report_agent_node(state: MultiAgentState) -> MultiAgentState:
    """报告生成Agent - 汇总所有分析结果"""
    log_entry = {
        "agent": "ReportAgent",
        "action": "生成综合报告",
        "time": datetime.now().isoformat(),
        "status": "running"
    }
    
    try:
        llm = get_deepseek_llm()
        
        sentiment = state.get("sentiment_result", {})
        topic = state.get("topic_result", {})
        risk = state.get("risk_result", {})
        knowledge = state.get("knowledge_results", [])
        
        knowledge_text = ""
        if knowledge:
            knowledge_text = "\n相关专业建议：\n" + "\n".join(
                f"- {item['content'][:150]}" for item in knowledge[:3]
            )
        
        prompt = f"""你是校园情感分析系统的报告生成专家。请根据多个分析Agent的结果，
生成一份结构化的综合分析报告。报告面向辅导员/管理人员阅读。

原始文本："{state['input_text']}"

【情感分析Agent结果】
- 情感倾向：{sentiment.get('sentiment', '未知')}
- 情绪标签：{', '.join(sentiment.get('emotions', []))}
- 置信度：{sentiment.get('confidence', 0):.0%}

【主题分析Agent结果】
- 主要话题：{topic.get('main_topic', '未知')}
- 子话题：{', '.join(topic.get('sub_topics', []))}
- 关键词：{', '.join(topic.get('keywords', []))}

【风险评估Agent结果】
- 风险等级：{state.get('risk_level', '未知')}
- 风险信号：{', '.join(risk.get('risk_indicators', []))}
- 建议行动：{', '.join(risk.get('suggested_actions', []))}

【审核决策Agent建议】
- 审核优先级：{state.get('review_priority', 0)}/5
- 建议：{state.get('review_suggestion', '无')}
{knowledge_text}

请生成一份简洁专业的中文分析报告，包括：
1. 情况概述（2-3句话）
2. 风险评估与建议
3. 后续处理建议
{"⚠️ 注意：当前为高风险情况，请在报告中强调紧急处理措施。" if state.get('alert_triggered') else ""}"""
        
        response = llm.invoke(prompt)
        state["final_report"] = response.content if hasattr(response, 'content') else str(response)
        
        log_entry["status"] = "success"
        log_entry["detail"] = "报告生成完成"
    except Exception as e:
        state["final_report"] = f"报告生成失败: {str(e)}"
        log_entry["status"] = "error"
        log_entry["detail"] = str(e)
    
    state["agent_logs"] = state.get("agent_logs", []) + [log_entry]
    return state


# ========== 路由函数 ==========

def route_after_risk(state: MultiAgentState) -> Literal["knowledge_agent", "report_agent"]:
    """风险评估后的路由"""
    if state.get("risk_level") in ["high", "critical"]:
        return "knowledge_agent"
    return "report_agent"


# ========== 构建多Agent工作流 ==========

def build_multi_agent_workflow():
    """构建多Agent协作工作流"""
    workflow = StateGraph(MultiAgentState)
    
    # 添加Agent节点
    workflow.add_node("sentiment_agent", sentiment_agent_node)
    workflow.add_node("topic_agent", topic_agent_node)
    workflow.add_node("risk_agent", risk_agent_node)
    workflow.add_node("review_decision", review_decision_node)
    workflow.add_node("knowledge_agent", knowledge_agent_node)
    workflow.add_node("report_agent", report_agent_node)
    
    # 设置入口 → 情感分析
    workflow.set_entry_point("sentiment_agent")
    
    # 情感分析 → 主题分析
    workflow.add_edge("sentiment_agent", "topic_agent")
    
    # 主题分析 → 风险评估
    workflow.add_edge("topic_agent", "risk_agent")
    
    # 风险评估 → 审核决策
    workflow.add_edge("risk_agent", "review_decision")
    
    # 审核决策 → 条件路由（高风险走知识检索，其他直接生成报告）
    workflow.add_conditional_edges(
        "review_decision",
        route_after_risk,
        {
            "knowledge_agent": "knowledge_agent",
            "report_agent": "report_agent"
        }
    )
    
    # 知识检索 → 报告生成
    workflow.add_edge("knowledge_agent", "report_agent")
    
    # 报告生成 → 结束
    workflow.add_edge("report_agent", END)
    
    return workflow.compile()


# ========== 协调者Agent类 ==========

class CoordinatorAgent:
    """
    协调者智能体 - 多Agent系统入口
    
    职责：
    1. 接收用户请求
    2. 调度多个子Agent协同工作
    3. 返回综合分析结果
    """
    
    def __init__(self):
        self._workflow = None
    
    @property
    def workflow(self):
        if self._workflow is None:
            self._workflow = build_multi_agent_workflow()
        return self._workflow
    
    def analyze(self, text: str, task_type: str = "auto") -> dict:
        """
        执行多Agent协作分析
        
        Args:
            text: 待分析文本
            task_type: 任务类型 (auto/analyze/review/report)
            
        Returns:
            包含所有Agent分析结果的字典
        """
        initial_state = {
            "input_text": text,
            "task_type": task_type,
            "sentiment_result": {},
            "topic_result": {},
            "risk_result": {},
            "knowledge_results": [],
            "risk_level": "low",
            "needs_review": False,
            "alert_triggered": False,
            "review_suggestion": "",
            "review_priority": 0,
            "final_report": "",
            "agent_logs": [],
        }
        
        result = self.workflow.invoke(initial_state)
        return result
    
    def get_agent_names(self) -> list:
        """获取所有注册的子Agent名称"""
        return [
            "SentimentAgent - 情感分析专家",
            "TopicAgent - 主题聚类专家",
            "RiskAgent - 风险评估专家",
            "ReviewDecisionAgent - 审核决策专家",
            "KnowledgeAgent - 知识检索专家",
            "ReportAgent - 报告生成专家",
        ]


# 全局单例
_coordinator = None

def get_coordinator():
    global _coordinator
    if _coordinator is None:
        _coordinator = CoordinatorAgent()
    return _coordinator


if __name__ == "__main__":
    print("=" * 60)
    print("多智能体协作系统测试")
    print("=" * 60)
    
    coordinator = CoordinatorAgent()
    
    test_text = "最近压力好大，考试考不好，室友关系也不太好，经常失眠"
    print(f"\n输入: {test_text}")
    print("-" * 40)
    
    result = coordinator.analyze(test_text)
    
    print(f"\n风险等级: {result['risk_level']}")
    print(f"需要审核: {result['needs_review']}")
    print(f"审核优先级: {result['review_priority']}")
    print(f"\n综合报告:\n{result['final_report']}")
    print(f"\nAgent执行日志:")
    for log in result['agent_logs']:
        print(f"  [{log['status']}] {log['agent']}: {log['detail']}")
