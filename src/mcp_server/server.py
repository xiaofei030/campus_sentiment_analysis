# src/mcp_server/server.py
"""
MCP Server - Model Context Protocol 服务器
将校园情感分析的能力以 MCP 协议暴露，供 Cursor / Claude 等 AI 工具调用

支持的 Tools：
1. analyze_sentiment - 情感分析
2. analyze_topic - 主题聚类
3. screen_risk - 风险筛查
4. search_knowledge - 知识库查询
5. multi_agent_analyze - 多Agent协作分析
6. get_dashboard_stats - 获取可视化面板数据
7. get_review_tasks - 获取待审核任务
8. submit_review - 提交审核结果

启动方式：
    python -m src.mcp_server.server
"""
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

import json
import asyncio
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.stdio import run_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[MCP] mcp 库未安装，请运行: pip install mcp")

from src.tools.sentiment_tool import sentiment_analyzer
from src.tools.topic_cluster import topic_clusterer
from src.tools.risk_screener import risk_screener
from src.tools.knowledge_tool import knowledge_searcher


# ========== MCP Tool 定义 ==========

MCP_TOOLS = [
    {
        "name": "analyze_sentiment",
        "description": "分析文本的情感倾向和情绪。适用于分析大学生发表的文本内容，识别积极/消极/中性情感，以及具体的情绪标签（焦虑、压力、喜悦等）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要分析的文本内容"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "analyze_topic",
        "description": "对文本进行主题聚类分析。识别文本的主要话题（如学业压力、人际关系、就业焦虑等）、子话题和关键词。",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要分析的文本内容"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "screen_risk",
        "description": "对文本进行心理风险筛查。评估文本中的心理风险信号，返回风险等级（low/medium/high/critical）、风险指标和建议行动。",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要筛查的文本内容"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "search_knowledge",
        "description": "在校园心理健康知识库中进行语义检索。基于 ChromaDB 向量数据库，返回与查询最相关的知识条目。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "检索查询词"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量，默认3",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "multi_agent_analyze",
        "description": "调用多智能体协作系统进行全面分析。协调情感Agent、主题Agent、风险Agent、审核决策Agent和报告Agent协同工作，返回综合分析报告。",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要分析的文本内容"
                }
            },
            "required": ["text"]
        }
    },
]


# ========== Tool 执行函数 ==========

def execute_tool(tool_name: str, arguments: dict) -> str:
    """执行 MCP Tool"""
    try:
        if tool_name == "analyze_sentiment":
            result = sentiment_analyzer.invoke(arguments["text"])
            return result
        
        elif tool_name == "analyze_topic":
            result = topic_clusterer.invoke(arguments["text"])
            return result
        
        elif tool_name == "screen_risk":
            result = risk_screener.invoke(arguments["text"])
            return result
        
        elif tool_name == "search_knowledge":
            result = knowledge_searcher.invoke(arguments["query"])
            return result
        
        elif tool_name == "multi_agent_analyze":
            from src.agents.coordinator_agent import get_coordinator
            coordinator = get_coordinator()
            result = coordinator.analyze(arguments["text"])
            # 转换为可序列化的格式
            return json.dumps({
                "sentiment": result.get("sentiment_result", {}),
                "topic": result.get("topic_result", {}),
                "risk": result.get("risk_result", {}),
                "risk_level": result.get("risk_level", "unknown"),
                "needs_review": result.get("needs_review", False),
                "review_priority": result.get("review_priority", 0),
                "review_suggestion": result.get("review_suggestion", ""),
                "report": result.get("final_report", ""),
                "agent_logs": result.get("agent_logs", []),
            }, ensure_ascii=False, indent=2)
        
        else:
            return json.dumps({"error": f"未知工具: {tool_name}"})
    
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ========== MCP Server 主逻辑 ==========

if MCP_AVAILABLE:
    server = Server("campus-sentiment-analysis")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """列出所有可用的 MCP 工具"""
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["input_schema"]
            )
            for t in MCP_TOOLS
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """执行 MCP 工具调用"""
        result = execute_tool(name, arguments)
        return [TextContent(type="text", text=result)]


# ========== 非MCP模式的HTTP接口 ==========

def get_tool_list() -> list:
    """获取工具列表（非MCP模式下也可使用）"""
    return MCP_TOOLS


def call_tool_directly(name: str, arguments: dict) -> str:
    """直接调用工具（非MCP模式）"""
    return execute_tool(name, arguments)


# ========== 启动入口 ==========

async def main():
    """启动 MCP Server"""
    if not MCP_AVAILABLE:
        print("[MCP] 无法启动 MCP Server，请先安装 mcp 库")
        print("  pip install mcp")
        return
    
    print("[MCP] 校园情感分析 MCP Server 启动中...")
    print(f"[MCP] 已注册 {len(MCP_TOOLS)} 个工具")
    for t in MCP_TOOLS:
        print(f"  - {t['name']}: {t['description'][:50]}...")
    
    await run_server(server)


if __name__ == "__main__":
    asyncio.run(main())
