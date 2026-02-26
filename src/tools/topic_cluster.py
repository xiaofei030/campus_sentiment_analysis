# src/tools/topic_cluster.py
"""
主题聚类工具 - 识别文本中的主要话题/主题
"""
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
import json
from src.config import get_deepseek_llm


class TopicClusterResult(BaseModel):
    """主题聚类结果"""
    main_topic: str = Field(description="主要话题，如：学业、人际关系、就业、生活、情感等")
    sub_topics: List[str] = Field(description="细分话题列表")
    keywords: List[str] = Field(description="关键词列表")
    confidence: float = Field(description="分类置信度, 0-1之间")
    reasoning: str = Field(description="分类理由")


@tool
def cluster_topic(text: str) -> str:
    """
    识别文本的主题和话题分类。输入一段校园相关文本，返回主题聚类结果。
    
    参数:
        text: 要分析的文本
        
    返回:
        JSON字符串，包含main_topic, sub_topics, keywords, confidence, reasoning字段
    """
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个校园话题分析专家。请分析文本，识别其主要话题和关键词。

主要话题类别：
- 学业：课程、考试、作业、学习压力、选课等
- 人际关系：室友、同学、朋友、社交等
- 就业：实习、求职、考研、职业规划等
- 生活：食堂、宿舍、校园设施等
- 情感：恋爱、家庭、个人情绪等
- 活动：社团、比赛、志愿者等
- 其他

输出要求：
1. main_topic 是最主要的话题类别
2. sub_topics 是细分话题标签列表
3. keywords 是关键词列表（3-5个）
4. confidence 是0-1之间的置信度
5. reasoning 用中文说明分类理由

返回严格的JSON格式。"""),
            ("human", "分析以下文本的话题：\n{text}")
        ])

        llm = get_deepseek_llm()
        parser = JsonOutputParser(pydantic_object=TopicClusterResult)
        chain = prompt | llm | parser
        
        result = chain.invoke({"text": text})
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "main_topic": "其他",
            "sub_topics": [],
            "keywords": [],
            "confidence": 0.0,
            "reasoning": f"分析时出错: {str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False)


# 工具实例
topic_clusterer = cluster_topic


if __name__ == "__main__":
    test_text = "明天就要期末考试了，我还有三门课没复习完，压力好大"
    print(f"测试文本: {test_text}")
    result = cluster_topic.invoke(test_text)
    print(f"分析结果: {result}")
