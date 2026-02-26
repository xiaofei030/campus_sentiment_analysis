# src/crawler/deep_crawler.py
"""
深度数据采集器 - 基于 MediaCrawler 的多平台关键词搜索爬取
吸收自 BettaFish MindSpider/DeepSentimentCrawling 架构

支持平台: wb(微博), zhihu(知乎), xhs(小红书), dy(抖音),
         ks(快手), bili(B站), tieba(贴吧)
"""
import sys
import os
import json
import subprocess
import glob as globmod
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

MEDIACRAWLER_DIR = Path(__file__).parent / "MediaCrawler"

SUPPORTED_PLATFORMS = {
    "wb":    "微博",
    "zhihu": "知乎",
    "xhs":   "小红书",
    "dy":    "抖音",
    "ks":    "快手",
    "bili":  "B站",
    "tieba": "贴吧",
}

PLATFORM_TO_DATASOURCE = {
    "wb":    "WEIBO",
    "zhihu": "FORUM",
    "xhs":   "OTHER",
    "dy":    "OTHER",
    "ks":    "OTHER",
    "bili":  "OTHER",
    "tieba": "FORUM",
}

# 平台代码 → MediaCrawler 实际使用的 data/ 子目录名
# MediaCrawler 的 AsyncFileWriter 用的是完整名称，不是代码缩写
PLATFORM_TO_DATA_DIR = {
    "wb":    "weibo",
    "dy":    "douyin",
    "ks":    "kuaishou",
    # 以下平台代码和目录名一致，不需要映射
}


