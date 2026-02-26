# 校园舆情监测系统

一个面向辅导员和学生管理人员的校园舆情监测与情感分析平台。

能做什么？简单说就是：**自动从微博、知乎等社交平台采集与你学校相关的讨论内容，做情感分析和风险预警，然后在可视化面板上展示出来。**

数据采集与情感分析模块的设计参考了 [BettaFish](https://github.com/) 项目，已完全内置，无需额外依赖。深度爬取引擎基于 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)，支持 7 个平台的关键词搜索采集。


## 技术栈

| 层 | 用了什么 |
|---|---|
| 前端 | React 19 + Vite + Recharts + React Router |
| 后端 | FastAPI + Uvicorn |
| AI | LangChain + LangGraph + DeepSeek API |
| 存储 | MySQL + ChromaDB + HuggingFace Embeddings |
| 采集 | httpx + MediaCrawler + Playwright |
| 协议 | MCP (Model Context Protocol) |

## 主要功能

### 数据采集 — 两种方式

**被动采集**：从微博热搜、知乎热榜、B站等 12 个平台抓热点，用校园关键词过滤后入库。适合了解全网校园舆论动态。

**主动深度爬取（推荐）**：直接拿你自定义的关键词（比如 "XX大学 食堂"）去微博、知乎、小红书、抖音、快手、B站、贴吧这 7 个平台上搜索，爬回来的都是跟你学校直接相关的内容。基于 MediaCrawler + Playwright 实现，首次使用需要扫码登录对应平台。

采集回来的内容会自动走一遍情感分析 + 风险评估，高风险内容会触发预警。

### 情感分析

- 快速分析器：基于关键词匹配，不调 LLM，批量处理很快
- LLM 分析：调 DeepSeek 做深度情感判断
- 集成投票：多个模型加权投票，取综合结果

### 多 Agent 协作

CoordinatorAgent 调度下面几个专家 Agent 协同工作：
- SentimentAgent / TopicAgent / RiskAgent — 分别负责情感、话题、风险
- ReviewDecisionAgent — 自动审核排优先级
- KnowledgeAgent — 高风险时走 RAG 检索知识库
- ReportAgent — 汇总生成分析报告

### 可视化面板

8 个页面：总览仪表板、舆情监测、情感分析、热点话题、预警中心、分析报告、系统设置、智能分析（多 Agent 对话界面）。

### 其他

- **MCP Server**：把系统能力通过 MCP 协议暴露出来，Cursor / Claude Desktop 可以直接调用
- **Skill 系统**：可插拔的技能模块（数据分析、预警管理、报告生成）
- **人工审核**：自动创建审核任务 → 分配辅导员 → 审核处理

## 项目结构

```
├── api/main.py                     # FastAPI 入口
├── src/
│   ├── config.py                   # 配置
│   ├── data_pipeline.py            # 向量知识库构建
│   ├── crawler/                    # 数据采集
│   │   ├── news_collector.py       #   12+ 平台热点采集
│   │   ├── topic_extractor.py      #   AI 话题提取
│   │   ├── crawler_pipeline.py     #   采集管道（被动 + 主动）
│   │   ├── deep_crawler.py         #   多平台深度搜索
│   │   └── MediaCrawler/           #   MediaCrawler 引擎
│   ├── sentiment/                  # 情感分析
│   │   ├── predictor.py            #   多模型预测器 + 集成投票
│   │   └── fast_analyzer.py        #   快速关键词分析器
│   ├── agents/                     # 智能体
│   │   ├── coordinator_agent.py    #   协调者（核心）
│   │   ├── review_agent.py         #   审核
│   │   └── report_agent.py         #   报告
│   ├── tools/                      # LangChain 工具
│   ├── workflows/risk_alert.py     # LangGraph 预警工作流
│   ├── database/                   # MySQL 数据层
│   ├── services/                   # 业务服务
│   ├── skills/                     # Skill 技能模块
│   └── mcp_server/server.py        # MCP 服务
├── scripts/generate_data.py        # 测试数据生成（~15000 条）
├── web/src/                        # React 前端
│   ├── pages/                      #   8 个页面组件
│   └── services/                   #   API 调用层
├── knowledge_docs/                 # 知识库文档
├── .env.example                    # 环境变量模板
└── requirements.txt                # Python 依赖
```

## 快速开始

### 环境要求

- Python 3.10+、Node.js 18+、MySQL 8.0+
- Chrome 或 Edge（深度爬取通过 CDP 协议复用本机浏览器）

### 1. 安装依赖

```bash
# Python
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 前端
cd web && npm install && cd ..
```

> 国内装太慢可以加镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 2. 配置

把 `.env.example` 复制一份为 `.env`，填入你的 DeepSeek API Key 和 MySQL 密码：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=campus_sentiment
```

然后在 MySQL 中建库：

```sql
CREATE DATABASE campus_sentiment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 初始化数据 & 启动

```bash
# 建表 + 生成测试数据
python scripts/generate_data.py

# 启动后端（终端 1）
python api/main.py
# 访问 http://localhost:8000/docs 可以看到 Swagger 文档

# 启动前端（终端 2）
cd web && npm run dev
# 访问 http://localhost:5173
```

### 4. 跑一次深度爬取试试

在 Swagger 文档 (`http://localhost:8000/docs`) 里找到 `POST /api/collector/keyword-crawl`，填入：

```json
{
  "keywords": ["XX大学 食堂", "XX大学 宿舍"],
  "platforms": ["wb"],
  "max_notes": 5,
  "headless": false,
  "import_to_db": true
}
```

> `headless` 设成 `false` 很重要 — 首次使用会弹出浏览器让你扫码登录微博。登录一次之后，后面就可以设 `true` 跑无头模式了。

登录态保存在 `src/crawler/MediaCrawler/browser_data/`，Cookie 过期前不用重复登录。

### 支持的爬取平台

| 代码 | 平台 | 代码 | 平台 |
|---|---|---|---|
| `wb` | 微博 | `dy` | 抖音 |
| `zhihu` | 知乎 | `ks` | 快手 |
| `xhs` | 小红书 | `bili` | B站 |
| `tieba` | 贴吧 | | |

### 自定义关键词

默认关键词在 `src/crawler/crawler_pipeline.py` 的 `DEFAULT_CAMPUS_KEYWORDS` 里，改成你自己学校的就行。前端采集页面的预设关键词在 `web/src/pages/CollectorPage.jsx` 的 `PRESET_KEYWORDS`。

## API 概览

启动后端后访问 `http://localhost:8000/docs` 可以看到完整的交互式 API 文档。这里列几个常用的：

| 接口 | 干什么的 |
| `POST /api/collector/keyword-crawl` | 关键词深度爬取（最常用） |
| `POST /api/collector/full-pipeline` | 热点被动采集 |
| `POST /api/collector/analyze-pending` | 补充分析未处理的记录 |
| `GET /api/dashboard/overview` | 仪表板总览数据 |
| `POST /api/multi-agent/analyze` | 多 Agent 协作分析 |
| `POST /api/sentiment/analyze-batch` | 批量情感分析 |
| `POST /api/sentiment/ensemble` | 多模型集成预测 |
| `POST /api/reports/generate-enhanced` | 生成增强报告（日/周/月/AI） |
| `GET /api/alerts` | 预警列表 |
| `POST /api/alerts/{id}/handle` | 处理预警 |

完整端点列表见 Swagger 文档。

## 常见问题

**扫码登录后浏览器一直不动？**
正常，等它加载完。如果二维码过期了关掉重跑就行。

**点 Execute 后没弹出浏览器？**
大概率是 uvicorn 热重载把爬虫子进程杀了。确认 `api/main.py` 里 uvicorn 启动参数有 `reload_excludes=["**/MediaCrawler/**"]`，然后重启后端。

**MediaCrawler 目录不存在？**
重新拉一份：`git clone https://github.com/NanmiCoder/MediaCrawler "src/crawler/MediaCrawler"`

**Playwright 装不上？**
默认用 CDP 模式复用本机 Chrome/Edge，其实可以不装。如果确实要装，国内设镜像：`set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright`

**采集后看不到数据？**
检查接口返回的 `imported` 字段。如果用的是被动采集，`imported=0` 说明当前热榜没匹配到校园关键词，换深度爬取试试。前端记得硬刷新 (Ctrl+Shift+R)。

**重置数据库？**

```bash
mysql -u root -p -e "DROP DATABASE campus_sentiment; CREATE DATABASE campus_sentiment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
python scripts/generate_data.py
python api/main.py
```

## License

本项目仅供学习交流，深度爬取功能请遵守各平台使用条款和 robots.txt 规则。MediaCrawler 部分遵循其 [原项目许可](https://github.com/NanmiCoder/MediaCrawler)。
