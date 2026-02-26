# -*- coding: utf-8 -*-
"""
学校信息配置 - 用于文档预处理时的文本替换
请根据你自己的学校信息修改以下配置
"""

# 目标学校信息（请替换为你的学校）
SCHOOL_INFO = {
    "name": "XX大学",
    "name_en": "XX University",
    "abbr": "XXU",
    "city": "某市",
    "province": "某省",
    "address": "某省某市某区某路某号",
    "postal_code": "000000",
    "counseling_center": {
        "name": "XX大学心理健康教育与咨询中心",
        "phone": "000-0000000",
        "location": "学生活动中心",
        "hours": "周一至周五 8:30-12:00, 14:30-17:30",
    },
    "hospital": {
        "name": "XX大学校医院",
        "phone": "000-0000000",
        "emergency": "000-0000000",
    },
    "hotlines": {
        "school": "000-0000000",
        "city": "000-00000000",
    }
}

# 需要替换的关键词映射（原文 -> 替换后）
# 如果你的知识库文档中包含其他学校名称，可以在这里配置替换规则
REPLACEMENTS = {
    # 学校名称
    "原大学名称": SCHOOL_INFO["name"],
    "OrigUniv": SCHOOL_INFO["abbr"],
    "origuniv": SCHOOL_INFO["abbr"].lower(),
    "Original University": SCHOOL_INFO["name_en"],

    # 城市/地区
    "原城市": SCHOOL_INFO["city"],
    "原城市市": f"{SCHOOL_INFO['city']}市",
    "原省份省": SCHOOL_INFO["province"],
    "原省份": SCHOOL_INFO["province"],

    # 通用替换
    "学校心理咨询中心": SCHOOL_INFO["counseling_center"]["name"],
}

# 需要追加的学校特定信息（在文档末尾添加）
SCHOOL_RESOURCES = f"""
===== {SCHOOL_INFO['name']}心理援助资源 =====

1. {SCHOOL_INFO['counseling_center']['name']}
   - 电话：{SCHOOL_INFO['counseling_center']['phone']}
   - 地点：{SCHOOL_INFO['counseling_center']['location']}
   - 服务时间：{SCHOOL_INFO['counseling_center']['hours']}

2. {SCHOOL_INFO['hospital']['name']}
   - 门诊电话：{SCHOOL_INFO['hospital']['phone']}
   - 急救电话：{SCHOOL_INFO['hospital']['emergency']}

3. 本市心理援助热线
   - 热线电话：{SCHOOL_INFO['hotlines']['city']}
   - 服务时间：24小时

4. 全国心理援助热线
   - 全国热线：400-161-9995
   - 希望24热线：400-161-9995
   - 生命热线：400-821-1215
"""
