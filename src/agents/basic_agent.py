# src/agents/basic_agent.py
"""
第二步：支持多工具的智能体
- sentiment_analyzer: 情感分析
- topic_clusterer: 主题聚类
- risk_screener: 风险筛查
"""
from langchain_core.prompts import ChatPromptTemplate
from src.config import get_deepseek_llm
from src.tools.sentiment_tool import sentiment_analyzer
from src.tools.topic_cluster import topic_clusterer
from src.tools.risk_screener import risk_screener
import json


class BasicSentimentAgent:
    """支持多工具的校园情感分析智能体"""

    def __init__(self):
        # 1. 获取LLM
        self.llm = get_deepseek_llm()
        
        # 2. 注册所有工具
        self.tools = {
            "sentiment": sentiment_analyzer,
            "topic": topic_clusterer,
            "risk": risk_screener,
        }
        
        # 3. 创建提示词模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个校园情感分析助手，能够进行多维度分析。
请根据工具的分析结果，给出综合、友好的中文回复和建议。"""),
            ("human", "{input}")
        ])
        
        # 4. 创建处理链
        self.chain = self.prompt | self.llm

    def analyze(self, text: str, mode: str = "full") -> str:
        """
        分析文本
        
        参数:
            text: 要分析的文本
            mode: 分析模式
                - "sentiment": 仅情感分析
                - "topic": 仅主题分类
                - "risk": 仅风险筛查
                - "full": 完整分析（所有工具）
        """
        try:
            results = {}
            
            # 根据模式调用工具
            if mode in ["sentiment", "full"]:
                print("  → 调用 sentiment_analyzer...")
                results["sentiment"] = json.loads(sentiment_analyzer.invoke(text))
                
            if mode in ["topic", "full"]:
                print("  → 调用 topic_clusterer...")
                results["topic"] = json.loads(topic_clusterer.invoke(text))
                
            if mode in ["risk", "full"]:
                print("  → 调用 risk_screener...")
                results["risk"] = json.loads(risk_screener.invoke(text))
            
            # 构建分析报告
            report = self._build_report(text, results)
            
            # 让LLM生成友好回复
            response = self.chain.invoke({"input": report})
            
            if hasattr(response, 'content'):
                return response.content
            return str(response)
            
        except Exception as e:
            return f"分析出错: {str(e)}"

    def _build_report(self, text: str, results: dict) -> str:
        """构建分析报告"""
        report = f'用户输入的文本："{text}"\n\n分析结果：\n'
        
        if "sentiment" in results:
            s = results["sentiment"]
            report += f"""
【情感分析】
- 情感倾向：{s.get('sentiment', '未知')}
- 具体情绪：{', '.join(s.get('emotions', [])) or '无'}
- 置信度：{s.get('confidence', 0):.0%}
- 理由：{s.get('reasoning', '无')}
"""
        
        if "topic" in results:
            t = results["topic"]
            report += f"""
【主题分类】
- 主要话题：{t.get('main_topic', '未知')}
- 细分话题：{', '.join(t.get('sub_topics', [])) or '无'}
- 关键词：{', '.join(t.get('keywords', [])) or '无'}
"""
        
        if "risk" in results:
            r = results["risk"]
            report += f"""
【风险评估】
- 风险等级：{r.get('risk_level', '未知')}
- 风险信号：{', '.join(r.get('risk_indicators', [])) or '无'}
- 建议行动：{', '.join(r.get('suggested_actions', [])) or '无'}
"""
        
        report += "\n请根据以上分析，用中文给出综合总结和建议。"
        return report

    def chat(self):
        """交互式聊天"""
        print("=" * 50)
        print("🎓 校园情感分析助手 (多工具版)")
        print("=" * 50)
        print("分析模式：")
        print("  [1] 完整分析 (情感+主题+风险)")
        print("  [2] 仅情感分析")
        print("  [3] 仅主题分类")
        print("  [4] 仅风险筛查")
        print("  输入 'quit' 退出")
        print("=" * 50)

        mode_map = {"1": "full", "2": "sentiment", "3": "topic", "4": "risk"}
        current_mode = "full"

        while True:
            try:
                user_input = input("\n💬 请输入文本 (或输入1-4切换模式): ").strip()

                if user_input.lower() in ["退出", "quit", "exit", "q"]:
                    print("👋 再见！")
                    break

                if user_input in mode_map:
                    current_mode = mode_map[user_input]
                    mode_names = {"full": "完整分析", "sentiment": "情感分析", 
                                  "topic": "主题分类", "risk": "风险筛查"}
                    print(f"✅ 已切换到: {mode_names[current_mode]}")
                    continue

                if not user_input:
                    print("⚠️ 请输入内容")
                    continue

                print(f"\n🔍 分析中 (模式: {current_mode})...")
                response = self.analyze(user_input, mode=current_mode)
                print(f"\n📊 分析结果:\n{response}")

            except KeyboardInterrupt:
                print("\n\n程序被中断")
                break
            except EOFError:
                print("\n\n输入结束")
                break


# 延迟初始化
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = BasicSentimentAgent()
    return _agent


if __name__ == "__main__":
    print("正在初始化智能体...")
    agent = BasicSentimentAgent()
    agent.chat()
