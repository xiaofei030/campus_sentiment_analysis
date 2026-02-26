# scripts/generate_data.py
"""
生成 1.5 万条高仿真校园情感数据并写入 MySQL
数据覆盖多种场景：学业压力、人际关系、就业焦虑、生活适应、心理健康等

用法：
    python scripts/generate_data.py
"""
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import random
from datetime import datetime, timedelta
from tqdm import tqdm

from src.database.connection import engine, SessionLocal, init_db
from src.database.models import (
    SentimentRecord, ReviewTask, Alert, User, AnalysisStats,
    SentimentType, RiskLevel, ReviewStatus, AlertStatus, DataSource
)

# ========== 高仿真文本模板 ==========

# 按话题分类的文本模板池
TEXT_TEMPLATES = {
    "学业压力": {
        "positive": [
            "今天终于把高数的期末复习搞完了，感觉这学期收获很大！",
            "拿到了奖学金，大三的努力总算没白费，继续加油！",
            "实验报告终于通过了导师的审核，开心死了！",
            "编程课的大作业拿了满分，果然熬夜debug是值得的",
            "保研名额确定了，终于可以松一口气了",
            "今天课设答辩顺利通过，感谢组员们的配合",
            "论文初稿写完了，虽然还要改但是很有成就感",
            "这学期GPA提高了0.5，进步很大",
            "参加了学术竞赛拿了二等奖，挺满意的",
            "选的这门选修课太有意思了，老师讲得特别好",
        ],
        "negative": [
            "期末考试一门接一门，真的要崩溃了，什么都来不及复习",
            "挂科了两门，绩点直接掉到3.0以下，好焦虑啊",
            "毕业论文开题报告被导师打回来三次了，太难了",
            "高数完全听不懂，感觉自己不适合学这个专业",
            "考研二战压力好大，每天图书馆坐到闭馆也看不进去",
            "实验数据一直跑不出来，deadline就在下周了",
            "分数出来了比预期低太多，不知道该怎么办",
            "课程设计完全不会做，找不到人请教，好绝望",
            "转专业没成功，接下来四年要学不喜欢的东西了",
            "四级又没过，都第三次了，太丢人了",
            "连续三天通宵赶作业，身体和精神都快撑不住了",
            "实习和课程冲突了，两边都要顾，真的好累",
        ],
        "neutral": [
            "明天有两节高数课，得提前预习一下",
            "图书馆今天人好多，找了半天才有位置",
            "下周开始期末考试了，要制定复习计划了",
            "选课系统又崩了，刷了半天没选上想要的课",
            "今天上了一天课，晚上还有实验报告要写",
        ],
    },
    "人际关系": {
        "positive": [
            "和室友一起去吃了火锅，聊了好多心里话，感觉关系更好了",
            "参加社团活动认识了好多有趣的朋友，大学生活真丰富",
            "男/女朋友今天给我准备了惊喜，好感动",
            "和好久不见的高中同学视频了，聊得特别开心",
            "班级秋游大家玩得很嗨，集体活动还是很有意义的",
            "导师今天夸我了，说我最近进步很大，超开心",
            "寝室关系特别和谐，每天回宿舍都很放松",
        ],
        "negative": [
            "室友天天打游戏到半夜，吵得我根本睡不着，沟通了也没用",
            "和最好的朋友吵架了，感觉心里很难受",
            "一个人吃饭一个人上课，感觉大学里一个真朋友都没有",
            "被室友孤立了，不知道自己做错了什么",
            "恋爱分手了，整个人都很低落，什么都不想做",
            "感觉自己在班级里透明人一样，没有存在感",
            "和家里人因为选专业的事大吵了一架，好心烦",
            "社交恐惧越来越严重了，不敢和陌生人说话",
            "寝室矛盾太大了，每天回去都很压抑",
        ],
        "neutral": [
            "今天和同学一起去了自习室，各学各的",
            "班级群里在讨论下周的班会安排",
            "参加了学生会的例会，讨论了新学期的活动计划",
            "和导师约了下周三讨论论文进度",
        ],
    },
    "就业焦虑": {
        "positive": [
            "秋招拿到了心仪公司的offer，太激动了！",
            "面试表现不错，HR说很快会给结果，期待",
            "实习公司想留我转正，感觉这段经历很值",
            "考公笔试成绩出来了，进面了！好开心",
            "简历投了一周终于有回复了，约了面试",
        ],
        "negative": [
            "投了几十份简历全部石沉大海，好绝望",
            "秋招季都快结束了还没有offer，同学们都签约了就我没有",
            "面试被刷了好多次，开始怀疑自己的能力了",
            "学了四年感觉什么都不会，简历都不知道怎么写",
            "家里一直催找工作，但现在就业形势真的太难了",
            "考研考公都没上岸，现在两手空空不知道怎么办",
            "实习工资太低了，在大城市根本活不下去",
            "专业对口的岗位太少了，感觉前途一片渺茫",
            "看到同龄人都找到好工作，自己还在迷茫，好焦虑",
            "HR说我经验不足，可我还是学生啊，很矛盾",
        ],
        "neutral": [
            "今天去听了一场校招宣讲会，了解了一些行业信息",
            "准备开始写简历了，先看看模板",
            "下周有三场面试，需要好好准备一下",
            "和学长聊了聊就业的情况，收获不少",
        ],
    },
    "心理健康": {
        "positive": [
            "去做了心理咨询，感觉轻松了很多，原来倾诉很重要",
            "开始每天跑步了，运动完心情真的好很多",
            "学会了冥想，最近睡眠质量改善了不少",
            "和心理老师聊了之后，觉得没那么焦虑了",
            "参加了减压活动，和大家一起做手工很治愈",
        ],
        "negative": [
            "最近总是失眠，凌晨三四点还睡不着，白天没精神",
            "什么都提不起兴趣，整天就是躺在床上发呆",
            "莫名其妙想哭，控制不住自己的情绪",
            "感觉活着没什么意思，每天都在重复一样的事",
            "焦虑到心跳加速、手发抖，不知道怎么缓解",
            "好久没出宿舍了，不想见任何人",
            "对自己越来越失望，觉得自己什么都做不好",
            "经常做噩梦，醒来之后很难再入睡",
            "情绪低落持续好几个月了，以前不是这样的",
            "有时候会不自觉地想到一些很极端的念头，害怕自己",
        ],
        "neutral": [
            "今天心情一般般，不好不坏",
            "学校的心理健康讲座还挺有用的",
            "同学推荐了一个冥想APP，打算试试",
        ],
    },
    "生活适应": {
        "positive": [
            "食堂新出了一道菜超好吃，幸福感爆棚",
            "终于把宿舍收拾整齐了，住着舒服多了",
            "周末和朋友出去逛街看电影，好久没这么放松了",
            "学会了自己做饭，虽然简单但很有成就感",
            "拿到驾照了，暑假可以自驾游了",
        ],
        "negative": [
            "北方太冷了，南方来的完全适应不了这个天气",
            "宿舍条件太差了，六人间连转身的地方都没有",
            "食堂饭菜太难吃了，每天点外卖钱都不够花",
            "离家太远了，好想家，经常一个人偷偷哭",
            "生活费不够用，又不好意思开口跟父母要",
            "水土不服一直拉肚子，好几天了都没好",
        ],
        "neutral": [
            "今天天气不错，出去走了走",
            "超市打折买了一堆零食，囤货成功",
            "给家里打了个电话，报了个平安",
            "宿舍楼下的快递终于到了",
        ],
    },
    "校园活动": {
        "positive": [
            "运动会我们班拿了第一名，太兴奋了！",
            "合唱比赛排练很辛苦，但上台的那一刻全值了",
            "志愿活动帮助了很多人，感觉自己很有价值",
            "学生会组织的晚会特别精彩，大学的青春记忆",
            "参加了创业大赛，虽然没获奖但学到了很多",
        ],
        "negative": [
            "被迫参加的活动真的很无聊，浪费时间",
            "学生会的工作压力太大了，每天都在开会",
            "社团活动和上课冲突了，很为难",
        ],
        "neutral": [
            "下周有校园歌手大赛，打算去看看",
            "报名了学校的马拉松，得开始练习了",
            "学生会在招新，在考虑要不要加入",
        ],
    },
}

