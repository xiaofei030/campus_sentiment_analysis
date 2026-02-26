import { useState } from 'react'
import { generateReport } from '../services/dashboardApi'

export default function ReportsPage() {
  const [generating, setGenerating] = useState(null) // 当前正在生成的类型
  const [reports, setReports] = useState({}) // 已生成的报告 { daily: data, weekly: data, ... }
  const [expandedReport, setExpandedReport] = useState(null)

  const today = new Date().toISOString().slice(0, 10)
  const weekNum = Math.ceil(new Date().getDate() / 7)
  const monthStr = `${new Date().getFullYear()}年${new Date().getMonth() + 1}月`

  async function handleGenerate(type) {
    setGenerating(type)
    try {
      const data = await generateReport(type)
      setReports(prev => ({ ...prev, [type]: data }))
      setExpandedReport(type)
    } catch (e) {
      console.error(e)
      alert(`报告生成失败: ${e.message}`)
    } finally {
      setGenerating(null)
    }
  }

  function renderReportPreview(type) {
    const data = reports[type]
    if (!data) return null

    return (
      <div style={{
        marginTop: '1rem', padding: '1.25rem',
        background: 'var(--bg-secondary)', borderRadius: 10,
        border: '1px solid var(--border)', fontSize: '0.85rem',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <span style={{ fontWeight: 700, color: 'var(--accent-light)' }}>
            {data.title || `${type}报告`}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            {data.generated_at?.slice(0, 16).replace('T', ' ')}
          </span>
        </div>

        {data.summary && (
          <p style={{ color: 'var(--text-primary)', lineHeight: 1.7, marginBottom: '0.75rem' }}>{data.summary}</p>
        )}

        {data.ai_summary && (
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontWeight: 600, marginBottom: '0.3rem', color: 'var(--accent-light)' }}>AI 智能分析</div>
            <p style={{ color: 'var(--text-primary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{data.ai_summary}</p>
          </div>
        )}

        {data.overview && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{ padding: '0.5rem', background: 'var(--bg-card)', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>总记录</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{data.overview.total_records?.toLocaleString()}</div>
            </div>
            <div style={{ padding: '0.5rem', background: 'var(--bg-card)', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>正面占比</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#00c48c' }}>
                {data.overview.total_records ? Math.round(data.overview.positive_count / data.overview.total_records * 100) : 0}%
              </div>
            </div>
            <div style={{ padding: '0.5rem', background: 'var(--bg-card)', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>负面率</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ff4757' }}>{data.overview.negative_rate}%</div>
            </div>
            <div style={{ padding: '0.5rem', background: 'var(--bg-card)', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>活跃预警</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f5a623' }}>{data.overview.active_alerts}</div>
            </div>
          </div>
        )}

        {data.topics && data.topics.length > 0 && (
          <div style={{ marginBottom: '0.5rem' }}>
            <div style={{ fontWeight: 600, marginBottom: '0.3rem', fontSize: '0.82rem' }}>热门话题 Top5</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {data.topics.slice(0, 5).map((t, i) => (
                <span key={i} className="tag tag-neutral">#{t.topic} ({t.count})</span>
              ))}
            </div>
          </div>
        )}

        <button className="btn btn-ghost" style={{ marginTop: '0.5rem' }}
          onClick={() => setExpandedReport(expandedReport === type ? null : type)}>
          {expandedReport === type ? '收起' : '展开详情'}
        </button>
      </div>
    )
  }

  const reportCards = [
    {
      type: 'daily', icon: '📊', title: `日报 ${today}`,
      desc: '舆情总量、正面占比、热点话题、预警统计...',
    },
    {
      type: 'weekly', icon: '📈', title: `周报 第${weekNum}周`,
      desc: '热点话题排行、情感趋势、院系对比分析...',
    },
    {
      type: 'monthly', icon: '📋', title: `月报 ${monthStr}`,
      desc: '月度舆情总览、趋势变化、风险预警统计、院系对比...',
    },
    {
      type: 'ai', icon: '🤖', title: 'AI 智能分析报告',
      desc: '基于多Agent协作系统，自动生成深度分析报告',
    },
  ]

  return (
    <div>
      <div className="grid-2 mb-15">
        {reportCards.slice(0, 2).map(card => (
          <div key={card.type} className="card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.5rem' }}>{card.icon}</span>
              <span style={{ fontSize: '1.15rem', fontWeight: 700 }}>{card.title}</span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
              {card.desc}
            </p>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-primary"
                onClick={() => handleGenerate(card.type)}
                disabled={generating !== null}>
                {generating === card.type ? '生成中...' : reports[card.type] ? '重新生成' : '生成报告'}
              </button>
              {reports[card.type] && (
                <button className="btn btn-outline"
                  onClick={() => setExpandedReport(expandedReport === card.type ? null : card.type)}>
                  {expandedReport === card.type ? '收起' : '查看报告'}
                </button>
              )}
            </div>
            {expandedReport === card.type && renderReportPreview(card.type)}
          </div>
        ))}
      </div>

      <div className="grid-2">
        {reportCards.slice(2).map(card => (
          <div key={card.type} className="card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.5rem' }}>{card.icon}</span>
              <span style={{ fontSize: '1.15rem', fontWeight: 700 }}>{card.title}</span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
              {card.desc}
            </p>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-primary"
                onClick={() => handleGenerate(card.type)}
                disabled={generating !== null}>
                {generating === card.type ? '生成中...' : reports[card.type] ? '重新生成' : card.type === 'ai' ? 'AI生成' : '生成报告'}
              </button>
              {reports[card.type] && (
                <button className="btn btn-outline"
                  onClick={() => setExpandedReport(expandedReport === card.type ? null : card.type)}>
                  {expandedReport === card.type ? '收起' : '查看报告'}
                </button>
              )}
            </div>
            {expandedReport === card.type && renderReportPreview(card.type)}
          </div>
        ))}
      </div>
    </div>
  )
}
