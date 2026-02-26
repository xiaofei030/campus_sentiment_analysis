把前端当作一个小型“多模式分析 UI 案例”来理解，按「结构 → 功能 → 流程」三个层级抓重点：

结构层：先看 web/src/main.jsx 的入口挂载，再看 web/src/App.jsx 的页面骨架（输入区、模式选择、结果面板），然后梳理 hooks/useAnalysis.js（状态与请求）、services/api.js（接口封装）、constants/modes.js（模式配置）。
components/ 里重点是 WorkflowDiagram，它可视化展示风险分支流程，属于“结果解释层”的独立组件。

功能层：用三个维度记住前端能力：
多模式驱动：ANALYSIS_MODES 控制 UI 展示与请求类型。
统一状态管理：useAnalysis 管理输入、模式、loading、error、result。
多结果适配：App 根据 activeMode 渲染 workflow/knowledge/综合结果。

流程层（面试时常聊）：
用户输入 → 选择模式 → useAnalysis.analyze() → api.analyzeText() → 接口返回 → App 根据模式渲染对应结果。
workflow 模式 → 展示流程图 + 风险等级 + 可能触发预警 → 组合多个结果卡片。
knowledge 模式 → 展示检索列表与相关度。
其他模式 → 展示情感/主题/风险的组合卡片。

面试经验提示：
说清楚自己如何把“页面/状态/请求”分层，避免巨型组件。

答：“App 只管 UI 结构与结果展示，useAnalysis 管理业务状态与请求，api 统一处理 endpoint 与请求体，modes 统一配置模式，减少重复和耦合。”

能简述关键的工程点：为什么抽 Hook、为什么把模式集中配置。
答：“Hook 让输入/请求/错误状态统一管理，便于复用；modes 作为单一数据源，新增模式只需改一处配置 + 接口映射 + 结果分支。”

提到可扩展性：新增模式或结果类型如何快速落地。
答：“新增模式只需在 constants/modes.js 添加定义、在 api.js 增加 endpoint/body、在 App 里补一个结果分支，核心流程无需重写。”

最后强调可扩展点（主题化/组件化/性能）让面试官感觉你能继续推进。
答：可拆 ResultPanel/ModeSelector 组件、加入表单校验与缓存、把 API 基址配置化，并引入测试（如 React Testing Library）保障模式扩展稳定