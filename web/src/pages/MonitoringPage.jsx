import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import {
  fetchSentimentTrend, fetchEmotions, fetchSources, fetchRecentMentions
} from '../services/dashboardApi'

export default function MonitoringPage() {
  const [sources, setSources] = useState([])
  const [trend, setTrend] = useState([])
  const [emotions, setEmotions] = useState([])
  const [mentions, setMentions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const [src, tr, em, mn] = await Promise.all([
          fetchSources(1), fetchSentimentTrend(7), fetchEmotions(7), fetchRecentMentions(10)
        ])
        setSources(src || []); setTrend(tr || [])
        setEmotions(em || []); setMentions(mn || [])
      } catch (e) { console.error(e) }
      finally { setLoading(false) }
    })()
  }, [])

  if (loading) return <div className="page-loading"><div className="spinner" /><p>加载数据中...</p></div>

  return (
    <div>
      {/* 平台声量卡片 */}
      <div className="stat-cards-row">
        {sources.slice(0, 4).map((p, i) => (
          <div key={i} className="stat-card">
            <div>
              <div className="stat-label">{p.name}声量</div>
              <div className="stat-value">{p.count?.toLocaleString() || 0}</div>
              <div className="stat-change up">占比 {p.value}%</div>
            </div>
            <span className="stat-icon" style={{ opacity: 0.6 }}>
              {['📱', '💬', '💻', '🎬'][i] || '📊'}
            </span>
          </div>
        ))}
        {sources.length === 0 && (
          <div className="stat-card">
            <div>
              <div className="stat-label">暂无数据</div>
              <div className="stat-value">--</div>
            </div>
          </div>
        )}
      </div>

      {/* 趋势图 + 词云 */}
      <div className="grid-2 mb-15">
        <div className="card">
          <div className="card-title">声量趋势</div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} tickFormatter={v => v?.slice(5)} />
              <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Legend />
              <Line type="monotone" dataKey="total" name="总量" stroke="var(--accent)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="negative" name="负面" stroke="#ff4757" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">实时舆情词云</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', alignItems: 'center', justifyContent: 'center', padding: '1rem', minHeight: 200 }}>
            {emotions.length > 0 ? emotions.map((em, i) => {
              const maxC = emotions[0]?.count || 1
              const size = 0.75 + (em.count / maxC) * 1.3
              const colors = ['#7c5ce7', '#00c48c', '#ff4757', '#f5a623', '#70a1ff', '#e17055']
              return (
                <span key={i} style={{
                  fontSize: `${size}rem`, color: colors[i % colors.length],
                  opacity: 0.5 + (em.count / maxC) * 0.5,
                  padding: '0.2rem 0.4rem', cursor: 'default',
                }}>
                  {em.word}
                </span>
              )
            }) : <p style={{ color: 'var(--text-secondary)' }}>暂无词云数据</p>}
          </div>
        </div>
      </div>

      {/* 最新提及列表 */}
      <div className="card">
        <div className="card-title">最新提及列表</div>
        <table className="data-table">
          <thead>
            <tr><th>用户/来源</th><th>内容</th><th>平台</th><th>情感</th><th>时间</th></tr>
          </thead>
          <tbody>
            {mentions.map((m, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{m.user}</td>
                <td style={{ maxWidth: 300 }}>{m.text}</td>
                <td><span className="tag tag-neutral">{m.platform}</span></td>
                <td>
                  <span className={`tag ${m.sentiment === '正面' ? 'tag-positive' : m.sentiment === '负面' ? 'tag-negative' : 'tag-neutral'}`}>
                    {m.sentiment}
                  </span>
                </td>
                <td style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{m.time}</td>
              </tr>
            ))}
            {mentions.length === 0 && (
              <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>暂无数据</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
