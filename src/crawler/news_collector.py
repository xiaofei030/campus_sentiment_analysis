# src/crawler/news_collector.py
"""
热点新闻采集器 - 吸收自 BettaFish MindSpider/BroadTopicExtraction
从 12+ 公开新闻源实时采集热点新闻，无需登录和浏览器自动化
"""
import asyncio
import httpx
import json
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# 新闻API基础URL（公开免费接口）
NEWS_API_BASE = "https://newsnow.busiyi.world"

# 新闻源配置
SOURCE_CONFIG = {
    "weibo": {"name": "微博热搜", "category": "social"},
    "zhihu": {"name": "知乎热榜", "category": "qa"},
    "bilibili-hot-search": {"name": "B站热搜", "category": "video"},
    "toutiao": {"name": "今日头条", "category": "news"},
    "douyin": {"name": "抖音热榜", "category": "video"},
    "tieba": {"name": "百度贴吧", "category": "forum"},
    "coolapk": {"name": "酷安热榜", "category": "tech"},
    "thepaper": {"name": "澎湃新闻", "category": "news"},
    "wallstreetcn": {"name": "华尔街见闻", "category": "finance"},
    "cls-hot": {"name": "财联社", "category": "finance"},
    "xueqiu": {"name": "雪球热榜", "category": "finance"},
    "github-trending-today": {"name": "GitHub趋势", "category": "tech"},
}

# 与校园舆情相关度较高的新闻源（优先采集）
CAMPUS_PRIORITY_SOURCES = ["weibo", "zhihu", "bilibili-hot-search", "douyin", "tieba", "toutiao"]


class NewsCollector:
    """
    热点新闻采集器
    
    设计模式吸收自 BettaFish MindSpider/BroadTopicExtraction/get_today_news.py
    使用公开 API 采集多平台热点，不依赖浏览器自动化
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": NEWS_API_BASE,
        }

    async def fetch_source(self, source_id: str) -> Dict:
        """从单个新闻源获取数据"""
        url = f"{NEWS_API_BASE}/api/s?id={source_id}&latest"
        source_name = SOURCE_CONFIG.get(source_id, {}).get("name", source_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", []) if isinstance(data, dict) else []
                return {
                    "source": source_id,
                    "source_name": source_name,
                    "status": "success",
                    "items": items,
                    "count": len(items),
                }
        except httpx.TimeoutException:
            return {"source": source_id, "source_name": source_name, "status": "timeout", "items": [], "count": 0}
        except Exception as e:
            return {"source": source_id, "source_name": source_name, "status": "error", "error": str(e), "items": [], "count": 0}

    async def collect_news(
        self,
        sources: Optional[List[str]] = None,
        campus_priority: bool = False,
    ) -> Dict:
        """
        采集多平台热点新闻

        Args:
            sources: 指定新闻源列表，None 使用全部源
            campus_priority: True 只采集高相关源，False 采集全部源（推荐）
        
        Returns:
            {success, news_list, stats}
        """
        if sources is None:
            sources = CAMPUS_PRIORITY_SOURCES if campus_priority else list(SOURCE_CONFIG.keys())

        logger.info(f"[NewsCollector] 开始采集 {len(sources)} 个新闻源...")

        results = []
        for src in sources:
            result = await self.fetch_source(src)
            results.append(result)
            await asyncio.sleep(0.3)  # 礼貌延迟

        # 汇总
        news_list = []
        success_count = 0
        total_items = 0

        for r in results:
            if r["status"] == "success":
                success_count += 1
                for i, item in enumerate(r["items"], 1):
                    title = item.get("title", "").strip() if isinstance(item, dict) else str(item).strip()
                    if not title:
                        continue
                    news_list.append({
                        "id": f"{r['source']}_{item.get('id', i) if isinstance(item, dict) else i}",
                        "title": title,
                        "url": item.get("url", "") if isinstance(item, dict) else "",
                        "source": r["source"],
                        "source_name": r["source_name"],
                        "rank": i,
                    })
                    total_items += 1
            else:
                logger.warning(f"[NewsCollector] {r['source_name']}: {r.get('error', r['status'])}")

        logger.info(f"[NewsCollector] 采集完成: {success_count}/{len(sources)} 源成功, 共 {total_items} 条新闻")

        return {
            "success": success_count > 0,
            "news_list": news_list,
            "stats": {
                "total_sources": len(sources),
                "success_sources": success_count,
                "total_news": total_items,
                "collected_at": datetime.now().isoformat(),
            },
        }

    def collect_news_sync(self, sources: Optional[List[str]] = None, campus_priority: bool = True) -> Dict:
        """同步版本（方便 FastAPI 非 async 端点调用）"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, self.collect_news(sources, campus_priority)).result()
            return asyncio.run(self.collect_news(sources, campus_priority))
        except RuntimeError:
            return asyncio.run(self.collect_news(sources, campus_priority))

    @staticmethod
    def get_available_sources() -> List[Dict]:
        """获取所有支持的新闻源"""
        return [
            {"id": k, "name": v["name"], "category": v["category"]}
            for k, v in SOURCE_CONFIG.items()
        ]
