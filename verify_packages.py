# test_minimal.py - 最小可行性测试
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import get_deepseek_client
from src.tools.sentiment_tool import analyze_sentiment
from src.agents.basic_agent import BasicSentimentAgent


def test_deepseek_connection():
    """测试DeepSeek API连接"""
    print("🔗 测试DeepSeek API连接...")
    try:
        client = get_deepseek_client()
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "请回复'连接成功'"}],
            max_tokens=10
        )
        print(f"   ✅ 连接成功: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False


def test_sentiment_tool():
    """测试情感分析工具"""
    print("\n🧠 测试情感分析工具...")
    test_cases = [
        "明天就要考试了，我什么都没复习，好焦虑啊",
        "今天食堂的糖醋排骨真好吃，心情都变好了",
        "宿舍的空调坏了，向宿管反映了一周还没人来修"
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n   测试案例 {i}: {text}")
        try:
            result = analyze_sentiment.invoke(text)
            print(f"      ✅ 分析成功: {result[:100]}...")  # 只显示前100字符
        except Exception as e:
            print(f"      ❌ 分析失败: {e}")

    return True


def test_basic_agent():
    """测试基础智能体"""
    print("\n🤖 测试基础智能体...")

    # 创建智能体
    agent = BasicSentimentAgent()

    # 测试查询
    test_queries = [
        "分析这句话的情感：'明天考试，我很紧张'",
        "请分析：'食堂的饭菜越来越难吃了' 这句话的情绪",
        "帮我分析一下这段文字的情感倾向：'虽然学习很累，但看到成绩进步还是很开心'"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n   查询 {i}: {query}")
        try:
            response = agent.analyze(query)
            print(f"      ✅ 智能体响应: {response}")
        except Exception as e:
            print(f"      ❌ 智能体失败: {e}")

    return True


def main():
    print("🚀 校园舆情系统 - 最小可行性测试")
    print("=" * 60)

    # 运行所有测试
    tests = [
        ("DeepSeek API连接", test_deepseek_connection),
        ("情感分析工具", test_sentiment_tool),
        ("基础智能体", test_basic_agent)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 正在测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
            results.append((test_name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("-" * 60)

    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name:20} {status}")
        if success:
            passed += 1

    print("-" * 60)
    print(f"总测试: {len(results)} 个, 通过: {passed} 个, 失败: {len(results) - passed} 个")

    if passed == len(results):
        print("\n🎉 所有测试通过！可以进入下一步开发。")
        print("   运行 'python src/agents/basic_agent.py' 开始交互式聊天")
    else:
        print("\n⚠️  部分测试失败，请检查问题后再继续。")


if __name__ == "__main__":
    main()