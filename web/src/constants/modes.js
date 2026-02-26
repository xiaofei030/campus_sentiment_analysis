// 分析模式配置
export const ANALYSIS_MODES = [
  { key: 'full', label: '完整分析', icon: '📊', desc: '情感+主题+风险' },
  { key: 'sentiment', label: '情感分析', icon: '😊', desc: '分析情绪倾向' },
  { key: 'topic', label: '主题聚类', icon: '📁', desc: '识别话题分类' },
  { key: 'risk', label: '风险筛查', icon: '⚠️', desc: '评估心理风险' },
  { key: 'workflow', label: '预警工作流', icon: '🚨', desc: '完整预警流程' },
  { key: 'knowledge', label: '知识库查询', icon: '📚', desc: '检索相关知识' },
]

export const DEFAULT_MODE = 'full'
