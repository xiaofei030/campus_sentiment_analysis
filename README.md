# 校园舆情监测系统 v2.4.0

基于 **多智能体 + MCP + Skill** 架构的校园舆情监测与情感分析平台，面向辅导员和学生管理人员。

数据采集与情感分析模块吸收自 [BettaFish](https://github.com/) 项目的优秀设计模式，已完全内置于本项目，无需外部依赖。

**v2.4.0 新增**：集成 MediaCrawler 深度爬取引擎，支持用自定义校园关键词在微博、知乎等 7 个平台进行主动搜索爬取，告别被动等热榜。

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                    React 前端 (8 页面)                      │
│  总览仪表板│舆情监测│情感分析│热点话题│预警中心│分析报告│系统设置  │
├──────────────────────────────────────────────────────────┤
│                  FastAPI 后端 (v2.2.0)                     │
├──────┬──────┬──────┬────────────────────────────────────┤
│多Agent│ MCP  │Skill │        REST API Endpoints           │
│ 协作  │Server│ 系统 │  面板/审核/预警/采集/分析/报告/设置    │
├──────┴──────┴──────┴────────────────────────────────────┤
│                      业务模块层                              │
│  数据采集(crawler)  │  情感分析(sentiment)  │  智能体(agents) │
│  NewsCollector     │  SentimentPredictor  │  Coordinator    │
│  TopicExtractor    │  FastAnalyzer        │  ReviewAgent    │
│  CrawlerPipeline   │  Ensemble投票        │  ReportAgent    │
├──────────────────┬───────────────────────────────────────┤
│    ChromaDB      │             MySQL                      │
│   (向量知识库)    │   (舆情记录/审核/预警/统计)               │
└──────────────────┴───────────────────────────────────────┘
```

## 核心功能

### 1. 可视化数据面板（8个页面）
- **总览仪表板**：关键指标卡片、近7日情感趋势、信息来源分布、平台情感细表、热门话题、最新预警
- **舆情监测**：平台声量统计、声量趋势、实时舆情词云、最新提及列表
- **情感分析**：整体情感分布饼图、情感趋势(周)、正面/负面/中性高频词
- **热点话题**：话题全榜（热度、平台、情感、趋势指标）
- **预警中心**：预警统计、预警处理中心（确认/解决/忽略操作）
- **分析报告**：日报/周报/月报/AI智能报告生成与预览
- **系统设置**：通知推送、预警阈值、监测关键词、采集频率、采集器状态
- **智能分析**：多Agent协作分析界面

### 2. 数据采集模块（吸收自 BettaFish MindSpider）

**方式 A：热点被动采集**
- **NewsCollector**：从微博热搜、知乎热榜、B站热搜、今日头条、抖音热榜等 12 个公开平台实时采集热点
- **校园相关性过滤**：用 70+ 个校园关键词自动筛选，只保留与大学/校园/学生生活相关的真实数据
- **TopicExtractor**：基于 DeepSeek LLM 从热点新闻中提取校园相关话题和搜索关键词

**方式 B：关键词主动深度爬取（v2.4 新增，推荐）**
- **DeepCrawler**：集成 MediaCrawler 引擎，通过 Playwright 浏览器自动化在 7 个平台上按关键词搜索
- **支持平台**：微博(wb)、知乎(zhihu)、小红书(xhs)、抖音(dy)、快手(ks)、B站(bili)、贴吧(tieba)
- **自定义关键词**：可直接传入 `["XX大学 食堂", "XX大学 宿舍", ...]` 等校园关键词
- **自动入库**：爬取内容 → 情感分析 → 风险评估 → 写入 sentiment_records 表

**通用能力**
- **CrawlerPipeline**：统一采集管道，同时支持被动热点采集和主动关键词爬取
- **FastAnalyzer**：基于关键词匹配的快速情感分析器，无需 LLM 调用，可瞬间处理数百条记录

### 3. 情感分析模块（吸收自 BettaFish SentimentPredictor）
- **BaseModel 抽象基类**：统一的 train/predict/evaluate 接口设计
- **多模型管理**：支持注册多个分析模型（LangChain Tool、DeepSeek LLM 等）
- **集成投票**：ensemble_predict 加权多模型投票融合
- **快速分析器**：基于关键词匹配的即时情感/风险分类（用于批量导入场景）

### 4. 多智能体系统 (Multi-Agent)
- **CoordinatorAgent**：协调者，调度多个子Agent协作
- **SentimentAgent / TopicAgent / RiskAgent**：情感/主题/风险分析专家
- **ReviewDecisionAgent**：审核决策，自动计算优先级
- **KnowledgeAgent**：知识检索（高风险时触发 RAG）
- **ReportAgent**：综合报告生成

### 5. MCP Server
将系统能力以 MCP 协议暴露，供 Cursor / Claude Desktop 等 AI 工具直接调用。

### 6. Skill 技能系统
可插拔的技能模块：DataAnalysisSkill、AlertManagementSkill、ReportGenerationSkill。

### 7. 人工审核系统
自动创建审核任务 → 智能分配辅导员 → 审核操作 → 升级处理。

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | React 19 + Vite 7 + Recharts + React Router |
| 后端 | FastAPI + Uvicorn |
| AI引擎 | LangChain + LangGraph + DeepSeek |
| 向量库 | ChromaDB + HuggingFace Embeddings |
| 关系库 | MySQL + SQLAlchemy + PyMySQL |
| 协议 | MCP (Model Context Protocol) |
| 数据采集 | httpx + 公开新闻API + MediaCrawler + Playwright（吸收自 BettaFish MindSpider） |
| 情感分析 | 多模型集成预测 + 快速关键词分析器（吸收自 BettaFish SentimentPredictor） |

## 项目结构

```
campus_sentiment_analysis/
├── api/
│   └── main.py                    # FastAPI 主入口 v2.2.0
├── src/
│   ├── config.py                  # 配置管理
│   ├── data_pipeline.py           # 知识库构建
│   ├── crawler/                   # 数据采集模块（吸收自BettaFish）
│   │   ├── news_collector.py      # 12+平台热点新闻采集
│   │   ├── topic_extractor.py     # AI话题提取与关键词生成
│   │   ├── crawler_pipeline.py    # 采集管道（热点采集 + 关键词深度爬取）
│   │   ├── deep_crawler.py        # 多平台深度搜索爬虫（基于MediaCrawler）
│   │   └── MediaCrawler/          # MediaCrawler 引擎（7平台浏览器自动化）
│   ├── sentiment/                 # 情感分析模块（吸收自BettaFish）
│   │   ├── predictor.py           # 统一预测器+多模型+集成投票
│   │   └── fast_analyzer.py       # 快速关键词情感/风险分析器
│   ├── agents/                    # 智能体系统
│   │   ├── basic_agent.py         # 基础Agent
│   │   ├── coordinator_agent.py   # 协调者Agent（多Agent核心）
│   │   ├── review_agent.py        # 审核Agent
│   │   └── report_agent.py        # 报告Agent
│   ├── tools/                     # LangChain 工具
│   │   ├── sentiment_tool.py
│   │   ├── topic_cluster.py
│   │   ├── risk_screener.py
│   │   └── knowledge_tool.py
│   ├── workflows/
│   │   └── risk_alert.py          # LangGraph 预警工作流
│   ├── database/                  # MySQL 数据库层
│   │   ├── connection.py
│   │   └── models.py              # 5张表：用户/记录/审核/预警/统计
│   ├── services/
│   │   └── dashboard_service.py   # 面板数据服务
│   ├── skills/                    # Skill 技能系统
│   │   ├── base_skill.py
│   │   ├── data_analysis_skill.py
│   │   ├── alert_skill.py
│   │   └── report_skill.py
│   └── mcp_server/
│       └── server.py              # MCP 协议服务
├── scripts/
│   └── generate_data.py           # 生成测试数据（15000条高仿真数据）
├── web/                           # React 前端
│   └── src/
│       ├── App.jsx                # 路由入口
│       ├── components/Layout/     # 侧边栏+顶栏布局
│       ├── pages/
│       │   ├── OverviewPage.jsx   # 总览仪表板
│       │   ├── MonitoringPage.jsx # 舆情监测
│       │   ├── SentimentPage.jsx  # 情感分析
│       │   ├── TopicsPage.jsx     # 热点话题
│       │   ├── AlertsPage.jsx     # 预警中心
│       │   ├── ReportsPage.jsx    # 分析报告
│       │   ├── SettingsPage.jsx   # 系统设置
│       │   └── AnalysisPage.jsx   # 智能分析(多Agent)
│       └── services/
│           ├── api.js
│           └── dashboardApi.js
├── knowledge_docs/                # 知识库文档
├── .cursor/mcp.json               # MCP 配置
├── .env                           # 环境变量
└── requirements.txt               # Python 依赖
```

---

## 运行步骤

### 前置要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Chrome 或 Edge 浏览器（深度爬取需要，系统会通过 CDP 协议复用你的浏览器）

### 第一步：安装 Python 依赖

```bash
cd /path/to/campus_sentiment_analysis

# 创建并激活虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS/Linux

# 安装全部依赖（已包含主项目 + MediaCrawler 的所有依赖，一次性安装完）
pip install -r requirements.txt
```

> **PyCharm 用户**：如果你使用 PyCharm 管理虚拟环境，确保在 PyCharm 终端（底部 Terminal 面板）中执行上述命令，这样会自动使用项目的虚拟环境。

> **安装慢？** 建议使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 第二步：安装 Playwright 浏览器（深度爬取需要）

```bash
# 安装 Playwright 的 Chromium 内核（深度爬取用）
python -m playwright install chromium
```

> **可以跳过此步**：系统默认启用 **CDP 模式**（`ENABLE_CDP_MODE = True`），会直接复用你本机已安装的 Chrome 或 Edge 浏览器，不依赖 Playwright 自带的浏览器内核。如果你电脑上已有 Chrome/Edge，可跳过这步。

### 第三步：安装前端依赖

```bash
cd web
npm install
cd ..
```

### 第四步：配置环境变量

编辑项目根目录下的 `.env` 文件：

```env
# DeepSeek API（必需 - 用于AI话题提取和智能分析）
DEEPSEEK_API_KEY=你的API_Key
DEEPSEEK_API_BASE=https://api.deepseek.com

# MySQL 数据库配置（必需）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的数据库密码
MYSQL_DATABASE=campus_sentiment
```

### 第五步：创建 MySQL 数据库

在 MySQL 客户端（Navicat / MySQL Workbench / 命令行）中执行：

```sql
CREATE DATABASE campus_sentiment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 第六步：初始化数据库 & 生成测试数据

```bash
python scripts/generate_data.py
```

该脚本会：
1. 自动创建全部数据库表（User、SentimentRecord、ReviewTask、Alert、AnalysisStats）
2. 填充约 15000 条高仿真校园舆情测试数据，确保前端面板有内容展示

### 第七步：启动后端 API

```bash
python api/main.py
```

启动成功后你会看到：

```
============================================================
  校园舆情监测系统 API v2.1.0
  文档: http://localhost:8000/docs
============================================================
```

- API 地址：http://127.0.0.1:8000
- Swagger 交互文档：http://127.0.0.1:8000/docs （可在浏览器中直接测试所有接口）

### 第八步：启动前端

新开一个终端窗口：

```bash
cd /path/to/campus_sentiment_analysis\web
npm run dev
```

启动成功后访问：**http://localhost:5173**

### 第九步：首次运行深度爬取（核心功能）

深度爬取会用自定义关键词在微博、知乎等平台上搜索内容，**首次运行需要扫码登录各平台**。

#### 9.1 首次登录（必须用非无头模式，打开浏览器扫码）

在 Swagger 文档 http://127.0.0.1:8000/docs 中找到 `POST /api/collector/keyword-crawl`，点击 **Try it out**，填入：

```json
{
  "keywords": ["XX大学 食堂", "XX大学 宿舍"],
  "platforms": ["wb"],
  "max_notes": 5,
  "headless": false,
  "import_to_db": true
}
```

> **关键**：`headless` 必须设为 `false`，这样会弹出浏览器窗口让你扫码登录微博。

点击 **Execute** 后：
1. 系统会弹出 Chrome/Edge 浏览器窗口
2. 页面显示微博登录二维码 → **用微博 App 扫码登录**
3. 登录成功后浏览器会自动开始搜索爬取
4. 爬取完成后浏览器自动关闭，数据自动做情感分析并入库

> **等待时间**：Execute 后 API 不会立即返回响应，需要等待爬虫完成全部流程（可能 1-5 分钟）。  
> 如果超过 30 秒浏览器仍未弹出，请看下方排错指南。

#### 9.1.1 排错：点击 Execute 后没有弹出浏览器

**原因 1（最常见）：uvicorn 热重载杀死了爬虫子进程**

症状：后端终端显示 `WatchFiles detected changes in 'MediaCrawler\config\base_config.py'. Reloading...`，
API 返回 `stderr_tail` 包含 `Fatal Python error: init_import_site ... KeyboardInterrupt`。

原因：爬虫启动前会修改 MediaCrawler 的配置文件，uvicorn 的 `reload=True` 检测到 `.py` 文件变化后触发服务重启，
重启信号传播到爬虫子进程，导致子进程还没启动就被杀死。

修复方法（已在代码中修复）：确认 `api/main.py` 底部的 uvicorn 启动参数包含 `reload_excludes`：

```python
uvicorn.run(
    "api.main:app",
    host="127.0.0.1",
    port=8000,
    reload=True,
    reload_excludes=["**/MediaCrawler/**"],
)
```

修改后**必须重启后端服务**（Ctrl+C 停掉旧的，重新 `python api/main.py`）。

**原因 2：`base_config.py` 语法错误**

检查文件 `src/crawler/MediaCrawler/config/base_config.py`，确认 `CRAWLER_TYPE` 行是单行赋值：

```python
# 正确 ✅
CRAWLER_TYPE = "search"  # search | detail | creator

# 错误 ❌（多行遗留导致 SyntaxError）
CRAWLER_TYPE = "search"
    "search"  # ...
)
```

如果发现是错误格式，删除多余的两行，只保留单行赋值即可。

**其他排查步骤：**

1. **查看后端终端输出**：启动 `python api/main.py` 的终端窗口中会打印 MediaCrawler 子进程的 stdout/stderr，如果出错会显示完整的错误信息。

2. **手动测试 MediaCrawler 是否能正常运行**（在你的 PyCharm 虚拟环境终端中）：
   ```bash
   cd src/crawler/MediaCrawler
   python main.py --platform wb --lt qrcode --type search --keywords "XX大学" --headless False
   ```
   如果手动运行能弹出浏览器，说明 MediaCrawler 本身没问题；如果手动也报错，根据错误信息修复。

3. **检查依赖是否全部安装**：主项目的 `requirements.txt` 已包含 MediaCrawler 的全部依赖，确保已执行：
   ```bash
   pip install -r requirements.txt
   ```
   如果仍报缺少某个包，单独安装即可：`pip install 包名`

4. **确认 Python 解释器一致**：API 服务（`python api/main.py`）使用的 Python 必须和你安装依赖的是同一个虚拟环境。在终端中运行 `python -c "import sys; print(sys.executable)"` 确认路径与你的虚拟环境一致。

#### 9.2 扫码登录后（后续使用）

登录态会保存在 `src/crawler/MediaCrawler/browser_data/` 目录中。之后无需再次扫码，可以直接用无头模式运行：

```bash
curl -X POST http://127.0.0.1:8000/api/collector/keyword-crawl ^
  -H "Content-Type: application/json" ^
  -d "{\"keywords\": [\"XX大学 食堂\", \"XX大学 宿舍\", \"XX大学 考试\", \"XX大学 就业\"], \"platforms\": [\"wb\", \"zhihu\"], \"max_notes\": 10, \"headless\": true, \"import_to_db\": true}"
```

或在 Python 中调用：

```python
from src.crawler.crawler_pipeline import CrawlerPipeline

pipeline = CrawlerPipeline()
result = pipeline.run_keyword_crawling(
    keywords=["XX大学 食堂", "XX大学 宿舍", "XX大学 考研"],
    platforms=["wb", "zhihu"],
    max_notes=10,
    import_to_db=True,
)
print(result)
```

> **不传 keywords 参数**会自动使用内置的 15 个默认校园关键词（XX大学 食堂/宿舍/考试/选课/就业/图书馆/奖学金/实习/教务/社团/军训/考研 + XX大学相关）。

#### 9.3 支持的平台代码

| 代码 | 平台 | 说明 |
|------|------|------|
| `wb` | 微博 | 社会话题、校园生活讨论 |
| `zhihu` | 知乎 | 深度问答、校园经验分享 |
| `xhs` | 小红书 | 校园生活、学习经验 |
| `dy` | 抖音 | 校园短视频 |
| `ks` | 快手 | 校园生活记录 |
| `bili` | B站 | 学习资源、校园vlog |
| `tieba` | 贴吧 | 校园贴吧讨论 |

> 每个平台首次使用都需要单独扫码登录一次。建议先从 `wb`（微博）开始测试。

### 第十步：启动 MCP Server（可选）

```bash
python -m src.mcp_server.server
```

MCP Server 可供 Cursor / Claude Desktop 等 AI 工具直接调用系统能力。

### 快速启动清单（日常使用）

每次开发/演示时只需运行以下命令（2~3 个终端窗口）：

```bash
# 终端 1：激活虚拟环境 + 启动后端 API
cd /path/to/campus_sentiment_analysis
.venv\Scripts\activate
python api/main.py

# 终端 2：启动前端
cd /path/to/campus_sentiment_analysis\web
npm run dev

# 终端 3（可选）：触发数据采集
# 深度爬取（推荐，用校园关键词主动搜索）
curl -X POST http://127.0.0.1:8000/api/collector/keyword-crawl -H "Content-Type: application/json" -d "{\"platforms\": [\"wb\"], \"max_notes\": 10}"

# 或热点采集（被动获取各平台热榜，按校园关键词过滤入库）
curl -X POST "http://127.0.0.1:8000/api/collector/full-pipeline?import_db=true"
```

> **PyCharm 用户**：如果在 PyCharm 中打开项目，终端会自动激活虚拟环境，无需手动 activate。

---

## 数据采集使用

系统提供两种采集方式，推荐使用**方式 B（深度爬取）**获取真正与你学校相关的数据。

### 方式 A：热点被动采集（每天运行一次）

从 12 个平台的热榜中抓取数据，按校园关键词过滤后入库。适合获取全网校园热点。

```bash
curl -X POST "http://127.0.0.1:8000/api/collector/full-pipeline?import_db=true"
```

返回值中 `imported` 是入库的校园相关条目数，`skipped_not_campus` 是被过滤掉的无关数据数。

### 方式 B：关键词深度爬取（推荐）

用自定义关键词在微博、知乎等平台上**主动搜索**，爬取的全部是与你学校直接相关的内容。

```bash
# 在微博和知乎上搜索XX大学相关内容
curl -X POST http://127.0.0.1:8000/api/collector/keyword-crawl ^
  -H "Content-Type: application/json" ^
  -d "{\"keywords\": [\"XX大学 食堂\", \"XX大学 宿舍\", \"XX大学 考研\", \"XX大学 就业\"], \"platforms\": [\"wb\", \"zhihu\"], \"max_notes\": 10, \"import_to_db\": true}"
```

不传 `keywords` 参数会使用内置的 15 个默认校园关键词：

```bash
# 使用默认关键词，在微博上爬取
curl -X POST http://127.0.0.1:8000/api/collector/keyword-crawl ^
  -H "Content-Type: application/json" ^
  -d "{\"platforms\": [\"wb\"], \"max_notes\": 10}"
```

Python 调用方式：

```python
from src.crawler.crawler_pipeline import CrawlerPipeline

pipeline = CrawlerPipeline()

# 自定义关键词
result = pipeline.run_keyword_crawling(
    keywords=["XX大学 食堂", "XX大学 宿舍", "XX大学 考研"],
    platforms=["wb", "zhihu"],
    max_notes=10,
)

# 或使用默认关键词
result = pipeline.run_keyword_crawling(platforms=["wb"], max_notes=10)
```

### 补充分析（修复之前未分析的旧记录）

如果数据库中有 sentiment 为 NULL 的记录：

```bash
curl -X POST "http://127.0.0.1:8000/api/collector/analyze-pending"
```

### 自定义默认校园关键词

深度爬取的默认关键词定义在 `src/crawler/crawler_pipeline.py` 顶部的 `DEFAULT_CAMPUS_KEYWORDS` 列表中：

```python
DEFAULT_CAMPUS_KEYWORDS = [
    "XX大学 食堂", "XX大学 宿舍", "XX大学 考试",
    "XX大学 选课", "XX大学 就业", "XX大学 图书馆",
    "XX大学 奖学金", "XX大学 实习", "XX大学 教务",
    "XX大学 社团", "XX大学 军训", "XX大学 考研",
    "XX大学 食堂", "XX大学 宿舍", "XX大学 考试",
]
```

你可以根据需要修改这些关键词。修改后重启后端服务生效。

热点被动采集的过滤关键词在同文件的 `CAMPUS_FILTER_KEYWORDS` 列表中（用于方式 A）。

### 其他采集命令

```bash
# 查看采集器状态（含深度爬取支持的平台列表）
curl http://127.0.0.1:8000/api/collector/status

# 查看支持的全部新闻源
curl http://127.0.0.1:8000/api/collector/sources

# 仅采集热点新闻（不入库、不过滤，查看原始数据）
curl -X POST http://127.0.0.1:8000/api/collector/collect-news

# 仅做 AI 话题提取（不入库）
curl -X POST http://127.0.0.1:8000/api/collector/extract-topics

# 批量情感分析
curl -X POST http://127.0.0.1:8000/api/sentiment/analyze-batch ^
  -H "Content-Type: application/json" ^
  -d "{\"texts\": [\"今天食堂的饭真好吃\", \"考试压力太大了\"]}"

# 集成预测（多模型投票）
curl -X POST http://127.0.0.1:8000/api/sentiment/ensemble ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"考研压力好大但是还是要坚持\"}"
```

### 数据采集流程说明

```
方式A：热点被动采集                            方式B：关键词深度爬取（推荐）
                                             
 12个平台热榜                                  自定义校园关键词
(微博/知乎/B站...)                            ["XX大学 食堂", ...]
       │                                              │
       ▼                                              ▼
  NewsCollector                                  DeepCrawler
  (公开API采集)                                (MediaCrawler + Playwright)
       │                                              │
       ▼                                              ▼
  校园关键词过滤                                在微博/知乎等平台
  (去掉娱乐/财经等)                             按关键词搜索爬取
       │                                              │
       └──────────────┬───────────────────────────────┘
                      ▼
               CrawlerPipeline
               ├─ 快速情感分析（关键词匹配，无LLM）
               ├─ 风险等级评估
               ├─ 自动创建高风险预警
               └─ 写入 MySQL sentiment_records 表
```

---

## API 端点一览

| 分类 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **基础** | GET | `/` | 健康检查 |
| **AI分析** | POST | `/api/sentiment` | 情感分析 |
| | POST | `/api/topic` | 主题聚类 |
| | POST | `/api/risk` | 风险筛查 |
| | POST | `/api/knowledge` | 知识库查询 |
| | POST | `/api/analyze` | 综合分析 |
| | POST | `/api/workflow/alert` | 预警工作流 |
| **多Agent** | POST | `/api/multi-agent/analyze` | 多Agent协作分析 |
| | GET | `/api/multi-agent/agents` | Agent列表 |
| **面板** | GET | `/api/dashboard/overview` | 总览数据 |
| | GET | `/api/dashboard/sentiment-trend` | 情感趋势 |
| | GET | `/api/dashboard/risk-trend` | 风险趋势 |
| | GET | `/api/dashboard/topics` | 话题分布 |
| | GET | `/api/dashboard/emotions` | 情绪词云 |
| | GET | `/api/dashboard/departments` | 院系统计 |
| | GET | `/api/dashboard/recent-alerts` | 最近预警 |
| | GET | `/api/dashboard/sources` | 数据来源分布 |
| | GET | `/api/dashboard/platform-sentiment` | 平台情感细表 |
| | GET | `/api/dashboard/recent-mentions` | 最近舆情提及 |
| | GET | `/api/dashboard/topic-detail` | 话题详情 |
| **审核** | GET | `/api/review/tasks` | 审核任务列表 |
| | POST | `/api/review/submit` | 提交审核 |
| | GET | `/api/review/stats` | 审核统计 |
| **预警** | GET | `/api/alerts` | 预警列表 |
| | GET | `/api/alerts/stats` | 预警统计 |
| | POST | `/api/alerts/{id}/handle` | 处理预警 |
| **Skill** | GET | `/api/skills` | 技能列表 |
| | POST | `/api/skills/invoke` | 调用技能 |
| **MCP** | GET | `/api/mcp/tools` | MCP工具列表 |
| | POST | `/api/mcp/call` | 调用MCP工具 |
| **采集** | GET | `/api/collector/status` | 采集器状态 |
| | GET | `/api/collector/sources` | 支持的新闻源 |
| | POST | `/api/collector/collect-news` | 采集热点新闻 |
| | POST | `/api/collector/extract-topics` | AI话题提取 |
| | POST | `/api/collector/analyze-pending` | 补充分析未处理记录 |
| | POST | `/api/collector/full-pipeline` | 完整采集管道（被动热点） |
| | POST | `/api/collector/keyword-crawl` | **自定义关键词深度爬取（推荐）** |
| **模型** | POST | `/api/sentiment/analyze-batch` | 批量情感分析 |
| | POST | `/api/sentiment/ensemble` | 集成投票预测 |
| | GET | `/api/sentiment/models` | 模型列表 |
| **报告** | POST | `/api/reports/generate` | 生成报告 |
| | POST | `/api/reports/generate-enhanced` | 增强报告(日/周/月/AI) |
| **设置** | GET | `/api/settings` | 获取系统设置 |
| | POST | `/api/settings` | 保存系统设置 |

---

## 常见问题

### Q: 深度爬取时弹出浏览器后一直停在登录页？

这是正常现象，需要你用手机 App 扫描浏览器中显示的二维码完成登录。登录成功后爬虫会自动开始工作。如果二维码过期，关闭后重新运行即可。

### Q: 深度爬取报错 "MediaCrawler 目录不存在"？

MediaCrawler 引擎已包含在项目中（`src/crawler/MediaCrawler/` 目录）。如果该目录被误删，需要重新克隆：

```bash
git clone https://github.com/NanmiCoder/MediaCrawler "src/crawler/MediaCrawler"
```

### Q: playwright install 下载浏览器失败？

国内网络可能无法直接下载。解决方案：
1. **使用 CDP 模式**（默认已开启）：系统会复用你本机的 Chrome/Edge，无需额外下载
2. **设置镜像源**：`set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright` 后重试
3. **手动下载**：从镜像站下载后放到 `%LOCALAPPDATA%\ms-playwright\` 目录

### Q: 已经扫过码了，下次还需要扫码吗？

不需要。登录态保存在 `src/crawler/MediaCrawler/browser_data/` 目录。只要不删除该目录，后续运行可以直接用 `headless: true`。Cookie 过期后（通常几天到几周）需要重新扫码。

### Q: 采集后数据库中看不到新数据？

1. **用深度爬取（推荐）**：`POST /api/collector/keyword-crawl`，直接搜索你的关键词，数据量更可控
2. **检查返回值**：`imported` 表示入库数
3. **检查数据库**：在 MySQL 客户端查看 `sentiment_records` 表最新记录
4. **刷新前端**：浏览器硬刷新 (Ctrl+Shift+R)

如果使用被动热点采集（方式 A），`imported` 为 0 说明当前热榜没有匹配校园关键词的条目，这是正常的。建议改用深度爬取（方式 B）。

### Q: 如何采集到真正跟XX大学相关的数据？

使用**深度爬取**（方式 B），直接传入本校关键词：

```python
pipeline.run_keyword_crawling(
    keywords=["XX大学 食堂", "XX大学 宿舍", "XX大学 考研"],
    platforms=["wb", "zhihu"],
)
```

这会在微博/知乎上搜索这些关键词，爬回的内容都是与你学校直接相关的。

### Q: 如何重置数据库重新生成？

```bash
# 先删除旧数据库
mysql -u root -p -e "DROP DATABASE campus_sentiment; CREATE DATABASE campus_sentiment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 重新生成15000条测试数据
python scripts/generate_data.py

# 重启后端
python api/main.py
```
