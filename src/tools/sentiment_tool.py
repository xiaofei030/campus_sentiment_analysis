# src/tools/sentiment_tool.py
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
import json
from src.config import get_deepseek_llm


# 定义输出结构（让AI返回结构化JSON）
class SentimentAnalysisResult(BaseModel):
    sentiment: str = Field(description="整体情感倾向: positive, negative, neutral")
    emotions: List[str] = Field(description="细粒度情绪列表，如: 焦虑, 压力, 喜悦等")
    confidence: float = Field(description="分析置信度, 0-1之间")
    reasoning: str = Field(description="简要分析理由")


@tool
def analyze_sentiment(text: str) -> str:
    """
    分析文本的情感和情绪。输入一段文本，返回情感分析结果。

    参数:
        text: 要分析的文本

    返回:
        JSON字符串，包含sentiment, emotions, confidence, reasoning字段
    """
    try:
        # 1. 创建提示词模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个校园心理分析专家，专门分析大学生的情感状态。
            请仔细分析文本，识别整体情感和具体情绪。

            输出要求：
            1. sentiment只能是 positive, negative, neutral 三者之一
            2. emotions列表包含具体的情绪标签，如：焦虑、压力、愤怒、喜悦、迷茫、孤独等
            3. confidence是一个0-1之间的浮点数，表示你的确信程度
            4. reasoning用中文简要说明分析理由

            返回格式必须是严格的JSON，不要有其他内容。"""),
            ("human", "分析以下文本：\n{text}")
        ])

        # 2. 获取LLM实例
        llm = get_deepseek_llm()

        # 3. 创建解析器
        parser = JsonOutputParser(pydantic_object=SentimentAnalysisResult)

        # 4. 构建处理链
        chain = prompt | llm | parser

        # 5. 执行分析
        result = chain.invoke({"text": text})

        # 6. 返回JSON字符串
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        # 如果出错，返回一个简单的分析结果
        error_result = {
            "sentiment": "neutral",
            "emotions": [],
            "confidence": 0.0,
            "reasoning": f"分析时出错: {str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False)


# 工具实例，方便导入
sentiment_analyzer = analyze_sentiment

# 测试函数
if __name__ == "__main__":
    # 简单测试
    test_text = "明天就要考试了，我什么都没复习，好焦虑啊"
    print(f"测试文本: {test_text}")
    result = analyze_sentiment.invoke(test_text)
    print(f"分析结果: {result}")