import './ResultCard.css'

function ResultCard({ title, icon, data, type }) {
  if (!data) return null

  return (
    <div className={`result-card ${type}`}>
      <h4>{icon} {title}</h4>
      
      {type === 'sentiment' && (
        <>
          <div className="result-row">
            <span className="label">情感倾向</span>
            <span className={`value sentiment-${data.sentiment}`}>{data.sentiment}</span>
          </div>
          <div className="result-row">
            <span className="label">具体情绪</span>
            <span className="value tags">
              {data.emotions?.map((e, i) => <span key={i} className="tag">{e}</span>)}
            </span>
          </div>
          <div className="result-row">
            <span className="label">置信度</span>
            <span className="value">{(data.confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="result-row reasoning">
            <span className="label">分析理由</span>
            <span className="value">{data.reasoning}</span>
          </div>
        </>
      )}

      {type === 'topic' && (
        <>
          <div className="result-row">
            <span className="label">主要话题</span>
            <span className="value highlight">{data.main_topic}</span>
          </div>
          <div className="result-row">
            <span className="label">细分话题</span>
            <span className="value tags">
              {data.sub_topics?.map((t, i) => <span key={i} className="tag">{t}</span>)}
            </span>
          </div>
          <div className="result-row">
            <span className="label">关键词</span>
            <span className="value tags">
              {data.keywords?.map((k, i) => <span key={i} className="tag keyword">{k}</span>)}
            </span>
          </div>
        </>
      )}

      {type === 'risk' && (
        <>
          <div className="result-row">
            <span className="label">风险等级</span>
            <span className={`value risk-level ${data.risk_level}`}>{data.risk_level}</span>
          </div>
          <div className="result-row">
            <span className="label">风险信号</span>
            <span className="value tags">
              {data.risk_indicators?.map((r, i) => <span key={i} className="tag risk">{r}</span>)}
            </span>
          </div>
          <div className="result-row">
            <span className="label">建议行动</span>
            <ul className="actions">
              {data.suggested_actions?.map((a, i) => <li key={i}>{a}</li>)}
            </ul>
          </div>
        </>
      )}
    </div>
  )
}

export default ResultCard