# 高风险文本（需要特别关注）
HIGH_RISK_TEXTS = [
    "真的太累了，不想继续了，如果能永远睡过去就好了",
    "觉得自己是多余的，消失了也不会有人在意",
    "最近一直在想，如果从楼上跳下去会怎样",
    "已经好久没有感到快乐了，活着就是受罪",
    "割了几道口子，看到血流出来反而觉得释放了",
    "写好了遗书，觉得这样做对所有人都好",
    "不想再承受了，如果有一种药能让我不再痛苦就好了",
    "每天都在想怎么结束这一切，太痛苦了",
    "觉得世界上没有人真正关心我，活着没有意义",
    "已经计划好了，等这学期结束就离开这个世界",
]

# 情绪标签池
EMOTION_POOLS = {
    "positive": ["喜悦", "兴奋", "满足", "自豪", "感恩", "期待", "轻松", "幸福", "希望"],
    "negative": ["焦虑", "压力", "沮丧", "迷茫", "孤独", "恐惧", "愤怒", "失望", "无助", "悲伤", "自卑", "烦躁"],
    "neutral": ["平静", "一般", "无感", "淡定"],
}

# 院系列表
DEPARTMENTS = [
    "计算机科学与技术学院", "数学与信息科学学院", "经济学院", "管理学院",
    "文学与新闻传播学院", "外国语学院", "法学院", "马克思主义学院",
    "化学化工学院", "生物科学与工程学院", "电气工程学院", "土木工程学院",
    "音乐舞蹈学院", "美术学院", "体育学院", "教育学院",
    "医学院", "预科教育学院",
]

