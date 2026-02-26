# src/tools/risk_screener.py
"""
风险筛查工具 - 识别文本中的心理风险信号
"""
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
import json
from src.config import get_deepseek_llm


class RiskScreenResult(BaseModel):
    """风险筛查结果"""
    risk_level: str = Field(description="风险等级: low, medium, high, critical")
    risk_indicators: List[str] = Field(description="识别到的风险信号列表")
    suggested_actions: List[str] = Field(description="建议采取的行动")
    confidence: float = Field(description="判断置信度, 0-1之间")
    reasoning: str = Field(description="风险判断理由")


@tool
def screen_risk(text: str) -> str:
    """
    筛查文本中的心理风险信号。输入一段文本，返回风险评估结果。
    
    参数:
        text: 要筛查的文本
        
    返回:
        JSON字符串，包含risk_level, risk_indicators, suggested_actions, confidence, reasoning字段
    """
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个校园心理健康风险评估专家。请分析文本中可能存在的心理风险信号。

风险等级定义：
- low（低风险）：正常的负面情绪表达，如一般的学习压力、小烦恼
- medium（中等风险）：持续的负面情绪，如长期焦虑、社交回避、失眠
- high（高风险）：明显的心理困扰信号，如严重抑郁倾向、自我否定、绝望感
- critical（危急）：自伤/自杀倾向、极端想法

常见风险信号：
- 情绪类：极度悲伤、绝望、无助、空虚
- 行为类：社交隔离、睡眠问题、食欲变化
- 认知类：自我否定、觉得是负担、没有希望
- 危急信号：提及自伤、结束生命、告别等

输出要求：
1. risk_level 必须是 low/medium/high/critical 之一
2. risk_indicators 列出识别到的具体风险信号
3. suggested_actions 给出建议行动
4. confidence 是0-1之间的置信度
5. reasoning 用中文说明判断理由

注意：保持客观专业，避免过度解读。返回严格的JSON格式。"""),
            ("human", "请评估以下文本的心理风险：\n{text}")
        ])

        llm = get_deepseek_llm()
        parser = JsonOutputParser(pydantic_object=RiskScreenResult)
        chain = prompt | llm | parser
        
        result = chain.invoke({"text": text})
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "risk_level": "low",
            "risk_indicators": [],
            "suggested_actions": ["建议重新分析"],
            "confidence": 0.0,
            "reasoning": f"分析时出错: {str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False)


# 工具实例
risk_screener = screen_risk


if __name__ == "__main__":
    test_texts = [
        "今天作业好多，有点累",
        "最近总是失眠，感觉很焦虑，不想和任何人说话",
    ]
    
    for text in test_texts:
        print(f"\n测试文本: {text}")
        result = screen_risk.invoke(text)
        print(f"风险评估: {result}")

