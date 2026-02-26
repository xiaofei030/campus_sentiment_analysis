# -*- coding: utf-8 -*-
"""
小故事抓取脚本
每次运行会从网上获取几条励志/心理健康相关的小故事，追加到 stories.txt 文件中
"""

import requests
from datetime import datetime
from pathlib import Path

# 输出文件路径
OUTPUT_FILE = Path(__file__).parent / "stories.txt"

# API 列表（免费公开接口）
STORY_APIS = [
    {
        "name": "ZenQuotes",
        "url": "https://zenquotes.io/api/random",
        "extract": lambda data: f"「{data[0]['q']}」—— {data[0]['a']}"
    },
    {
        "name": "Quotable",
        "url": "https://api.quotable.io/random",
        "extract": lambda data: f"「{data['content']}」—— {data['author']}"
    },
    {
        "name": "Affirmations",
        "url": "https://www.affirmations.dev/",
        "extract": lambda data: f"「{data['affirmation']}」"
    },
]

# 备用故事（网络不通时使用）
FALLBACK_STORIES = [
    "每一次尝试，都是成功道路上的有效练习；放下焦虑，留给自己更多呼吸的空间。",
    "遇到情绪低落，先和自己说一句：我已经很努力了，慢慢来。",
    "当我们向他人倾诉压力时，往往感觉到的不只是被理解，更是重新找到力量。",
    "你不必完美，你只需要真实。接纳自己的不完美，是成长的第一步。",
    "压力像弹簧，适度的压力让我们成长，过度的压力需要及时释放。",
]


def fetch_story(api):
    """从单个 API 获取故事"""
    try:
        resp = requests.get(api["url"], timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return api["extract"](data)
    except Exception as e:
        print(f"  [!] {api['name']} 获取失败: {e}")
        return None


def fetch_all_stories():
    """从所有 API 获取故事"""
    stories = []
    print("正在获取小故事...")
    
    for api in STORY_APIS:
        print(f"  -> 尝试 {api['name']}...")
        story = fetch_story(api)
        if story:
            stories.append(story)
            print(f"     ✓ 成功")
    
    # 如果全部失败，使用备用故事
    if not stories:
        print("  [!] 网络获取失败，使用备用故事")
        import random
        stories = random.sample(FALLBACK_STORIES, min(3, len(FALLBACK_STORIES)))
    
    return stories


def save_stories(stories):
    """保存故事到文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"获取时间: {timestamp}\n")
        f.write(f"{'='*50}\n\n")
        
        for i, story in enumerate(stories, 1):
            f.write(f"{i}. {story}\n\n")
    
    print(f"\n✓ 已保存 {len(stories)} 条故事到: {OUTPUT_FILE.name}")


def main():
    stories = fetch_all_stories()
    if stories:
        save_stories(stories)
        print("\n本次获取的故事:")
        print("-" * 40)
        for story in stories:
            print(f"  • {story}")
    else:
        print("未获取到任何故事")


if __name__ == "__main__":
    main()
