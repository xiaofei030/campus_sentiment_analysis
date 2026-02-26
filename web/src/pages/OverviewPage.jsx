import { useState, useEffect } from 'react'
import {
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line
} from 'recharts'
import {
  fetchOverview, fetchSentimentTrend, fetchTopics,
  fetchDepartments, fetchRecentAlerts,
  fetchSources, fetchPlatformSentiment
} from '../services/dashboardApi'

const SENTIMENT_COLORS = { positive: '#00c48c', negative: '#ff4757', neutral: '#70a1ff' }

export default function OverviewPage() {
  const [overview, setOverview] = useState(null)
  const [trend, setTrend] = useState([])
  const [topics, setTopics] = useState([])
  const [alerts, setAlerts] = useState([])
  const [departments, setDepartments] = useState([])
  const [sources, setSources] = useState([])
  const [platformSentiment, setPlatformSentiment] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const [ov, tr, tp, al, dp, src, ps] = await Promise.all([
          fetchOverview(30), fetchSentimentTrend(7),
          fetchTopics(30), fetchRecentAlerts(5), fetchDepartments(30),
          fetchSources(30), fetchPlatformSentiment(30)
        ])
        setOverview(ov); setTrend(tr || []); setTopics(tp || [])
        setAlerts(al || []); setDepartments(dp || [])
        setSources(src || []); setPlatformSentiment(ps || [])
      } catch (e) { console.error(e) }
      finally { setLoading(false) }
    })()
  }, [])

  if (loading) return <div className="page-loading"><div className="spinner"/><p>加载数据中...</p></div>

  const sentimentPie = overview ? [
    { name: '正面', value: overview.positive_count, pct: Math.round(overview.positive_count / overview.total_records * 100) },
    { name: '负面', value: overview.negative_count, pct: Math.round(overview.negative_count / overview.total_records * 100) },
    { name: '中性', value: overview.neutral_count, pct: Math.round(overview.neutral_count / overview.total_records * 100) },
  ] : []

  return (
    <div className="overview-page">
      {/* 指标卡片 */}
      <div className="stat-cards-row">
        <div className="stat-card">
          <div>
            <div className="stat-label">今日舆情总量</div>
            <div className="stat-value">{overview?.today_new?.toLocaleString() || 0}</div>
            <div className="stat-change up">累计 {overview?.total_records?.toLocaleString() || 0} 条</div>
          </div>
          <span className="stat-icon">📈</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">正面情感占比</div>
            <div className="stat-value">{overview?.total_records ? Math.round(overview.positive_count / overview.total_records * 100) : 0}%</div>
            <div className="stat-change up">↑ {overview?.yesterday_new > 0 ? ((overview.positive_count / overview.total_records * 100) - 50).toFixed(1) : '0'}% 较昨日</div>
          </div>
          <span className="stat-icon">😊</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">热点话题数</div>
            <div className="stat-value">{topics?.length || 0}</div>
            <div className="stat-change up">实时追踪中</div>
          </div>
          <span className="stat-icon">🔥</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">活跃预警</div>
            <div className="stat-value">{overview?.active_alerts || 0}</div>
            <div className="stat-change down">{overview?.high_risk_count || 0}条严重 需处理</div>
          </div>
          <span className="stat-icon">🚨</span>
        </div>
      </div>

      {/* 24h情感趋势 + 来源分布 */}
      <div className="grid-2-1 mb-15">
        <div className="card">
          <div className="card-title">近7日情感趋势</div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" stroke="var(--text-secondary)" tick={{ fontSize: 11 }}
                tickFormatter={v => v?.slice(5)} />
              <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Legend />
              <Line type="monotone" dataKey="positive" name="正面" stroke="#00c48c" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="negative" name="负面" stroke="#ff4757" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="neutral" name="中性" stroke="#70a1ff" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">信息来源分布</div>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={sources} cx="50%" cy="50%" innerRadius={50} outerRadius={85}
                paddingAngle={3} dataKey="value">
                {sources.map((e, i) => <Cell key={i} fill={e.color || '#a0a0b0'} />)}
              </Pie>
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}
                formatter={(value, name, props) => [`${value}% (${props.payload.count}条)`, props.payload.name]}
              />
              <Legend formatter={(value, entry) => <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{entry.payload.name}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 情感详细占比 + 平台细表 + 热门话题 */}
      <div className="grid-1-1-1 mb-15">
        <div className="card">
          <div className="card-title">情感详细占比</div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={sentimentPie} cx="50%" cy="50%" outerRadius={80}
                dataKey="value" label={({ name, pct }) => `${name} ${pct}%`}>
                <Cell fill="#00c48c" /><Cell fill="#ff4757" /><Cell fill="#70a1ff" />
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            {departments?.slice(0, 3).map((d, i) => (
              <span key={i}>{d.department?.slice(0, 4)} {d.total}条</span>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-title">平台情感细表</div>
          <table className="data-table">
            <thead><tr><th>平台</th><th>总量</th><th>正面</th><th>负面</th><th>中性</th></tr></thead>
            <tbody>
              {platformSentiment.map((p, i) => (
                <tr key={i}>
                  <td>{p.name}</td><td>{p.total_fmt}</td>
                  <td style={{ color: '#00c48c' }}>{p.positive}</td>
                  <td style={{ color: '#ff4757' }}>{p.negative}</td>
                  <td>{p.neutral}</td>
                </tr>
              ))}
              {platformSentiment.length === 0 && (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>暂无数据</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-title">🔥 热门话题实时</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {topics.slice(0, 5).map((t, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.88rem' }}>#{t.topic}</span>
                <span style={{
                  padding: '0.15rem 0.6rem', borderRadius: 12,
                  background: i < 2 ? 'rgba(255,71,87,0.15)' : 'rgba(124,92,231,0.1)',
                  color: i < 2 ? '#ff4757' : 'var(--accent-light)',
                  fontSize: '0.8rem', fontWeight: 600,
                }}>{t.count}</span>
              </div>
            ))}
            {topics.length === 0 && <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>暂无话题</p>}
          </div>
          <button className="btn btn-primary" style={{ width: '100%', marginTop: '1rem', fontSize: '0.82rem' }}
            onClick={() => window.location.hash = '/topics'}>
            查看全部话题
          </button>
        </div>
      </div>

      {/* 最新预警 + 实时舆情摘要 */}
      <div className="grid-2">
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span className="card-title" style={{ margin: 0 }}>⚠️ 最新预警 ({alerts.length}条)</span>
            {overview?.high_risk_count > 0 && (
              <span className="tag tag-critical">{overview.high_risk_count}条严重</span>
            )}
          </div>
          {alerts.length === 0 ? <p style={{ color: 'var(--text-secondary)' }}>暂无预警</p> :
            alerts.map((a, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                padding: '0.6rem 0', borderBottom: i < alerts.length - 1 ? '1px solid var(--border)' : 'none'
              }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                  background: a.risk_level === 'critical' ? '#ff4757' : a.risk_level === 'high' ? '#e17055' : '#f5a623'
                }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600 }}>{a.title?.slice(0, 25)}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{a.content?.slice(0, 40)}</div>
                </div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                  {a.triggered_at?.slice(11, 16)}
                </span>
              </div>
            ))
          }
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span className="card-title" style={{ margin: 0 }}>📰 实时舆情摘要</span>
          </div>
          {departments?.slice(0, 5).map((d, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '0.5rem 0', borderBottom: i < 4 ? '1px solid var(--border)' : 'none'
            }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span className={`tag ${d.high_risk > 0 ? 'tag-negative' : 'tag-neutral'}`} style={{ fontSize: '0.7rem' }}>
                  {d.department?.slice(0, 4)}
                </span>
                <span style={{ fontSize: '0.85rem' }}>共{d.total}条 · 负面{d.negative}条</span>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                高风险{d.high_risk}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