GRADES = ["大一", "大二", "大三", "大四", "研一", "研二", "研三"]

SOURCES = list(DataSource)


def random_date(start_days_ago=365, end_days_ago=0):
    """生成随机日期"""
    days_ago = random.randint(end_days_ago, start_days_ago)
    return datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23),
                                       minutes=random.randint(0, 59))


def generate_emotions(sentiment_type: str, count=None):
    """根据情感类型生成情绪标签"""
    pool = EMOTION_POOLS.get(sentiment_type, EMOTION_POOLS["neutral"])
    if count is None:
        count = random.randint(1, min(3, len(pool)))
    return random.sample(pool, min(count, len(pool)))


def generate_risk_indicators(risk_level: str):
    """根据风险等级生成风险信号"""
    indicators_pool = {
        "low": ["轻微压力", "一般性抱怨", "日常负面情绪"],
        "medium": ["持续焦虑", "睡眠问题", "社交回避", "食欲变化", "情绪波动"],
        "high": ["严重抑郁倾向", "自我否定", "绝望感", "长期失眠", "社交隔离", "丧失兴趣"],
        "critical": ["自伤倾向", "自杀意念", "极端想法", "告别行为", "丧失求生欲"],
    }
    pool = indicators_pool.get(risk_level, indicators_pool["low"])
    return random.sample(pool, random.randint(1, min(3, len(pool))))


def generate_actions(risk_level: str):
    """根据风险等级生成建议行动"""
    actions_pool = {
        "low": ["保持关注", "正常沟通"],
        "medium": ["主动沟通", "建议心理咨询", "密切关注动态", "联系班主任"],
        "high": ["紧急约谈", "联系家长", "安排心理咨询", "持续跟踪", "上报院系"],
        "critical": ["立即干预", "24小时陪护", "紧急联系家长", "上报学校心理危机干预中心", "拨打心理援助热线"],
    }
    pool = actions_pool.get(risk_level, actions_pool["low"])
    return random.sample(pool, random.randint(1, min(3, len(pool))))


def determine_risk_level(sentiment_type: str, topic: str) -> str:
    """根据情感和话题确定风险等级（带权重随机）"""
    if sentiment_type == "positive":
        return random.choices(
            ["low", "low", "low", "medium"],
            weights=[85, 10, 4, 1]
        )[0]
    elif sentiment_type == "neutral":
        return random.choices(
            ["low", "medium"],
            weights=[90, 10]
        )[0]
    else:  # negative
        if topic == "心理健康":
            return random.choices(
                ["low", "medium", "high", "critical"],
                weights=[10, 35, 40, 15]
            )[0]
        elif topic == "就业焦虑":
            return random.choices(
                ["low", "medium", "high", "critical"],
                weights=[20, 45, 30, 5]
            )[0]
        else:
            return random.choices(
                ["low", "medium", "high", "critical"],
                weights=[30, 45, 20, 5]
            )[0]


