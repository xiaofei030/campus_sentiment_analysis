# src/crawler/topic_extractor.py
"""
AI话题提取器 - 吸收自 BettaFish MindSpider/BroadTopicExtraction/topic_extractor.py
基于 DeepSeek LLM 从热点新闻中提取校园相关话题和关键词
"""
import json
import re
from typing import List, Dict, Tuple
import logging

from src.config import get_deepseek_llm

logger = logging.getLogger(__name__)


class TopicExtractor:
    """
    AI 话题提取器

    设计模式吸收自 BettaFish TopicExtractor：
    - LLM 驱动的关键词提取
    - JSON 结构化输出 + 多层 fallback 解析
    - 校园舆情场景定制 prompt
    """

    def __init__(self):
        self.llm = get_deepseek_llm()

    # ────────── 核心能力 ──────────

    def extract_keywords_and_summary(
        self, news_list: List[Dict], max_keywords: int = 60
    ) -> Tuple[List[str], str]:
        """
        从新闻列表中提取校园相关关键词和分析总结

        Args:
            news_list: [{title, source_name, ...}, ...]
            max_keywords: 最大关键词数

        Returns:
            (关键词列表, 新闻分析总结)
        """
        if not news_list:
            return [], "暂无热点新闻数据"

        news_text = self._build_news_text(news_list)
        prompt = self._build_prompt(news_text, max_keywords)

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            keywords, summary = self._parse_result(content)
            logger.info(f"[TopicExtractor] 提取 {len(keywords)} 个关键词")
            return keywords[:max_keywords], summary
        except Exception as e:
            logger.error(f"[TopicExtractor] LLM 调用失败: {e}")
            return self._fallback_keywords(news_list), "AI话题提取暂时不可用，已使用标题关键词替代。"

    def get_search_keywords(self, keywords: List[str], limit: int = 15) -> List[str]:
        """过滤出适合社交平台搜索的关键词"""
        seen = set()
        result = []
        for kw in keywords:
            kw = kw.strip()
            if (
                1 < len(kw) < 20
                and kw not in seen
                and not kw.isdigit()
                and not re.match(r"^[a-zA-Z]+$", kw)
            ):
                seen.add(kw)
                result.append(kw)
        return result[:limit]

    # ────────── 内部方法 ──────────

    def _build_news_text(self, news_list: List[Dict]) -> str:
        lines = []
        for i, n in enumerate(news_list[:200], 1):  # 限制 200 条避免 token 过长
            title = re.sub(r"[#@]", "", n.get("title", "")).strip()
            src = n.get("source_name", n.get("source", ""))
            lines.append(f"{i}. 【{src}】{title}")
        return "\n".join(lines)

    def _build_prompt(self, news_text: str, max_keywords: int) -> str:
        return f"""你是一位校园舆情分析专家。请分析以下热点新闻，完成两个任务：

=== 热点新闻列表 ===
{news_text}

=== 任务 ===

任务1：提取校园舆情监测关键词（最多{max_keywords}个）
- 重点关注与大学生、校园生活、就业、学业、心理健康相关的话题
- 关键词应适合在微博、知乎、贴吧等平台搜索
- 包含热点事件名称、相关人物、核心概念
- 按热度从高到低排列

任务2：撰写新闻分析总结（150-300字）
- 概括今日社会热点与校园舆情的关联
- 指出需要关注的潜在风险话题
- 语言客观简洁

请严格按照以下JSON格式输出，不要包含其他文字：
```json
{{
  "keywords": ["关键词1", "关键词2", ...],
  "summary": "分析总结内容..."
}}
```"""

    def _parse_result(self, text: str) -> Tuple[List[str], str]:
        """解析 LLM 返回的 JSON（含多层 fallback）"""
        # 尝试提取 json 代码块
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        raw = json_match.group(1) if json_match else text.strip()

        try:
            data = json.loads(raw)
            keywords = [str(k).strip() for k in data.get("keywords", []) if str(k).strip()]
            summary = data.get("summary", "").strip()
            # 去重保序
            seen = set()
            unique_kw = []
            for k in keywords:
                if k not in seen:
                    seen.add(k)
                    unique_kw.append(k)
            return unique_kw, summary or "分析结果已生成。"
        except json.JSONDecodeError:
            logger.warning("[TopicExtractor] JSON解析失败，尝试手动提取")
            return self._manual_parse(text)

    def _manual_parse(self, text: str) -> Tuple[List[str], str]:
        """当 JSON 解析失败时的手动提取"""
        keywords = re.findall(r'[""](.*?)[""]', text)
        keywords = [k.strip() for k in keywords if 1 < len(k.strip()) < 20]

        summary = ""
        for line in text.split("\n"):
            line = line.strip()
            if len(line) > 50 and ("今日" in line or "热点" in line or "校园" in line):
                summary = line
                break
        return keywords[:60], summary or "热点新闻分析结果。"

    def _fallback_keywords(self, news_list: List[Dict]) -> List[str]:
        """备用：从标题中提取简单关键词"""
        stopwords = {"的", "了", "在", "和", "与", "或", "但", "是", "有", "被", "将", "已", "正在", "不", "也", "都"}
        keywords = []
        for n in news_list[:50]:
            title = re.sub(r"[#@【】\[\]()（）：:，。！？]", " ", n.get("title", ""))
            for w in title.split():
                w = w.strip()
                if len(w) > 1 and w not in stopwords and w not in keywords:
                    keywords.append(w)
        return keywords[:30]
