import { request } from './api'

// ========== 可视化面板 API ==========

export async function fetchOverview(days = 30) {
  const res = await request.get('/api/dashboard/overview', { params: { days } })
  return res.data
}

export async function fetchSentimentTrend(days = 30) {
  const res = await request.get('/api/dashboard/sentiment-trend', { params: { days } })
  return res.data
}

export async function fetchRiskTrend(days = 30) {
  const res = await request.get('/api/dashboard/risk-trend', { params: { days } })
  return res.data
}

export async function fetchTopics(days = 30) {
  const res = await request.get('/api/dashboard/topics', { params: { days } })
  return res.data
}

export async function fetchEmotions(days = 30) {
  const res = await request.get('/api/dashboard/emotions', { params: { days } })
  return res.data
}

export async function fetchDepartments(days = 30) {
  const res = await request.get('/api/dashboard/departments', { params: { days } })
  return res.data
}

export async function fetchRecentAlerts(limit = 10) {
  const res = await request.get('/api/dashboard/recent-alerts', { params: { limit } })
  return res.data
}

export async function fetchSources(days = 30) {
  const res = await request.get('/api/dashboard/sources', { params: { days } })
  return res.data
}

export async function fetchPlatformSentiment(days = 30) {
  const res = await request.get('/api/dashboard/platform-sentiment', { params: { days } })
  return res.data
}

export async function fetchRecentMentions(limit = 20) {
  const res = await request.get('/api/dashboard/recent-mentions', { params: { limit } })
  return res.data
}

export async function fetchTopicDetail(days = 30) {
  const res = await request.get('/api/dashboard/topic-detail', { params: { days } })
  return res.data
}

// ========== 审核 API ==========

export async function fetchReviewTasks(params = {}) {
  const res = await request.get('/api/review/tasks', { params })
  return res.data
}

export async function submitReview(data) {
  const res = await request.post('/api/review/submit', data)
  return res
}

export async function escalateTask(taskId) {
  const res = await request.post(`/api/review/escalate/${taskId}`)
  return res
}

export async function fetchReviewStats(reviewerId = null) {
  const params = reviewerId ? { reviewer_id: reviewerId } : {}
  const res = await request.get('/api/review/stats', { params })
  return res.data
}

// ========== 预警 API ==========

export async function fetchAlerts(params = {}) {
  const res = await request.get('/api/alerts', { params })
  return res.data
}

export async function fetchAlertStats(days = 30) {
  const res = await request.get('/api/alerts/stats', { params: { days } })
  return res.data
}

export async function handleAlert(alertId, handlerId, status = 'acknowledged', note = '') {
  const res = await request.post(`/api/alerts/${alertId}/handle`, null, {
    params: { handler_id: handlerId, status, note }
  })
  return res
}

// ========== 多Agent API ==========

export async function multiAgentAnalyze(text) {
  const res = await request.post('/api/multi-agent/analyze', { text })
  return res.data
}

// ========== 报告生成 API ==========

export async function generateReport(type = 'daily') {
  const res = await request.post('/api/reports/generate-enhanced', { type })
  return res.data
}

// ========== 系统设置 API ==========

export async function fetchSettings() {
  const res = await request.get('/api/settings')
  return res.data
}

export async function saveSettings(settings) {
  const res = await request.post('/api/settings', settings)
  return res
}

// ========== 数据采集 API ==========

export async function fetchCollectorStatus() {
  const res = await request.get('/api/collector/status')
  return res.data
}

export async function fetchCollectorSources() {
  const res = await request.get('/api/collector/sources')
  return res.data
}

export async function extractTopics() {
  const res = await request.post('/api/collector/extract-topics')
  return res.data
}

export async function collectNews(sources = null) {
  const params = {}
  if (sources) params.sources = sources
  const res = await request.post('/api/collector/collect-news', null, { params })
  return res.data
}

export async function runFullPipeline(sources = null, importDb = false, maxKeywords = 60) {
  const params = { import_db: importDb, max_keywords: maxKeywords }
  if (sources) params.sources = sources
  const res = await request.post('/api/collector/full-pipeline', null, { params })
  return res.data
}

// ========== 数据管理 API ==========

export async function clearTestData() {
  const res = await request.delete('/api/collector/clear-test-data')
  return res.data
}

// ========== 关键词深度爬取 API ==========

export async function keywordCrawl({ keywords, platforms, maxNotes = 10, headless = true, importToDb = true }) {
  const res = await request.post('/api/collector/keyword-crawl', {
    keywords,
    platforms,
    max_notes: maxNotes,
    headless,
    import_to_db: importToDb,
  }, { timeout: 600000 })
  return res.data
}

// ========== 情感分析模型 API ==========

export async function analyzeBatch(texts, model = null) {
  const body = { texts }
  if (model) body.model = model
  const res = await request.post('/api/sentiment/analyze-batch', body)
  return res.data
}

export async function ensemblePredict(text) {
  const res = await request.post('/api/sentiment/ensemble', { text })
  return res.data
}

export async function fetchSentimentModels() {
  const res = await request.get('/api/sentiment/models')
  return res.models
}