def generate_records(count=15000):
    """生成指定数量的高仿真数据"""
    records = []
    topics = list(TEXT_TEMPLATES.keys())

    # 情感分布比例：negative 45%, positive 30%, neutral 25%
    sentiment_weights = {
        "negative": 0.45,
        "positive": 0.30,
        "neutral": 0.25,
    }

    for i in tqdm(range(count), desc="生成数据"):
        # 选择情感倾向
        sentiment_type = random.choices(
            list(sentiment_weights.keys()),
            weights=list(sentiment_weights.values())
        )[0]

        # 选择话题
        topic = random.choice(topics)

        # 获取文本
        text_pool = TEXT_TEMPLATES[topic].get(sentiment_type, [])
        if not text_pool:
            text_pool = TEXT_TEMPLATES[topic].get("neutral", ["今天是平凡的一天"])

        content = random.choice(text_pool)

        # 添加一些随机性（附加短语）
        suffixes = {
            "positive": ["", "！", "～", " 加油！", " 感觉不错！", "，希望一直这样下去"],
            "negative": ["", "...", "。", " 唉", " 好烦", " 不知道该怎么办", "，真的好累"],
            "neutral": ["", "。", "～", " 就这样吧"],
        }
        content += random.choice(suffixes.get(sentiment_type, [""]))

        # 5% 概率使用高风险文本替换
        if sentiment_type == "negative" and random.random() < 0.05:
            content = random.choice(HIGH_RISK_TEXTS)
            risk_level = random.choice(["high", "critical"])
            topic = "心理健康"
        else:
            risk_level = determine_risk_level(sentiment_type, topic)

        # 生成时间线（过去一年）
        original_time = random_date(365, 0)
        analyzed_at = original_time + timedelta(minutes=random.randint(1, 60))

        # 确定审核状态
        if risk_level in ["high", "critical"]:
            review_status = random.choices(
                [ReviewStatus.PENDING, ReviewStatus.PROCESSING,
                 ReviewStatus.APPROVED, ReviewStatus.ESCALATED],
                weights=[30, 20, 40, 10]
            )[0]
        elif risk_level == "medium":
            review_status = random.choices(
                [ReviewStatus.PENDING, ReviewStatus.APPROVED, ReviewStatus.REJECTED],
                weights=[40, 50, 10]
            )[0]
        else:
            review_status = random.choices(
                [ReviewStatus.PENDING, ReviewStatus.APPROVED],
                weights=[20, 80]
            )[0]

        record = SentimentRecord(
            content=content,
            source=random.choice(SOURCES),
            author_id=f"STU{random.randint(2020001, 2026999):07d}",
            author_grade=random.choice(GRADES),
            author_department=random.choice(DEPARTMENTS),
            sentiment=SentimentType(sentiment_type),
            emotions=generate_emotions(sentiment_type),
            sentiment_confidence=round(random.uniform(0.65, 0.98), 2),
            main_topic=topic,
            sub_topics=random.sample(
                [t for t in topics if t != topic], k=random.randint(0, 2)
            ),
            keywords=random.sample(
                ["学业", "考试", "压力", "朋友", "室友", "就业", "焦虑",
                 "孤独", "迷茫", "开心", "感恩", "运动", "社团", "恋爱",
                 "家庭", "实习", "论文", "考研", "考公", "失眠"],
                k=random.randint(2, 5)
            ),
            risk_level=RiskLevel(risk_level),
            risk_indicators=generate_risk_indicators(risk_level),
            risk_confidence=round(random.uniform(0.60, 0.95), 2),
            suggested_actions=generate_actions(risk_level),
            review_status=review_status,
            ai_summary=f"该文本表达了{sentiment_type}情绪，主题为{topic}，"
                       f"风险等级{risk_level}。",
            original_time=original_time,
            analyzed_at=analyzed_at,
            created_at=analyzed_at + timedelta(seconds=random.randint(1, 30)),
        )
        records.append(record)

    return records


