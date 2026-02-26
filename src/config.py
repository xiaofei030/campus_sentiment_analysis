# src/config.py - 统一管理配置
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# DeepSeek配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL = "deepseek-chat"

# 验证配置
if not DEEPSEEK_API_KEY:
    raise ValueError("请在.env文件中设置DEEPSEEK_API_KEY")


# 创建OpenAI客户端（兼容DeepSeek）
def get_deepseek_client():
    """获取DeepSeek客户端"""
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_API_BASE
    )


# 创建LangChain LLM实例
def get_deepseek_llm():
    """获取LangChain封装的DeepSeek LLM"""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        openai_api_key=DEEPSEEK_API_KEY,
        openai_api_base=DEEPSEEK_API_BASE,
        model_name=DEEPSEEK_MODEL,
        temperature=0.7,
        max_tokens=1000
    )


# ChromaDB配置
CHROMA_PERSIST_DIR = "./chroma_data"  # 向量数据库存储位置
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# 测试数据路径
TEST_DATA_DIR = "./data/test"
os.makedirs(TEST_DATA_DIR, exist_ok=True)