import { useState, useEffect } from 'react'
import { fetchTopicDetail } from '../services/dashboardApi'

export default function TopicsPage() {
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const tp = await fetchTopicDetail(30)
        setTopics(tp || [])
      } catch (e) { console.error(e) }
      finally { setLoading(false) }
    })()
  }, [])

  if (loading) return <div className="page-loading"><div className="spinner" /><p>加载中...</p></div>

  const formatCount = (n) => n >= 1000 ? (n / 1000).toFixed(1) + 'k' : n

  const sentimentClass = (s) => {
    if (s === '正面') return 'tag-positive'
    if (s === '负面') return 'tag-negative'
    return 'tag-neutral'
  }

  return (
    <div>
      {/* 顶部统计 */}
      <div className="stat-cards-row mb-15">
        <div className="stat-card">
          <div>
            <div className="stat-label">追踪话题数</div>
            <div className="stat-value">{topics.length}</div>
          </div>
          <span className="stat-icon">🔥</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">正面话题</div>
            <div className="stat-value" style={{ color: '#00c48c' }}>
              {topics.filter(t => t.sentiment_raw === 'positive').length}
            </div>
          </div>
          <span className="stat-icon">😊</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">负面话题</div>
            <div className="stat-value" style={{ color: '#ff4757' }}>
              {topics.filter(t => t.sentiment_raw === 'negative').length}
            </div>
          </div>
          <span className="stat-icon">😟</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">上升趋势</div>
            <div className="stat-value" style={{ color: 'var(--accent-light)' }}>
              {topics.filter(t => t.trend === 'up').length}
            </div>
          </div>
          <span className="stat-icon">📈</span>
        </div>
      </div>

      <div className="card">
        <div className="card-title">🔥 热点话题全榜</div>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 40 }}>#</th>
              <th>话题</th>
              <th>热度</th>
              <th>主要平台</th>
              <th>整体情感</th>
              <th>趋势</th>
            </tr>
          </thead>
          <tbody>
            {topics.map((t, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 700, color: i < 3 ? '#ff4757' : 'var(--text-secondary)' }}>{i + 1}</td>
                <td style={{ fontWeight: 600 }}>#{t.topic}</td>
                <td style={{ fontWeight: 600 }}>{formatCount(t.count)}</td>
                <td><span className="tag tag-neutral">{t.platform}</span></td>
                <td>
                  <span className={`tag ${sentimentClass(t.sentiment)}`}>
                    {t.sentiment}
                  </span>
                </td>
                <td style={{ color: t.trend === 'up' ? '#00c48c' : t.trend === 'down' ? '#ff4757' : 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>
                  {t.trend === 'up' ? '↑ 上升' : t.trend === 'down' ? '↓ 下降' : '— 持平'}
                </td>
              </tr>
            ))}
            {topics.length === 0 && (
              <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>暂无话题数据</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