class DeepCrawler:
    """
    深度爬虫管理器

    通过配置并调用 MediaCrawler 子进程，在各平台按关键词搜索内容。
    爬取结果以 JSON 存储后，由本模块读取并返回结构化数据，
    可直接对接 CrawlerPipeline 进行情感分析 + 入库。
    """

    def __init__(self):
        if not MEDIACRAWLER_DIR.exists():
            raise FileNotFoundError(
                f"MediaCrawler 目录不存在: {MEDIACRAWLER_DIR}\n"
                "请先运行: git clone https://github.com/NanmiCoder/MediaCrawler "
                f'"{MEDIACRAWLER_DIR}"'
            )
        self.crawl_stats: Dict[str, Dict] = {}

    # ───── 配置写入 ─────

    # 需要动态覆盖的配置项及其新值模板
    # key → (变量名前缀, 格式化函数)
    _CONFIG_OVERRIDES = {
        "PLATFORM":            lambda p, **_: f'PLATFORM = "{p["platform"]}"',
        "KEYWORDS":            lambda p, **_: f'KEYWORDS = "{p["keywords_str"]}"',
        "CRAWLER_TYPE":        lambda **_: 'CRAWLER_TYPE = "search"  # search | detail | creator',
        "SAVE_DATA_OPTION":    lambda **_: 'SAVE_DATA_OPTION = "json"',
        "CRAWLER_MAX_NOTES_COUNT": lambda p, **_: f'CRAWLER_MAX_NOTES_COUNT = {p["max_notes"]}',
        "ENABLE_GET_COMMENTS": lambda p, **_: f'ENABLE_GET_COMMENTS = {p["enable_comments"]}',
        "CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES": lambda **_: "CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 20",
        "HEADLESS":            lambda p, **_: f'HEADLESS = {p["headless"]}',
        "CDP_HEADLESS":        lambda p, **_: f'CDP_HEADLESS = {p["headless"]}',
        "ENABLE_CDP_MODE":     lambda **_: "ENABLE_CDP_MODE = True",
    }

    @staticmethod
    def _write_base_config(
        platform: str,
        keywords: List[str],
        max_notes: int = 20,
        enable_comments: bool = True,
        headless: bool = True,
    ):
        """
        动态生成 MediaCrawler 的 base_config.py

        安全地处理多行赋值（如 ``VAR = (\\n  value\\n)``），
        避免只替换首行而遗留尾行导致 SyntaxError。
        """
        cfg_path = MEDIACRAWLER_DIR / "config" / "base_config.py"
        original = cfg_path.read_text(encoding="utf-8")

        params = {
            "platform": platform,
            "keywords_str": ",".join(keywords),
            "max_notes": max_notes,
            "enable_comments": enable_comments,
            "headless": headless,
        }

        lines = original.split("\n")
        new_lines: List[str] = []
        skip_continuation = False

        for line in lines:
            # 如果正在跳过多行赋值的后续行（括号内部 / 闭合括号）
            if skip_continuation:
                stripped = line.strip()
                # 遇到闭合括号表示多行赋值结束
                if stripped == ")" or stripped.startswith(")"):
                    skip_continuation = False
                continue

            code_part = line.split("#")[0].strip()

            matched = False
            for var_name, formatter in DeepCrawler._CONFIG_OVERRIDES.items():
                if code_part.startswith(f"{var_name} =") or code_part.startswith(f"{var_name}="):
                    new_lines.append(formatter(p=params))
                    matched = True
                    # 检测值是否以 '(' 开头但未在本行闭合 → 多行赋值
                    assign_value = code_part.split("=", 1)[1].strip() if "=" in code_part else ""
                    if assign_value.startswith("(") and ")" not in assign_value:
                        skip_continuation = True
                    break

            if not matched:
                new_lines.append(line)

        cfg_path.write_text("\n".join(new_lines), encoding="utf-8")
        logger.info(
            f"[DeepCrawler] base_config 已配置: platform={platform}, "
            f"keywords={len(keywords)}个, max_notes={max_notes}, headless={headless}"
        )

    # ───── 运行爬虫 ─────

    def run_crawler(
        self,
        platform: str,
        keywords: List[str],
        max_notes: int = 20,
        enable_comments: bool = True,
        headless: bool = True,
        timeout: int = 3600,
    ) -> Dict:
        """
        在指定平台上按关键词搜索爬取

        Args:
            platform: 平台代码 (wb/zhihu/xhs/dy/ks/bili/tieba)
            keywords: 搜索关键词列表
            max_notes: 每次搜索的最大内容数
            enable_comments: 是否爬取评论
            headless: 是否无头模式（首次登录建议 False 以便扫码）
            timeout: 超时秒数

        Returns:
            {"success": bool, "platform": str, "items": [...], ...}
        """
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"不支持的平台: {platform}，"
                f"可选: {', '.join(SUPPORTED_PLATFORMS.keys())}"
            )
        if not keywords:
            raise ValueError("关键词列表不能为空")

        logger.info(
            f"[DeepCrawler] 开始爬取 {SUPPORTED_PLATFORMS[platform]}，"
            f"关键词: {keywords[:5]}{'...' if len(keywords) > 5 else ''}"
        )

        start_time = datetime.now()

        self._write_base_config(
            platform, keywords, max_notes, enable_comments, headless
        )

        cmd = [
            sys.executable, "main.py",
            "--platform", platform,
            "--lt", "qrcode",
            "--type", "search",
            "--save_data_option", "json",
            "--keywords", ",".join(keywords),
            "--headless", str(headless),
            "--get_comment", str(enable_comments),
        ]

        # Windows: CREATE_NEW_PROCESS_GROUP 防止父进程的 Ctrl+C / 重载信号传播到子进程
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            logger.info(f"[DeepCrawler] 启动子进程: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=str(MEDIACRAWLER_DIR),
                timeout=timeout,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creation_flags,
            )

            duration = (datetime.now() - start_time).total_seconds()

            if result.stdout:
                logger.info(f"[DeepCrawler] {platform} stdout:\n{result.stdout[-2000:]}")
            if result.stderr:
                logger.warning(f"[DeepCrawler] {platform} stderr:\n{result.stderr[-2000:]}")

            items = self._collect_json_results(platform)

            stats = {
                "success": result.returncode == 0,
                "platform": platform,
                "platform_name": SUPPORTED_PLATFORMS[platform],
                "keywords_count": len(keywords),
                "items_count": len(items),
                "items": items,
                "duration_seconds": round(duration, 1),
                "return_code": result.returncode,
                "started_at": start_time.isoformat(),
            }

            if result.returncode != 0:
                stats["stderr_tail"] = (result.stderr or "")[-1000:]
                stats["stdout_tail"] = (result.stdout or "")[-1000:]
                logger.error(
                    f"[DeepCrawler] {platform} 爬取失败 (code={result.returncode})"
                )
            else:
                logger.info(
                    f"[DeepCrawler] {platform} 爬取完成: "
                    f"{len(items)} 条内容, 耗时 {duration:.1f}s"
                )

            self.crawl_stats[platform] = stats
            return stats

        except subprocess.TimeoutExpired:
            logger.error(f"[DeepCrawler] {platform} 爬取超时 ({timeout}s)")
            return {
                "success": False,
                "platform": platform,
                "error": f"爬取超时 ({timeout}s)",
                "items": [],
            }
        except Exception as e:
            logger.error(f"[DeepCrawler] {platform} 爬取异常: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e),
                "items": [],
            }

    def _collect_json_results(self, platform: str) -> List[Dict]:
        """读取 MediaCrawler 的 JSON 输出文件"""
        # MediaCrawler 的 data 目录名与平台代码不同：wb→weibo, dy→douyin, ks→kuaishou
        data_dir_name = PLATFORM_TO_DATA_DIR.get(platform, platform)
        json_dir = MEDIACRAWLER_DIR / "data" / data_dir_name / "json"

        if not json_dir.exists():
            logger.warning(
                f"[DeepCrawler] JSON 目录不存在: {json_dir}，"
                f"尝试备选目录 data/{platform}/json"
            )
            json_dir = MEDIACRAWLER_DIR / "data" / platform / "json"
            if not json_dir.exists():
                return []

        today_str = datetime.now().strftime("%Y-%m-%d")
        items = []

        for pattern in [f"search_contents_{today_str}.json", f"*contents*{today_str}*.json"]:
            for fpath in json_dir.glob(pattern):
                try:
                    raw = json.loads(fpath.read_text(encoding="utf-8"))
                    if isinstance(raw, list):
                        items.extend(raw)
                    elif isinstance(raw, dict):
                        items.append(raw)
                    logger.info(f"[DeepCrawler] 读取 {fpath.name}: {len(raw) if isinstance(raw, list) else 1} 条")
                except Exception as e:
                    logger.warning(f"[DeepCrawler] 读取 {fpath.name} 失败: {e}")

        if not items:
            logger.warning(
                f"[DeepCrawler] 在 {json_dir} 中未找到今日({today_str})的数据文件，"
                f"目录下现有文件: {[f.name for f in json_dir.glob('*.json')]}"
            )

        seen_ids = set()
        unique = []
        for item in items:
            item_id = item.get("note_id") or item.get("aweme_id") or item.get("id") or id(item)
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                unique.append(item)

        return unique

    # ───── 多平台爬取 ─────

    def run_multi_platform(
        self,
        keywords: List[str],
        platforms: Optional[List[str]] = None,
        max_notes: int = 20,
        enable_comments: bool = True,
        headless: bool = True,
    ) -> Dict:
        """
        在多个平台上搜索爬取

        Returns:
            {"total_items": int, "platform_results": {...}, ...}
        """
        if platforms is None:
            platforms = ["wb", "zhihu"]

        all_items = []
        platform_results = {}

        for plat in platforms:
            if plat not in SUPPORTED_PLATFORMS:
                logger.warning(f"[DeepCrawler] 跳过不支持的平台: {plat}")
                continue
            result = self.run_crawler(
                plat, keywords, max_notes, enable_comments, headless
            )
            platform_results[plat] = result
            if result.get("success"):
                all_items.extend(result.get("items", []))

        return {
            "success": any(r.get("success") for r in platform_results.values()),
            "total_items": len(all_items),
            "all_items": all_items,
            "platform_results": platform_results,
            "platforms_count": len(platforms),
            "keywords_count": len(keywords),
        }

    # ───── 结果转换：MediaCrawler JSON → 统一格式 ─────

    @staticmethod
    def normalize_items(items: List[Dict], platform: str) -> List[Dict]:
        """
        将各平台的原始 JSON 统一为入库格式

        Returns:
            [{"title": str, "content": str, "source": str, "url": str, ...}, ...]
        """
        normalized = []
        for item in items:
            content = (
                item.get("content")
                or item.get("desc")
                or item.get("title")
                or ""
            ).strip()
            if not content or len(content) < 2:
                continue

            note_id = str(
                item.get("note_id")
                or item.get("aweme_id")
                or item.get("video_id")
                or item.get("id")
                or ""
            )
            url = (
                item.get("note_url")
                or item.get("video_url")
                or item.get("url")
                or ""
            )
            nickname = item.get("nickname") or item.get("user_name") or ""
            create_time = item.get("create_date_time") or item.get("create_time") or ""

            normalized.append({
                "id": f"{platform}_{note_id}",
                "title": content[:100],
                "content": content,
                "source": platform,
                "source_name": SUPPORTED_PLATFORMS.get(platform, platform),
                "url": url,
                "author": nickname,
                "liked_count": item.get("liked_count", "0"),
                "comments_count": item.get("comments_count", "0"),
                "shared_count": item.get("shared_count", "0"),
                "create_time": create_time,
                "source_keyword": item.get("source_keyword", ""),
            })

        return normalized

    def get_stats(self) -> Dict:
        return {
            "platforms_crawled": list(self.crawl_stats.keys()),
            "stats": self.crawl_stats,
        }
