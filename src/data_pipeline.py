# src/data_pipeline.py
"""
数据管道 - 构建和管理向量知识库
支持多种文档格式：TXT、PDF、Word (doc/docx)
自动将学校相关信息替换为目标学校（参见 knowledge_docs/school_config.py）
"""
import os
import sys
from pathlib import Path
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import CHROMA_PERSIST_DIR

BASE_DIR = Path(__file__).resolve().parents[1]

# 导入学校配置（用于文本替换）
sys.path.insert(0, str(BASE_DIR / "knowledge_docs"))
try:
    from school_config import REPLACEMENTS, SCHOOL_INFO
    ENABLE_SCHOOL_REPLACEMENT = True
    print(f"[配置] 学校信息替换已启用 -> {SCHOOL_INFO['name']}")
except ImportError:
    ENABLE_SCHOOL_REPLACEMENT = False
    REPLACEMENTS = {}
    print("[配置] 未找到 school_config.py，跳过学校信息替换")

# 支持的文件格式
SUPPORTED_EXTENSIONS = {
    '.txt': 'text',
    '.pdf': 'pdf',
    '.docx': 'word',
    '.doc': 'word',
}


def preprocess_text(text: str) -> str:
    """预处理文本：替换学校相关信息"""
    if not ENABLE_SCHOOL_REPLACEMENT or not text:
        return text
    
    result = text
    for old, new in REPLACEMENTS.items():
        if old and new is not None:
            result = result.replace(old, new)
    return result


class KnowledgeBase:
    """向量知识库管理"""
    
    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        persist_path = Path(persist_dir)
        if not persist_path.is_absolute():
            persist_path = BASE_DIR / persist_path
        self.persist_dir = str(persist_path)
        
        # 使用本地嵌入模型（免费，无需API）
        print("加载嵌入模型...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # 加载或创建向量库
        if os.path.exists(persist_dir) and os.listdir(persist_dir):
            print(f"从 {persist_dir} 加载已有知识库...")
            self.vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings
            )
        else:
            print("知识库为空，请先添加文档")
            self.vectorstore = None
    
    def _load_single_file(self, file_path: Path):
        """加载单个文件，根据格式选择加载器"""
        ext = file_path.suffix.lower()
        file_type = SUPPORTED_EXTENSIONS.get(ext)
        
        if not file_type:
            print(f"  [跳过] 不支持的格式: {file_path.name}")
            return []
        
        try:
            if file_type == 'text':
                loader = TextLoader(str(file_path), encoding='utf-8')
            elif file_type == 'pdf':
                loader = PyPDFLoader(str(file_path))
            elif file_type == 'word':
                # docx2txt 同时支持 .doc 和 .docx
                loader = Docx2txtLoader(str(file_path))
            else:
                return []
            
            docs = loader.load()
            # 添加文件来源到 metadata，并进行文本预处理
            for doc in docs:
                doc.metadata['source_file'] = file_path.name
                doc.metadata['file_type'] = file_type
                # 替换学校相关信息
                doc.page_content = preprocess_text(doc.page_content)
            
            print(f"  [成功] {file_path.name} ({len(docs)} 页/段)")
            return docs
            
        except Exception as e:
            print(f"  [失败] {file_path.name}: {e}")
            return []
    
    def add_documents_from_directory(self, docs_dir: str = None):
        """从目录加载文档并添加到知识库（支持 txt/pdf/docx）"""
        docs_path = Path(docs_dir) if docs_dir else (BASE_DIR / "knowledge_docs")
        if not docs_path.is_absolute():
            docs_path = BASE_DIR / docs_path
        if not docs_path.exists():
            print(f"目录不存在: {docs_path}")
            return False
            
        print(f"从 {docs_path} 加载文档...")
        print(f"支持格式: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        print("-" * 40)
        
        # 扫描所有支持的文件
        all_documents = []
        for ext in SUPPORTED_EXTENSIONS.keys():
            for file_path in docs_path.glob(f"**/*{ext}"):
                # 跳过 Python 脚本
                if file_path.suffix == '.py':
                    continue
                docs = self._load_single_file(file_path)
                all_documents.extend(docs)
        
        if not all_documents:
            print("未找到任何可加载的文档")
            return False
        
        print("-" * 40)
        print(f"共加载 {len(all_documents)} 个文档片段")
        
        # 分割文档
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", " "]
        )
        splits = text_splitter.split_documents(all_documents)
        print(f"分割为 {len(splits)} 个文本块")
        
        # 创建或更新向量库
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.persist_dir
        )
        
        print(f"知识库已保存到 {self.persist_dir}")
        return True
    
    def search(self, query: str, k: int = 3) -> list:
        """搜索相关文档"""
        if self.vectorstore is None:
            return []
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def search_with_scores(self, query: str, k: int = 3) -> list:
        """搜索相关文档并返回相似度分数"""
        if self.vectorstore is None:
            return []
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return results


# 全局知识库实例（延迟初始化）
_kb = None

def get_knowledge_base() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb


if __name__ == "__main__":
    # 测试：构建知识库
    print("=" * 50)
    print("构建向量知识库")
    print("=" * 50)
    
    kb = KnowledgeBase()
    kb.add_documents_from_directory("knowledge_docs")
    
    # 测试搜索
    print("\n测试搜索...")
    query = "考试焦虑怎么办"
    results = kb.search(query, k=2)
    
    print(f"\n查询: {query}")
    for i, doc in enumerate(results):
        print(f"\n结果 {i+1}:")
        print(doc.page_content[:200] + "...")

