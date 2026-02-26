import WorkflowDiagram from '../components/WorkflowDiagram'
import ResultCard from '../components/ResultCard'
import WorkflowLog from '../components/WorkflowLog'
import { useAnalysis } from '../hooks/useAnalysis'
import { ANALYSIS_MODES } from '../constants/modes'

export default function AnalysisPage() {
  const { inputText, setInputText, loading, result, error, activeMode, setActiveMode, analyze, logs } = useAnalysis()

  const renderResult = () => {
    if (!result) return null
    if (activeMode === 'workflow') {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <WorkflowDiagram riskLevel={result.risk_level} alertTriggered={result.alert_triggered} />
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span className={`tag ${result.risk_level === 'high' || result.risk_level === 'critical' ? 'tag-critical' : result.risk_level === 'medium' ? 'tag-warning' : 'tag-low'}`} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
              风险等级: {result.risk_level}
            </span>
            {result.alert_triggered && <span className="tag tag-critical" style={{ padding: '0.4rem 0.8rem' }}>已触发预警</span>}
          </div>
          {result.sentiment && <ResultCard title="情感分析" icon="S" data={result.sentiment} type="sentiment" />}
          {result.risk && <ResultCard title="风险评估" icon="R" data={result.risk} type="risk" />}
          <div className="card"><h4 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem' }}>智能回复</h4><p style={{ lineHeight: 1.8, fontSize: '0.9rem' }}>{result.response}</p></div>
        </div>
      )
    }
    if (activeMode === 'knowledge') {
      return (
        <div>
          <h3 style={{ marginBottom: '1rem' }}>检索结果</h3>
          {result.found ? result.results.map((item, idx) => (
            <div key={idx} className="card" style={{ marginBottom: '0.5rem' }}>
              <p style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>{item.content}</p>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>相关度: {(item.relevance_score * 100).toFixed(0)}%</span>
            </div>
          )) : <p style={{ color: 'var(--text-secondary)' }}>{result.message}</p>}
        </div>
      )
    }
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {result.sentiment && <ResultCard title="情感分析" icon="S" data={result.sentiment} type="sentiment" />}
        {result.topic && <ResultCard title="主题聚类" icon="T" data={result.topic} type="topic" />}
        {result.risk && <ResultCard title="风险筛查" icon="R" data={result.risk} type="risk" />}
      </div>
    )
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', maxWidth: 1400 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.6rem' }}>
          {ANALYSIS_MODES.map(mode => (
            <button key={mode.key} onClick={() => setActiveMode(mode.key)}
              style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                padding: '0.8rem 0.4rem', background: activeMode === mode.key ? 'rgba(124,92,231,0.15)' : 'var(--bg-card)',
                border: `2px solid ${activeMode === mode.key ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: 10, cursor: 'pointer', color: 'var(--text-primary)', transition: 'all 0.15s',
              }}>
              <span style={{ fontSize: '1.3rem' }}>{mode.icon}</span>
              <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>{mode.label}</span>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{mode.desc}</span>
            </button>
          ))}
        </div>
        <textarea value={inputText} onChange={e => setInputText(e.target.value)}
          placeholder="请输入要分析的文本，例如：最近考试压力好大，总是睡不好觉..."
          rows={5} style={{
            width: '100%', padding: '1rem', background: 'var(--bg-card)', border: '2px solid var(--border)',
            borderRadius: 12, color: 'var(--text-primary)', fontSize: '0.95rem', resize: 'vertical',
            fontFamily: 'inherit', minHeight: 130,
          }} />
        <button className="btn btn-primary" onClick={analyze} disabled={loading}
          style={{ padding: '0.8rem', fontSize: '1rem', width: '100%' }}>
          {loading ? '分析中...' : '开始分析'}
        </button>
        {error && <div style={{ padding: '0.75rem', background: 'rgba(255,71,87,0.1)', border: '1px solid var(--danger)', borderRadius: 8, color: 'var(--danger)', fontSize: '0.85rem' }}>{error}</div>}
      </div>

      <div className="card" style={{ minHeight: 400, maxHeight: 'calc(100vh - 180px)', overflowY: 'auto' }}>
        {loading ? (
          <div className="page-loading" style={{ minHeight: 200 }}><div className="spinner" /><p>分析中...</p></div>
        ) : result ? renderResult() : (
          activeMode === 'workflow' ? (
            <div><WorkflowDiagram riskLevel={null} alertTriggered={false} /><p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '1rem' }}>输入文本后点击"开始分析"</p></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 300, color: 'var(--text-secondary)' }}>
              <span style={{ fontSize: '3rem', opacity: 0.4, marginBottom: '1rem' }}>🔍</span>
              <p>输入文本并点击"开始分析"</p>
            </div>
          )
        )}
      </div>

      <div style={{ gridColumn: '1 / -1' }}>
        <WorkflowLog logs={logs} isRunning={loading} />
      </div>
    </div>
  )
}
