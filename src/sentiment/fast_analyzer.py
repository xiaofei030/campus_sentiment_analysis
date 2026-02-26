# src/sentiment/fast_analyzer.py
"""
快速情感分析器 - 基于关键词匹配，无需 LLM 调用
用于数据导入时的即时情感分类，可处理数百条记录毫无延迟
"""
import random
from typing import Dict, List

# ====================================================================
# 情感/风险关键词
# ====================================================================

POSITIVE_WORDS = [
    "开心", "快乐", "喜欢", "棒", "优秀", "成功", "进步", "感谢", "幸福",
    "期待", "满意", "舒服", "有趣", "值得", "成就", "希望", "加油", "美好",
    "温暖", "兴奋", "惊喜", "骄傲", "自豪", "感动", "欣慰", "自信",
    "充实", "收获", "突破", "好消息", "点赞", "太强",
    "牛", "厉害", "真好", "感恩", "不错", "很赞", "大赞", "完美",
    "支持", "鼓励", "奖", "冠军", "胜", "赢", "录取",
    "通过", "毕业", "就业", "保研", "考上", "上岸", "好评", "好棒",
    "好看", "好吃", "成就感", "安心", "愉快", "热爱",
]

NEGATIVE_WORDS = [
    "焦虑", "压力", "烦", "讨厌", "累", "失眠", "孤独", "绝望", "难过",
    "伤心", "郁闷", "无聊", "害怕", "失败", "痛苦", "崩溃", "迷茫",
    "后悔", "厌倦", "无助", "挂科", "不想", "烦躁", "糟糕", "哭",
    "难受", "抑郁", "紧张", "尴尬", "委屈", "愤怒", "生气", "不满",
    "失望", "沮丧", "担心", "恐惧", "悲伤", "无奈", "疲惫", "内卷",
    "矛盾", "冲突", "争议", "事故", "悲剧",
    "不公", "歧视", "暴力", "欺凌", "霸凌",
    "拉肚子", "生病", "头疼", "难熬", "好烦", "好累", "受不了",
    "不开心", "不舒服", "想哭", "压抑", "心累", "无语",
    "裁员", "下降", "危机", "亏损",
]

HIGH_RISK_WORDS = [
    "自杀", "自伤", "结束生命", "不想活", "活不下去", "割腕",
    "跳楼", "轻生", "遗书", "告别", "了结",
]

MEDIUM_RISK_WORDS = [
    "抑郁", "绝望", "崩溃", "极度", "严重焦虑", "恐慌",
    "社交恐惧", "厌食", "暴食", "自残", "无助", "放弃",
    "不想见人", "人生无意义",
]

EMOTION_MAP = {
    "焦虑": "焦虑", "压力": "压力", "烦": "烦躁", "累": "疲惫",
    "失眠": "失眠", "孤独": "孤独", "绝望": "绝望", "迷茫": "迷茫",
    "开心": "喜悦", "快乐": "喜悦", "幸福": "幸福", "感动": "感动",
    "期待": "期待", "兴奋": "兴奋", "害怕": "恐惧", "担心": "担忧",
    "愤怒": "愤怒", "生气": "愤怒", "委屈": "委屈", "无奈": "无奈",
    "后悔": "后悔", "伤心": "伤心", "难过": "难过", "满意": "满意",
    "自信": "自信", "骄傲": "骄傲", "沮丧": "沮丧",
    "内卷": "焦虑", "崩溃": "崩溃", "抑郁": "抑郁",
    "紧张": "紧张", "尴尬": "尴尬", "惊喜": "惊喜",
}

TOPIC_KEYWORDS = {
    "学业压力": ["考试", "挂科", "绩点", "作业", "论文", "毕设", "答辩", "复习", "教育"],
    "就业求职": ["就业", "工作", "实习", "面试", "简历", "offer", "秋招", "春招", "考公", "上岸", "裁员"],
    "考研升学": ["考研", "保研", "研究生", "初试", "复试", "调剂", "推免"],
    "校园生活": ["社团", "食堂", "宿舍", "图书馆", "校园", "同学", "室友", "活动"],
    "心理健康": ["焦虑", "抑郁", "压力", "失眠", "心理", "情绪", "咨询", "孤独", "健康"],
    "人际关系": ["朋友", "室友", "矛盾", "冲突", "社交", "恋爱", "分手", "吵架"],
    "经济困难": ["学费", "生活费", "贷款", "兼职", "打工", "奖学金", "助学金", "消费"],
    "网络舆情": ["网络", "热搜", "微博", "短视频", "舆论", "网暴", "造谣", "AI", "科技"],
    "社会热点": ["新闻", "政策", "改革", "经济", "医疗", "安全"],
    "文化娱乐": ["电影", "音乐", "游戏", "综艺", "追星", "动漫", "旅游", "体育"],
}


