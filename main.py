# main.py
"""
校园情感分析系统 - 主入口
整合所有功能：情感分析、主题聚类、风险筛查、知识库、预警工作流
"""
import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_menu():
    """打印主菜单"""
    print("\n" + "=" * 55)
    print("🎓 校园情感分析系统")
    print("=" * 55)
    print("请选择功能：")
    print("  [1] 多工具智能体（情感+主题+风险）")
    print("  [2] 预警工作流（带知识库）")
    print("  [3] 构建/更新知识库")
    print("  [4] 单独测试 - 情感分析")
    print("  [5] 单独测试 - 主题聚类")
    print("  [6] 单独测试 - 风险筛查")
    print("  [7] 单独测试 - 知识库查询")
    print("  [q] 退出")
    print("-" * 55)


def run_multi_tool_agent():
    """运行多工具智能体"""
    from src.agents.basic_agent import BasicSentimentAgent
    print("\n🚀 启动多工具智能体...")
    agent = BasicSentimentAgent()
    agent.chat()


def run_alert_workflow():
    """运行预警工作流"""
    from src.workflows.risk_alert import run_alert_workflow
    
    print("\n🚨 预警工作流模式")
    print("输入文本进行分析，输入 'q' 退出")
    print("-" * 40)
    
    while True:
        text = input("\n💬 请输入文本: ").strip()
        if text.lower() in ['q', 'quit', '退出']:
            break
        if not text:
            continue
            
        print("\n⏳ 执行工作流...")
        result = run_alert_workflow(text)
        
        print("\n" + "=" * 40)
        print(f"📊 风险等级: {result['risk_level']}")
        print(f"⚠️ 触发预警: {'是' if result['alert_triggered'] else '否'}")
        print(f"\n💬 回复:\n{result['final_response']}")
        print("=" * 40)


def build_knowledge_base():
    """构建知识库"""
    from src.data_pipeline import KnowledgeBase
    
    print("\n📚 构建向量知识库...")
    kb = KnowledgeBase()
    kb.add_documents_from_directory()
    print("✅ 知识库构建完成！")


def test_sentiment():
    """测试情感分析"""
    from src.tools.sentiment_tool import sentiment_analyzer
    import json
    
    print("\n😊 情感分析测试")
    text = input("请输入文本: ").strip()
    if text:
        result = sentiment_analyzer.invoke(text)
        data = json.loads(result)
        print(f"\n结果: {json.dumps(data, ensure_ascii=False, indent=2)}")


def test_topic():
    """测试主题聚类"""
    from src.tools.topic_cluster import topic_clusterer
    import json
    
    print("\n📁 主题聚类测试")
    text = input("请输入文本: ").strip()
    if text:
        result = topic_clusterer.invoke(text)
        data = json.loads(result)
        print(f"\n结果: {json.dumps(data, ensure_ascii=False, indent=2)}")


def test_risk():
    """测试风险筛查"""
    from src.tools.risk_screener import risk_screener
    import json
    
    print("\n⚠️ 风险筛查测试")
    text = input("请输入文本: ").strip()
    if text:
        result = risk_screener.invoke(text)
        data = json.loads(result)
        print(f"\n结果: {json.dumps(data, ensure_ascii=False, indent=2)}")


def test_knowledge():
    """测试知识库查询"""
    from src.tools.knowledge_tool import knowledge_searcher
    import json
    
    print("\n📖 知识库查询测试")
    query = input("请输入查询: ").strip()
    if query:
        result = knowledge_searcher.invoke(query)
        data = json.loads(result)
        print(f"\n找到 {len(data.get('results', []))} 条结果:")
        for i, item in enumerate(data.get('results', []), 1):
            print(f"\n--- 结果 {i} (相关度: {item.get('relevance_score', 0)}) ---")
            print(item.get('content', '')[:300] + "...")


def main():
    """主函数"""
    print("\n" + "🎉 " * 10)
    print("欢迎使用校园情感分析系统！")
    print("🎉 " * 10)
    
    actions = {
        '1': run_multi_tool_agent,
        '2': run_alert_workflow,
        '3': build_knowledge_base,
        '4': test_sentiment,
        '5': test_topic,
        '6': test_risk,
        '7': test_knowledge,
    }
    
    while True:
        print_menu()
        choice = input("请选择 [1-7/q]: ").strip().lower()
        
        if choice in ['q', 'quit', '退出']:
            print("\n👋 再见！")
            break
        
        if choice in actions:
            try:
                actions[choice]()
            except KeyboardInterrupt:
                print("\n\n⚠️ 操作被中断")
            except Exception as e:
                print(f"\n❌ 出错: {e}")
        else:
            print("⚠️ 无效选择，请重试")


if __name__ == "__main__":
    main()

