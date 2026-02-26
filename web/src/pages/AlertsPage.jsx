import { useState, useEffect, useCallback } from 'react'
import { fetchAlerts, fetchAlertStats, handleAlert } from '../services/dashboardApi'

const RISK_MAP = { critical: '严重', high: '高级', medium: '中级', low: '低级' }
const RISK_COLOR = { critical: '#ff4757', high: '#e17055', medium: '#f5a623', low: '#00c48c' }

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState(null)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [handling, setHandling] = useState(null) // 正在处理的 alert id
  const [filter, setFilter] = useState('all') // all / active / resolved

  const loadData = useCallback(async () => {
    try {
      const params = { page: 1, page_size: 30 }
      if (filter === 'active') params.status = 'active'
      else if (filter === 'resolved') params.status = 'resolved'

      const [al, st] = await Promise.all([
        fetchAlerts(params),
        fetchAlertStats(30)
      ])
      setAlerts(al?.alerts || [])
      setTotal(al?.total || 0)
      setStats(st)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [filter])

  useEffect(() => { loadData() }, [loadData])

  async function onHandleAlert(alertId, status) {
    setHandling(alertId)
    try {
      await handleAlert(alertId, 1, status, '')
      // 刷新数据
      await loadData()
    } catch (e) {
      console.error(e)
      alert(`处理失败: ${e.message}`)
    } finally {
      setHandling(null)
    }
  }

  if (loading) return <div className="page-loading"><div className="spinner" /><p>加载中...</p></div>

  return (
    <div>
      {/* 统计卡片 */}
      {stats && (
        <div className="stat-cards-row mb-15">
          <div className="stat-card">
            <div><div className="stat-label">总预警数</div><div className="stat-value">{stats.total}</div></div>
            <span className="stat-icon">🔔</span>
          </div>
          <div className="stat-card">
            <div><div className="stat-label">活跃预警</div><div className="stat-value" style={{ color: '#ff4757' }}>{stats.active}</div></div>
            <span className="stat-icon">🚨</span>
          </div>
          <div className="stat-card">
            <div><div className="stat-label">已处理</div><div className="stat-value" style={{ color: '#00c48c' }}>{stats.resolved}</div></div>
            <span className="stat-icon">✅</span>
          </div>
          <div className="stat-card">
            <div><div className="stat-label">处理率</div><div className="stat-value">{stats.resolution_rate}%</div></div>
            <span className="stat-icon">📊</span>
          </div>
        </div>
      )}

      {/* 筛选栏 */}
      <div className="card mb-15" style={{ padding: '0.75rem 1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>筛选：</span>
        {[
          { key: 'all', label: `全部 (${total})` },
          { key: 'active', label: '活跃' },
          { key: 'resolved', label: '已处理' },
        ].map(f => (
          <button key={f.key}
            className={`btn ${filter === f.key ? 'btn-primary' : 'btn-outline'}`}
            style={{ padding: '0.3rem 0.9rem', fontSize: '0.8rem' }}
            onClick={() => { setFilter(f.key); setLoading(true) }}>
            {f.label}
          </button>
        ))}
      </div>

      {/* 预警处理中心 */}
      <div className="card">
        <div className="card-title">⚠️ 预警处理中心</div>

        {alerts.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>暂无预警数据</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {alerts.map((a, i) => (
              <div key={a.id || i} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '1rem 1.25rem',
                background: a.risk_level === 'critical' ? 'rgba(255,71,87,0.06)' :
                  a.risk_level === 'high' ? 'rgba(225,112,85,0.04)' : 'transparent',
                borderRadius: 10,
                border: `1px solid ${a.risk_level === 'critical' ? 'rgba(255,71,87,0.15)' : 'var(--border)'}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, minWidth: 0 }}>
                  <span style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: RISK_COLOR[a.risk_level] || '#a0a0b0',
                    flexShrink: 0,
                  }} />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                      {a.title?.slice(0, 30) || '未命名预警'}
                      {' · '}
                      <span style={{ color: RISK_COLOR[a.risk_level] }}>{RISK_MAP[a.risk_level]}</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                      {a.content?.slice(0, 50) || a.description?.slice(0, 50)}
                      {a.triggered_at && ` · ${a.triggered_at.slice(0, 16).replace('T', ' ')}`}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0, marginLeft: '0.75rem' }}>
                  {a.status === 'resolved' ? (
                    <span className="tag tag-positive" style={{ fontSize: '0.78rem' }}>已处理</span>
                  ) : a.status === 'acknowledged' ? (
                    <>
                      <span className="tag tag-warning" style={{ fontSize: '0.78rem' }}>已确认</span>
                      <button className="btn btn-ghost" style={{ fontSize: '0.78rem', padding: '0.3rem 0.6rem' }}
                        disabled={handling === a.id}
                        onClick={() => onHandleAlert(a.id, 'resolved')}>
                        {handling === a.id ? '...' : '标记解决'}
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="btn btn-ghost" style={{ fontSize: '0.78rem', padding: '0.3rem 0.6rem' }}
                        disabled={handling === a.id}
                        onClick={() => onHandleAlert(a.id, 'acknowledged')}>
                        {handling === a.id ? '...' : '确认'}
                      </button>
                      <button className="btn btn-ghost" style={{ fontSize: '0.78rem', padding: '0.3rem 0.6rem', color: '#00c48c' }}
                        disabled={handling === a.id}
                        onClick={() => onHandleAlert(a.id, 'resolved')}>
                        {handling === a.id ? '...' : '解决'}
                      </button>
                      <button className="btn btn-ghost" style={{ fontSize: '0.78rem', padding: '0.3rem 0.6rem', color: 'var(--text-secondary)' }}
                        disabled={handling === a.id}
                        onClick={() => onHandleAlert(a.id, 'dismissed')}>
                        忽略
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