# ====================================================================
# 核心分析函数
# ====================================================================

def analyze_text(text: str) -> Dict:
    """对单条文本进行快速情感分析，返回完整的分析结果字典。"""
    if not text:
        return _default_result()

    text_lower = text.lower()

    pos_score, neg_score = 0, 0
    emotions: List[str] = []

    for word in POSITIVE_WORDS:
        if word in text_lower:
            pos_score += 1
    for word in NEGATIVE_WORDS:
        if word in text_lower:
            neg_score += 1

    for keyword, emotion in EMOTION_MAP.items():
        if keyword in text_lower and emotion not in emotions:
            emotions.append(emotion)

    if pos_score > neg_score:
        sentiment = "positive"
        confidence = min(0.6 + pos_score * 0.08, 0.95)
    elif neg_score > pos_score:
        sentiment = "negative"
        confidence = min(0.6 + neg_score * 0.08, 0.95)
    else:
        sentiment = "neutral"
        confidence = 0.5 + random.uniform(0, 0.2)

    if not emotions:
        if sentiment == "positive":
            emotions = [random.choice(["喜悦", "满意", "期待"])]
        elif sentiment == "negative":
            emotions = [random.choice(["焦虑", "压力", "烦躁"])]
        else:
            emotions = [random.choice(["平静", "淡定", "一般"])]

    risk_level = "low"
    risk_indicators: List[str] = []
    risk_confidence = 0.8

    for word in HIGH_RISK_WORDS:
        if word in text_lower:
            risk_level = "critical"
            risk_indicators.append(word)
    if risk_level != "critical":
        for word in MEDIUM_RISK_WORDS:
            if word in text_lower:
                risk_level = "high" if len(risk_indicators) > 0 else "medium"
                risk_indicators.append(word)

    if risk_level == "low" and sentiment == "negative" and neg_score >= 3:
        risk_level = "medium"
        risk_indicators.append("多重负面情绪叠加")

    main_topic = _detect_topic(text_lower)

    return {
        "sentiment": sentiment,
        "emotions": emotions[:5],
        "sentiment_confidence": round(confidence, 3),
        "risk_level": risk_level,
        "risk_indicators": risk_indicators or ["无明显风险"],
        "risk_confidence": round(risk_confidence, 3),
        "main_topic": main_topic,
        "suggested_actions": _get_suggested_actions(risk_level),
    }


def analyze_batch(texts: List[str]) -> List[Dict]:
    """批量快速分析"""
    return [analyze_text(t) for t in texts]


# ====================================================================
# 内部辅助
# ====================================================================

def _detect_topic(text: str) -> str:
    """从文本中检测主题"""
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[topic] = score
    if scores:
        return max(scores, key=scores.get)
    return random.choice(["社会热点", "校园生活", "网络舆情"])


def _get_suggested_actions(risk_level: str) -> List[str]:
    actions = {
        "low": ["常规关注"],
        "medium": ["持续关注情绪变化", "适时引导正面思考"],
        "high": ["安排辅导员约谈", "关注后续动态", "必要时联系心理咨询中心"],
        "critical": ["立即联系辅导员", "启动心理危机干预", "通知学生家长", "安排专业心理援助"],
    }
    return actions.get(risk_level, ["常规关注"])


def _default_result() -> Dict:
    return {
        "sentiment": "neutral",
        "emotions": ["平静"],
        "sentiment_confidence": 0.5,
        "risk_level": "low",
        "risk_indicators": ["无明显风险"],
        "risk_confidence": 0.5,
        "main_topic": "其他",
        "suggested_actions": ["常规关注"],
    }
