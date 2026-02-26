# src/workflows/risk_alert.py
"""
风险预警工作流 - 基于 LangGraph 的多步骤处理流程
当检测到高风险时，触发预警流程
"""
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
import json

from src.tools.sentiment_tool import sentiment_analyzer
from src.tools.risk_screener import risk_screener
from src.tools.knowledge_tool import knowledge_searcher
from src.config import get_deepseek_llm


class AlertState(TypedDict):
    """工作流状态"""
    input_text: str                    # 输入文本
    sentiment_result: dict             # 情感分析结果
    risk_result: dict                  # 风险评估结果
    knowledge_results: list            # 知识库检索结果
    risk_level: str                    # 风险等级
    final_response: str                # 最终回复
    alert_triggered: bool              # 是否触发预警


def analyze_sentiment(state: AlertState) -> AlertState:
    """步骤1：情感分析"""
    print("  [1/4] 执行情感分析...")
    result = sentiment_analyzer.invoke(state["input_text"])
    state["sentiment_result"] = json.loads(result)
    return state


def assess_risk(state: AlertState) -> AlertState:
    """步骤2：风险评估"""
    print("  [2/4] 执行风险评估...")
    result = risk_screener.invoke(state["input_text"])
    risk_data = json.loads(result)
    state["risk_result"] = risk_data
    state["risk_level"] = risk_data.get("risk_level", "low")
    
    # 判断是否触发预警
    state["alert_triggered"] = state["risk_level"] in ["high", "critical"]
    return state


def search_knowledge(state: AlertState) -> AlertState:
    """步骤3：检索相关知识"""
    print("  [3/4] 检索相关知识...")
    
    # 根据情感和风险结果构建查询
    emotions = state["sentiment_result"].get("emotions", [])
    risk_indicators = state["risk_result"].get("risk_indicators", [])
    
    # 构建查询词
    query_terms = emotions + risk_indicators
    if not query_terms:
        query_terms = ["心理健康", "情绪调节"]
    
    query = " ".join(query_terms[:3])
    result = knowledge_searcher.invoke(query)
    knowledge_data = json.loads(result)
    
    state["knowledge_results"] = knowledge_data.get("results", [])
    return state


def generate_response(state: AlertState) -> AlertState:
    """步骤4：生成最终回复"""
    print("  [4/4] 生成回复...")
    
    llm = get_deepseek_llm()
    
    # 构建提示
    risk_level_map = {
        "low": "低风险",
        "medium": "中等风险", 
        "high": "高风险",
        "critical": "危急"
    }
    
    knowledge_text = ""
    if state["knowledge_results"]:
        knowledge_text = "\n\n相关建议：\n"
        for i, item in enumerate(state["knowledge_results"][:2], 1):
            knowledge_text += f"{i}. {item['content'][:200]}...\n"
    
    prompt = f"""你是一个温暖、专业的校园心理支持助手。

用户输入："{state['input_text']}"

分析结果：
- 情感倾向：{state['sentiment_result'].get('sentiment', '未知')}
- 具体情绪：{', '.join(state['sentiment_result'].get('emotions', [])) or '无'}
- 风险等级：{risk_level_map.get(state['risk_level'], '未知')}
- 风险信号：{', '.join(state['risk_result'].get('risk_indicators', [])) or '无'}
{knowledge_text}

请根据以上信息，用温暖、理解的语气回复用户。
{"⚠️ 注意：这是高风险情况，请在回复中提供专业求助资源（如心理咨询热线）。" if state['alert_triggered'] else ""}
"""
    
    response = llm.invoke(prompt)
    state["final_response"] = response.content if hasattr(response, 'content') else str(response)
    
    return state


def route_by_risk(state: AlertState) -> Literal["search_knowledge", "generate_simple"]:
    """路由：根据风险等级决定下一步"""
    if state["risk_level"] in ["medium", "high", "critical"]:
        return "search_knowledge"
    return "generate_simple"


def generate_simple_response(state: AlertState) -> AlertState:
    """简单回复（低风险情况）"""
    print("  [3/4] 生成简单回复...")
    
    llm = get_deepseek_llm()
    
    prompt = f"""你是一个友好的校园助手。

用户说："{state['input_text']}"

情感分析：{state['sentiment_result'].get('sentiment', '中性')}
具体情绪：{', '.join(state['sentiment_result'].get('emotions', [])) or '无'}

请用简短、友好的方式回复用户。"""
    
    response = llm.invoke(prompt)
    state["final_response"] = response.content if hasattr(response, 'content') else str(response)
    state["knowledge_results"] = []
    
    return state


def build_workflow():
    """构建工作流图"""
    workflow = StateGraph(AlertState)
    
    # 添加节点
    workflow.add_node("analyze_sentiment", analyze_sentiment)
    workflow.add_node("assess_risk", assess_risk)
    workflow.add_node("search_knowledge", search_knowledge)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("generate_simple", generate_simple_response)
    
    # 设置入口
    workflow.set_entry_point("analyze_sentiment")
    
    # 添加边
    workflow.add_edge("analyze_sentiment", "assess_risk")
    
    # 条件路由
    workflow.add_conditional_edges(
        "assess_risk",
        route_by_risk,
        {
            "search_knowledge": "search_knowledge",
            "generate_simple": "generate_simple"
        }
    )
    
    workflow.add_edge("search_knowledge", "generate_response")
    workflow.add_edge("generate_response", END)
    workflow.add_edge("generate_simple", END)
    
    return workflow.compile()


# 全局工作流实例
_workflow = None

def get_workflow():
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
    return _workflow


def run_alert_workflow(text: str) -> dict:
    """运行预警工作流"""
    workflow = get_workflow()
    
    initial_state = {
        "input_text": text,
        "sentiment_result": {},
        "risk_result": {},
        "knowledge_results": [],
        "risk_level": "low",
        "final_response": "",
        "alert_triggered": False
    }
    
    result = workflow.invoke(initial_state)
    return result


if __name__ == "__main__":
    print("=" * 50)
    print("风险预警工作流测试")
    print("=" * 50)
    
    test_texts = [
        "今天天气真好，心情不错",
        "最近压力好大，考试总是考不好",
        "我真的很累，感觉活着没什么意思"
    ]
    
    for text in test_texts:
        print(f"\n输入: {text}")
        print("-" * 30)
        result = run_alert_workflow(text)
        print(f"风险等级: {result['risk_level']}")
        print(f"触发预警: {result['alert_triggered']}")
        print(f"回复: {result['final_response'][:200]}...")