def generate_users():
    """生成管理员和辅导员账户"""
    users = [
        User(
            username="admin",
            password_hash="pbkdf2:sha256:admin123",  # 仅演示用
            real_name="系统管理员",
            role="admin",
            department="学生工作部",
            phone="13800000001",
            email="admin@campus.edu.cn",
        ),
    ]
    # 每个院系生成1-2个辅导员
    for i, dept in enumerate(DEPARTMENTS):
        for j in range(random.randint(1, 2)):
            users.append(User(
                username=f"counselor_{i}_{j}",
                password_hash=f"pbkdf2:sha256:pass{i}{j}",
                real_name=f"{dept[:2]}老师{j+1}",
                role="counselor",
                department=dept,
                phone=f"138{random.randint(10000000, 99999999)}",
                email=f"counselor_{i}_{j}@campus.edu.cn",
            ))
    return users


def generate_review_tasks(session, records):
    """为中高风险记录生成审核任务"""
    tasks = []
    # 获取辅导员列表
    counselors = session.query(User).filter(User.role == "counselor").all()
    if not counselors:
        return tasks

    for record in records:
        if record.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            priority = {"medium": 2, "high": 4, "critical": 5}.get(
                record.risk_level.value, 1
            )
            reviewer = random.choice(counselors)
            task = ReviewTask(
                record_id=record.id,
                reviewer_id=reviewer.id if record.review_status != ReviewStatus.PENDING else None,
                status=record.review_status,
                priority=priority,
                ai_risk_level=record.risk_level,
                reviewer_risk_level=(
                    record.risk_level
                    if record.review_status == ReviewStatus.APPROVED
                    else None
                ),
                review_comment=(
                    "AI判定结果准确，已确认风险等级" 
                    if record.review_status == ReviewStatus.APPROVED
                    else None
                ),
                assigned_at=(
                    record.created_at + timedelta(minutes=random.randint(5, 120))
                    if record.review_status != ReviewStatus.PENDING else None
                ),
                reviewed_at=(
                    record.created_at + timedelta(hours=random.randint(1, 48))
                    if record.review_status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]
                    else None
                ),
                created_at=record.created_at,
            )
            tasks.append(task)
    return tasks


def generate_alerts(session, records):
    """为高危记录生成预警"""
    alerts = []
    counselors = session.query(User).filter(User.role == "counselor").all()

    for record in records:
        if record.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            handler = random.choice(counselors) if counselors else None
            status = random.choices(
                [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED,
                 AlertStatus.RESOLVED, AlertStatus.DISMISSED],
                weights=[20, 30, 40, 10]
            )[0]

            alert = Alert(
                record_id=record.id,
                handler_id=handler.id if handler and status != AlertStatus.ACTIVE else None,
                alert_type="risk",
                risk_level=record.risk_level,
                status=status,
                title=f"【{record.risk_level.value.upper()}】{record.main_topic}风险预警",
                description=f"检测到{record.author_department}{record.author_grade}学生"
                           f"发表{record.risk_level.value}风险内容，"
                           f"情绪标签：{','.join(record.emotions or [])}",
                ai_suggestion="，".join(record.suggested_actions or []),
                handler_note=(
                    "已联系学生本人并安排心理辅导"
                    if status == AlertStatus.RESOLVED else None
                ),
                resolved_at=(
                    record.created_at + timedelta(hours=random.randint(2, 72))
                    if status == AlertStatus.RESOLVED else None
                ),
                triggered_at=record.analyzed_at,
                created_at=record.created_at,
            )
            alerts.append(alert)
    return alerts


