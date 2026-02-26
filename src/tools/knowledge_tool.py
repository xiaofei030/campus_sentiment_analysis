# src/tools/knowledge_tool.py
"""
知识库查询工具 - 从向量知识库中检索相关信息
"""
from langchain_core.tools import tool
import json


@tool
def query_knowledge(query: str) -> str:
    """
    从校园心理健康知识库中检索相关信息。
    
    参数:
        query: 查询问题，如"考试焦虑怎么办"、"心理咨询热线"
        
    返回:
        JSON字符串，包含检索到的相关知识
    """
    try:
        # 延迟导入，避免循环依赖
        from src.data_pipeline import get_knowledge_base
        
        kb = get_knowledge_base()
        
        if kb.vectorstore is None:
            return json.dumps({
                "found": False,
                "message": "知识库未初始化，请先运行 data_pipeline.py 构建知识库",
                "results": []
            }, ensure_ascii=False)
        
        # 搜索相关文档
        results = kb.search_with_scores(query, k=3)
        
        if not results:
            return json.dumps({
                "found": False,
                "message": "未找到相关信息",
                "results": []
            }, ensure_ascii=False)
        
        # 格式化结果
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "relevance_score": round(1 - score, 2)  # 转换为相关度（越高越好）
            })
        
        return json.dumps({
            "found": True,
            "message": f"找到 {len(formatted_results)} 条相关信息",
            "results": formatted_results
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "found": False,
            "message": f"查询出错: {str(e)}",
            "results": []
        }, ensure_ascii=False)


# 工具实例
knowledge_searcher = query_knowledge


if __name__ == "__main__":
    # 测试
    test_queries = [
        "考试焦虑怎么办",
        "心理咨询热线电话",
        "室友关系不好怎么处理"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        result = query_knowledge.invoke(query)
        print(f"结果: {result}")

