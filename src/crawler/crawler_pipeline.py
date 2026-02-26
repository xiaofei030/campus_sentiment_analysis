# src/crawler/crawler_pipeline.py
"""
数据采集管道 - 吸收自 BettaFish MindSpider 的两阶段架构
阶段1: 热点新闻采集 → AI话题提取 → 生成关键词
阶段2: 真实数据 → 情感分析 → 风险评估 → 入库
阶段2b: 自定义关键词 → 多平台深度搜索爬取 → 情感分析 → 入库

本模块还提供将采集数据导入校园舆情 MySQL 数据库的能力
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import logging

from src.crawler.news_collector import NewsCollector, SOURCE_CONFIG, CAMPUS_PRIORITY_SOURCES
from src.crawler.topic_extractor import TopicExtractor

logger = logging.getLogger(__name__)

DEFAULT_CAMPUS_KEYWORDS = [
    "XX大学 食堂", "XX大学 宿舍", "XX大学 考试",
    "XX大学 选课", "XX大学 就业", "XX大学 图书馆",
    "XX大学 奖学金", "XX大学 实习", "XX大学 教务",
    "XX大学 社团", "XX大学 军训", "XX大学 考研",
    "XX大学 食堂", "XX大学 宿舍", "XX大学 考试",
]


class CrawlerPipeline:
    """
    数据采集管道

    架构吸收自 BettaFish MindSpider：
    - BroadTopicExtraction: 热点发现 → 关键词生成
    - DeepSentimentCrawling: 关键词 → 多平台爬取（简化版）
    """

    def __init__(self):
        self.news_collector = NewsCollector()
        self.topic_extractor = TopicExtractor()

    # ─────── 阶段1: 热点发现 ───────

    async def run_topic_extraction(
        self,
        news_sources: Optional[List[str]] = None,
        max_keywords: int = 60,
    ) -> Dict:
        """
        运行话题提取流程
        1. 采集热点新闻
        2. AI 提取关键词与总结
        3. 返回结构化结果（含原始 news_list 供后续入库）
        """
        logger.info("[Pipeline] === 阶段1: 热点话题发现 ===")
        start = datetime.now()

        news_result = await self.news_collector.collect_news(sources=news_sources)
        if not news_result["success"] or not news_result["news_list"]:
            return {
                "success": False,
                "error": "新闻采集失败或无数据",
                "news_stats": news_result.get("stats"),
                "_news_list": [],
            }

        keywords, summary = self.topic_extractor.extract_keywords_and_summary(
            news_result["news_list"], max_keywords
        )
        search_keywords = self.topic_extractor.get_search_keywords(keywords, limit=15)

        duration = (datetime.now() - start).total_seconds()

        result = {
            "success": len(keywords) > 0,
            "keywords": keywords,
            "search_keywords": search_keywords,
            "summary": summary,
            "news_stats": news_result["stats"],
            "duration_seconds": round(duration, 1),
            "extracted_at": datetime.now().isoformat(),
            "_news_list": news_result["news_list"],
        }

        logger.info(
            f"[Pipeline] 话题提取完成: {len(keywords)} 关键词, "
            f"{len(search_keywords)} 搜索词, 耗时 {duration:.1f}s"
        )
        return result

    def run_topic_extraction_sync(self, **kwargs) -> Dict:
        """同步版本"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, self.run_topic_extraction(**kwargs)).result()
            return asyncio.run(self.run_topic_extraction(**kwargs))
        except RuntimeError:
            return asyncio.run(self.run_topic_extraction(**kwargs))

    # ─────── 校园相关性过滤 ───────

    # 只要标题包含以下任意关键词，就认为与校园舆情相关
    # >>> 你可以在这里增删关键词来控制采集范围 <<<
    CAMPUS_FILTER_KEYWORDS = ["XX大学", "XX大", "某市", "某省"
        # 学校 / 高校
        # "大学", "高校", "学院", "校园", "学校", "师生",
        # # 学生身份
        # "大学生", "学生", "研究生", "本科", "硕士", "博士", "毕业生",
        # "新生", "学弟", "学妹", "学长", "学姐", "00后",
        # # 学业
        # "考研", "保研", "考公", "考编", "四六级", "期末", "挂科",
        # "绩点", "论文", "答辩", "毕设", "毕业", "学位", "考试",
        # "高考", "分数线", "录取", "招生", "推免", "调剂", "复试",
        # # 就业
        # "就业", "秋招", "春招", "实习", "offer", "校招", "求职",
        # "应届", "签约", "三方", "裁员",
        # # 校园生活
        # "宿舍", "食堂", "图书馆", "社团", "室友", "辅导员", "导师",
        # "奖学金", "助学金", "学费", "军训", "开学", "返校",
        # # 心理 / 安全
        # "心理健康", "抑郁", "焦虑", "压力", "校园暴力", "霸凌",
        # "跳楼", "轻生", "心理咨询",
        # # 教育政策
        # "教育", "教育部", "双一流", "学科", "教学", "课程",
    ]

    @classmethod
    def is_campus_related(cls, title: str) -> bool:
        """判断标题是否与校园舆情相关"""
        for kw in cls.CAMPUS_FILTER_KEYWORDS:
            if kw in title:
                return True
        return False

    # ─────── 阶段2: 真实数据导入 ───────

    def import_news_to_database(self, news_list: List[Dict], keywords: List[str] = None) -> Dict:
        """
        将采集到的真实新闻数据导入 MySQL：
        1. 用校园关键词过滤，只保留与校园相关的真实条目
        2. 对真实内容执行情感分析和风险评估
        3. 原始内容原样入库，不做任何篡改
        """
        from src.database.connection import SessionLocal
        from src.database.models import (
            SentimentRecord, DataSource, SentimentType, RiskLevel, Alert, AlertStatus
        )
        from src.sentiment.fast_analyzer import analyze_text

        session = SessionLocal()
        imported = 0
        skipped = 0
        alerts_created = 0

        SOURCE_MAP = {
            "weibo": DataSource.WEIBO,
            "zhihu": DataSource.FORUM,
            "bilibili-hot-search": DataSource.OTHER,
            "toutiao": DataSource.OTHER,
            "douyin": DataSource.OTHER,
            "tieba": DataSource.FORUM,
            "coolapk": DataSource.OTHER,
            "thepaper": DataSource.OTHER,
        }

        SENTIMENT_MAP = {
            "positive": SentimentType.POSITIVE,
            "negative": SentimentType.NEGATIVE,
            "neutral": SentimentType.NEUTRAL,
        }
        RISK_MAP = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }

        try:
            for item in news_list:
                title = item.get("title", "").strip()
                if not title or len(title) < 4:
                    continue

                if not self.is_campus_related(title):
                    skipped += 1
                    continue

                source_id = item.get("source", "other")
                db_source = SOURCE_MAP.get(source_id, DataSource.OTHER)

                analysis = analyze_text(title)
                detected_topic = analysis["main_topic"]
                if keywords and (not detected_topic or detected_topic in ("其他",)):
                    detected_topic = keywords[0]

                record = SentimentRecord(
                    content=title,
                    source=db_source,
                    author_id=item.get("id", ""),
                    sentiment=SENTIMENT_MAP.get(analysis["sentiment"], SentimentType.NEUTRAL),
                    emotions=analysis["emotions"],
                    sentiment_confidence=analysis["sentiment_confidence"],
                    main_topic=detected_topic,
                    keywords=keywords[:5] if keywords else None,
                    risk_level=RISK_MAP.get(analysis["risk_level"], RiskLevel.LOW),
                    risk_indicators=analysis["risk_indicators"],
                    risk_confidence=analysis["risk_confidence"],
                    suggested_actions=analysis["suggested_actions"],
                    created_at=datetime.now(),
                    analyzed_at=datetime.now(),
                )
                session.add(record)
                session.flush()
                imported += 1

                if analysis["risk_level"] in ("high", "critical"):
                    alert = Alert(
                        record_id=record.id,
                        alert_type="risk",
                        risk_level=RISK_MAP[analysis["risk_level"]],
                        status=AlertStatus.ACTIVE,
                        title=f"[{analysis['risk_level'].upper()}] {title[:50]}",
                        description=f"风险指标: {', '.join(analysis['risk_indicators'])}",
                        ai_suggestion="; ".join(analysis["suggested_actions"]),
                    )
                    session.add(alert)
                    alerts_created += 1

            session.commit()
            logger.info(
                f"[Pipeline] 校园相关 {imported} 条已导入, "
                f"过滤掉无关数据 {skipped} 条, 创建预警 {alerts_created} 条"
            )
            return {
                "success": True,
                "imported": imported,
                "skipped_not_campus": skipped,
                "alerts_created": alerts_created,
            }
        except Exception as e:
            session.rollback()
            logger.error(f"[Pipeline] 数据导入失败: {e}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    # ─────── 阶段2b: 自定义关键词深度搜索爬取 ───────

    def run_keyword_crawling(
        self,
        keywords: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        max_notes: int = 20,
        enable_comments: bool = True,
        headless: bool = True,
        import_to_db: bool = True,
    ) -> Dict:
        """
        跳过热点提取，直接用自定义校园关键词在多平台上搜索爬取。
        爬取结果自动做情感分析并导入数据库。

        Args:
            keywords: 搜索关键词列表，为 None 则使用默认校园关键词
            platforms: 目标平台列表，为 None 则默认 ["wb", "zhihu"]
            max_notes: 每个平台的最大爬取内容数
            enable_comments: 是否爬取评论
            headless: 是否无头模式（首次登录建议 False）
            import_to_db: 是否将爬取内容做情感分析后入库

        Returns:
            {"success": bool, "crawl_result": {...}, "import_result": {...}}
        """
        from src.crawler.deep_crawler import DeepCrawler

        if keywords is None:
            keywords = DEFAULT_CAMPUS_KEYWORDS
        if platforms is None:
            platforms = ["wb", "zhihu"]

        logger.info(
            f"[Pipeline] === 自定义关键词深度爬取 ===\n"
            f"  关键词: {keywords[:5]}{'...' if len(keywords) > 5 else ''}\n"
            f"  平台: {platforms}"
        )

        crawler = DeepCrawler()
        crawl_result = crawler.run_multi_platform(
            keywords=keywords,
            platforms=platforms,
            max_notes=max_notes,
            enable_comments=enable_comments,
            headless=headless,
        )

        import_result = None
        if import_to_db and crawl_result.get("all_items"):
            all_normalized = []
            for plat, plat_result in crawl_result.get("platform_results", {}).items():
                raw_items = plat_result.get("items", [])
                normalized = DeepCrawler.normalize_items(raw_items, plat)
                all_normalized.extend(normalized)

            if all_normalized:
                import_result = self._import_deep_crawl_to_database(
                    all_normalized, keywords
                )

        return {
            "success": crawl_result.get("success", False),
            "crawl_result": {
                k: v for k, v in crawl_result.items() if k != "all_items"
            },
            "import_result": import_result,
            "keywords_used": keywords,
            "platforms_used": platforms,
        }

    def _import_deep_crawl_to_database(
        self, items: List[Dict], keywords: List[str]
    ) -> Dict:
        """
        将深度爬取的结构化数据导入 MySQL
        每条记录做情感分析 + 风险评估后入库
        """
        from src.database.connection import SessionLocal
        from src.database.models import (
            SentimentRecord, DataSource, SentimentType, RiskLevel,
            Alert, AlertStatus,
        )
        from src.sentiment.fast_analyzer import analyze_text
        from src.crawler.deep_crawler import PLATFORM_TO_DATASOURCE

        SOURCE_MAP = {
            "WEIBO": DataSource.WEIBO,
            "FORUM": DataSource.FORUM,
            "OTHER": DataSource.OTHER,
        }
        SENTIMENT_MAP = {
            "positive": SentimentType.POSITIVE,
            "negative": SentimentType.NEGATIVE,
            "neutral": SentimentType.NEUTRAL,
        }
        RISK_MAP = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }

        session = SessionLocal()
        imported = 0
        alerts_created = 0

        try:
            for item in items:
                content = item.get("content", "").strip()
                if not content or len(content) < 4:
                    continue

                plat_code = item.get("source", "other")
                ds_key = PLATFORM_TO_DATASOURCE.get(plat_code, "OTHER")
                db_source = SOURCE_MAP.get(ds_key, DataSource.OTHER)

                analysis = analyze_text(content)
                detected_topic = analysis["main_topic"]
                if not detected_topic or detected_topic in ("其他",):
                    kw = item.get("source_keyword") or (keywords[0] if keywords else "")
                    detected_topic = kw

                record = SentimentRecord(
                    content=content[:500],
                    source=db_source,
                    author_id=item.get("id", ""),
                    sentiment=SENTIMENT_MAP.get(
                        analysis["sentiment"], SentimentType.NEUTRAL
                    ),
                    emotions=analysis["emotions"],
                    sentiment_confidence=analysis["sentiment_confidence"],
                    main_topic=detected_topic,
                    keywords=keywords[:5] if keywords else None,
                    risk_level=RISK_MAP.get(
                        analysis["risk_level"], RiskLevel.LOW
                    ),
                    risk_indicators=analysis["risk_indicators"],
                    risk_confidence=analysis["risk_confidence"],
                    suggested_actions=analysis["suggested_actions"],
                    created_at=datetime.now(),
                    analyzed_at=datetime.now(),
                )
                session.add(record)
                session.flush()
                imported += 1

                if analysis["risk_level"] in ("high", "critical"):
                    alert = Alert(
                        record_id=record.id,
                        alert_type="risk",
                        risk_level=RISK_MAP[analysis["risk_level"]],
                        status=AlertStatus.ACTIVE,
                        title=f"[{analysis['risk_level'].upper()}] {content[:50]}",
                        description=(
                            f"风险指标: {', '.join(analysis['risk_indicators'])}"
                        ),
                        ai_suggestion="; ".join(analysis["suggested_actions"]),
                    )
                    session.add(alert)
                    alerts_created += 1

            session.commit()
            logger.info(
                f"[Pipeline] 深度爬取导入完成: {imported} 条, "
                f"预警 {alerts_created} 条"
            )
            return {
                "success": True,
                "imported": imported,
                "alerts_created": alerts_created,
            }
        except Exception as e:
            session.rollback()
            logger.error(f"[Pipeline] 深度爬取导入失败: {e}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    # ─────── 补充分析已入库但未分析的记录 ───────

    def analyze_pending_records(self, batch_size: int = 500) -> Dict:
        """
        扫描数据库中 sentiment 为 NULL 的记录，对原始内容补充情感/风险分析。
        不修改原始内容，只填充分析结果字段。
        """
        from src.database.connection import SessionLocal
        from src.database.models import (
            SentimentRecord, SentimentType, RiskLevel, Alert, AlertStatus
        )
        from src.sentiment.fast_analyzer import analyze_text

        session = SessionLocal()
        SENTIMENT_MAP = {
            "positive": SentimentType.POSITIVE,
            "negative": SentimentType.NEGATIVE,
            "neutral": SentimentType.NEUTRAL,
        }
        RISK_MAP = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }

        try:
            pending = (
                session.query(SentimentRecord)
                .filter(SentimentRecord.sentiment.is_(None))
                .limit(batch_size)
                .all()
            )

            if not pending:
                return {"success": True, "analyzed": 0, "message": "没有待分析的记录"}

            analyzed = 0
            alerts_created = 0
            for record in pending:
                analysis = analyze_text(record.content or "")

                record.sentiment = SENTIMENT_MAP.get(analysis["sentiment"], SentimentType.NEUTRAL)
                record.emotions = analysis["emotions"]
                record.sentiment_confidence = analysis["sentiment_confidence"]
                record.risk_level = RISK_MAP.get(analysis["risk_level"], RiskLevel.LOW)
                record.risk_indicators = analysis["risk_indicators"]
                record.risk_confidence = analysis["risk_confidence"]
                record.suggested_actions = analysis["suggested_actions"]
                record.analyzed_at = datetime.now()

                if not record.main_topic:
                    record.main_topic = analysis["main_topic"]

                if analysis["risk_level"] in ("high", "critical"):
                    alert = Alert(
                        record_id=record.id,
                        alert_type="risk",
                        risk_level=RISK_MAP[analysis["risk_level"]],
                        status=AlertStatus.ACTIVE,
                        title=f"[{analysis['risk_level'].upper()}] {(record.content or '')[:50]}",
                        description=f"风险指标: {', '.join(analysis['risk_indicators'])}",
                        ai_suggestion="; ".join(analysis["suggested_actions"]),
                    )
                    session.add(alert)
                    alerts_created += 1

                analyzed += 1

            session.commit()
            logger.info(f"[Pipeline] 补充分析 {analyzed} 条记录, 创建 {alerts_created} 条预警")
            return {"success": True, "analyzed": analyzed, "alerts_created": alerts_created}
        except Exception as e:
            session.rollback()
            logger.error(f"[Pipeline] 补充分析失败: {e}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    # ─────── 完整流程 ───────

    async def run_full_pipeline(
        self,
        news_sources: Optional[List[str]] = None,
        max_keywords: int = 60,
        import_to_db: bool = False,
    ) -> Dict:
        """
        运行完整的数据采集管道
        1. 采集热点新闻（只采集一次）
        2. AI 话题提取
        3. (可选) 导入数据库（复用同一批新闻数据）
        """
        extract_result = await self.run_topic_extraction(news_sources, max_keywords)

        if not extract_result["success"]:
            return extract_result

        import_result = None
        if import_to_db:
            news_list = extract_result.pop("_news_list", [])
            if news_list:
                import_result = self.import_news_to_database(
                    news_list,
                    extract_result.get("search_keywords"),
                )
            else:
                import_result = {"success": False, "error": "无可导入的新闻数据"}
        else:
            extract_result.pop("_news_list", None)

        extract_result["import_result"] = import_result
        return extract_result

    # ─────── 状态查询 ───────

    def get_status(self) -> Dict:
        """获取采集器状态"""
        from src.crawler.deep_crawler import SUPPORTED_PLATFORMS, MEDIACRAWLER_DIR

        deep_available = MEDIACRAWLER_DIR.exists()

        return {
            "available": True,
            "news_sources": len(SOURCE_CONFIG),
            "priority_sources": CAMPUS_PRIORITY_SOURCES,
            "supported_sources": NewsCollector.get_available_sources(),
            "campus_filter_keywords": self.CAMPUS_FILTER_KEYWORDS,
            "deep_crawl_available": deep_available,
            "deep_crawl_platforms": (
                list(SUPPORTED_PLATFORMS.keys()) if deep_available else []
            ),
            "default_campus_keywords": DEFAULT_CAMPUS_KEYWORDS,
            "capabilities": [
                "热点新闻实时采集 (12+ 平台)",
                "校园相关性关键词过滤（只入库与校园相关的真实数据）",
                "AI 话题提取与关键词生成",
                "快速情感/风险分析",
                "数据库批量导入",
                "自定义关键词多平台深度搜索爬取 (wb/zhihu/xhs/dy/ks/bili/tieba)",
            ],
        }