def generate_daily_stats(session):
    """基于已有数据生成每日统计"""
    from sqlalchemy import func

    stats_list = []
    # 获取日期范围
    min_date = session.query(func.min(SentimentRecord.created_at)).scalar()
    max_date = session.query(func.max(SentimentRecord.created_at)).scalar()

    if not min_date or not max_date:
        return stats_list

    current = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = max_date.replace(hour=0, minute=0, second=0, microsecond=0)

    while current <= end:
        next_day = current + timedelta(days=1)

        day_records = session.query(SentimentRecord).filter(
            SentimentRecord.created_at >= current,
            SentimentRecord.created_at < next_day
        ).all()

        if day_records:
            total = len(day_records)
            pos = sum(1 for r in day_records if r.sentiment == SentimentType.POSITIVE)
            neg = sum(1 for r in day_records if r.sentiment == SentimentType.NEGATIVE)
            neu = total - pos - neg

            low = sum(1 for r in day_records if r.risk_level == RiskLevel.LOW)
            med = sum(1 for r in day_records if r.risk_level == RiskLevel.MEDIUM)
            high = sum(1 for r in day_records if r.risk_level == RiskLevel.HIGH)
            crit = sum(1 for r in day_records if r.risk_level == RiskLevel.CRITICAL)

            pending = sum(1 for r in day_records if r.review_status == ReviewStatus.PENDING)
            completed = sum(1 for r in day_records if r.review_status == ReviewStatus.APPROVED)

            # 统计话题分布
            topic_counts = {}
            emotion_counts = {}
            for r in day_records:
                if r.main_topic:
                    topic_counts[r.main_topic] = topic_counts.get(r.main_topic, 0) + 1
                for em in (r.emotions or []):
                    emotion_counts[em] = emotion_counts.get(em, 0) + 1

            top_topics = sorted(topic_counts.items(), key=lambda x: -x[1])[:10]
            top_emotions = sorted(emotion_counts.items(), key=lambda x: -x[1])[:10]

            avg_sent_conf = sum(
                r.sentiment_confidence or 0 for r in day_records
            ) / total
            avg_risk_conf = sum(
                r.risk_confidence or 0 for r in day_records
            ) / total

            stat = AnalysisStats(
                stat_date=current,
                period_type="daily",
                total_records=total,
                positive_count=pos,
                negative_count=neg,
                neutral_count=neu,
                low_risk_count=low,
                medium_risk_count=med,
                high_risk_count=high,
                critical_risk_count=crit,
                pending_review_count=pending,
                completed_review_count=completed,
                top_topics=[{"topic": t, "count": c} for t, c in top_topics],
                top_emotions=[{"emotion": e, "count": c} for e, c in top_emotions],
                avg_sentiment_confidence=round(avg_sent_conf, 3),
                avg_risk_confidence=round(avg_risk_conf, 3),
                created_at=next_day,
            )
            stats_list.append(stat)

        current = next_day

    return stats_list


def main():
    """主函数 - 生成全部数据"""
    print("=" * 60)
    print("  校园情感分析系统 - 高仿真数据生成器")
    print("  目标：15,000 条记录 + 关联数据")
    print("=" * 60)

    # 1. 初始化数据库
    print("\n[1/6] 初始化数据库表...")
    init_db()

    session = SessionLocal()

    try:
        # 2. 生成用户
        print("\n[2/6] 生成管理员和辅导员账户...")
        users = generate_users()
        session.add_all(users)
        session.commit()
        print(f"  ✓ 创建了 {len(users)} 个用户账户")

        # 3. 生成情感记录
        print("\n[3/6] 生成 15,000 条高仿真情感数据...")
        records = generate_records(15000)

        # 批量插入（每1000条提交一次）
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            session.add_all(batch)
            session.commit()

        # 刷新以获取ID
        session.flush()
        print(f"  ✓ 成功插入 {len(records)} 条记录")

        # 重新查询获取有ID的记录
        all_records = session.query(SentimentRecord).all()

        # 4. 生成审核任务
        print("\n[4/6] 生成审核任务...")
        tasks = generate_review_tasks(session, all_records)
        if tasks:
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                session.add_all(batch)
                session.commit()
        print(f"  ✓ 创建了 {len(tasks)} 个审核任务")

        # 5. 生成预警
        print("\n[5/6] 生成预警记录...")
        alerts = generate_alerts(session, all_records)
        if alerts:
            for i in range(0, len(alerts), batch_size):
                batch = alerts[i:i + batch_size]
                session.add_all(batch)
                session.commit()
        print(f"  ✓ 创建了 {len(alerts)} 条预警记录")

        # 6. 生成统计
        print("\n[6/6] 生成每日统计数据...")
        stats = generate_daily_stats(session)
        if stats:
            session.add_all(stats)
            session.commit()
        print(f"  ✓ 生成了 {len(stats)} 天的统计数据")

        print("\n" + "=" * 60)
        print("  数据生成完成！")
        print(f"  - 用户: {len(users)}")
        print(f"  - 情感记录: {len(records)}")
        print(f"  - 审核任务: {len(tasks)}")
        print(f"  - 预警记录: {len(alerts)}")
        print(f"  - 统计数据: {len(stats)} 天")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 数据生成失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
