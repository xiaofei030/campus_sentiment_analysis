import './WorkflowDiagram.css'

function WorkflowDiagram({ riskLevel, alertTriggered }) {
  const hasResult = riskLevel !== null
  const isHighRisk = ['medium', 'high', 'critical'].includes(riskLevel)
  
  return (
    <div className="workflow-diagram">
      <h4>🔄 工作流执行路径</h4>
      <div className="diagram-container">
        {/* 第一行：入口 */}
        <div className="diagram-row">
          <div className={`node start ${hasResult ? 'active' : 'pending'}`}>
            <span className="node-icon">📥</span>
            <span className="node-label">输入文本</span>
          </div>
        </div>
        
        {/* 曲线箭头 */}
        <svg className="curve-arrow" viewBox="0 0 100 40">
          <path 
            d="M50 0 Q50 20, 50 35" 
            className={hasResult ? 'active' : ''}
          />
          <polygon points="45,32 50,40 55,32" className={hasResult ? 'active' : ''} />
        </svg>
        
        {/* 第二行：情感分析 */}
        <div className="diagram-row">
          <div className={`node process ${hasResult ? 'active' : 'pending'}`}>
            <span className="node-icon">😊</span>
            <span className="node-label">情感分析</span>
          </div>
        </div>
        
        <svg className="curve-arrow" viewBox="0 0 100 40">
          <path d="M50 0 Q50 20, 50 35" className={hasResult ? 'active' : ''} />
          <polygon points="45,32 50,40 55,32" className={hasResult ? 'active' : ''} />
        </svg>
        
        {/* 第三行：风险评估 */}
        <div className="diagram-row">
          <div className={`node process ${hasResult ? 'active' : 'pending'}`}>
            <span className="node-icon">⚠️</span>
            <span className="node-label">风险评估</span>
          </div>
        </div>
        
        <svg className="curve-arrow" viewBox="0 0 100 40">
          <path d="M50 0 Q50 20, 50 35" className={hasResult ? 'active' : ''} />
          <polygon points="45,32 50,40 55,32" className={hasResult ? 'active' : ''} />
        </svg>
        
        {/* 第四行：条件路由 */}
        <div className="diagram-row">
          <div className={`node decision ${hasResult ? 'active' : 'pending'}`}>
            <span className="node-icon">🔀</span>
            <span className="node-label">路由</span>
          </div>
        </div>
        
        {/* 分支曲线 */}
        <svg className="branch-curves" viewBox="0 0 200 50">
          {/* 左分支曲线 */}
          <path 
            d="M100 0 Q100 15, 60 25 Q30 35, 30 45" 
            className={`branch-path ${hasResult && !isHighRisk ? 'active' : ''}`}
          />
          <polygon 
            points="25,42 30,50 35,42" 
            className={hasResult && !isHighRisk ? 'active' : ''}
          />
          {/* 右分支曲线 */}
          <path 
            d="M100 0 Q100 15, 140 25 Q170 35, 170 45" 
            className={`branch-path ${hasResult && isHighRisk ? 'active' : ''}`}
          />
          <polygon 
            points="165,42 170,50 175,42" 
            className={hasResult && isHighRisk ? 'active' : ''}
          />
          {/* 分支标签 */}
          <text x="25" y="20" className={`label ${hasResult && !isHighRisk ? 'active' : ''}`}>低风险</text>
          <text x="145" y="20" className={`label ${hasResult && isHighRisk ? 'active' : ''}`}>中/高风险</text>
        </svg>
        
        {/* 第五行：分支节点 */}
        <div className="diagram-row branches">
          <div className={`node process ${!hasResult ? 'pending' : (!isHighRisk ? 'active' : 'inactive')}`}>
            <span className="node-icon">💬</span>
            <span className="node-label">简单回复</span>
          </div>
          <div className={`node process ${!hasResult ? 'pending' : (isHighRisk ? 'active' : 'inactive')}`}>
            <span className="node-icon">📚</span>
            <span className="node-label">知识检索</span>
          </div>
        </div>
        
        {/* 两侧并行的连接线 */}
        <div className="parallel-lines">
          {/* 左侧 - 简单回复向下 */}
          <svg className="vertical-curve" viewBox="0 0 100 70">
            <path 
              d="M50 0 Q50 35, 50 65" 
              className={hasResult && !isHighRisk ? 'active' : ''}
            />
            <polygon 
              points="45,62 50,70 55,62" 
              className={hasResult && !isHighRisk ? 'active' : ''}
            />
          </svg>
          
          {/* 右侧 - 知识检索 → 专业回复 → 向下 */}
          <div className="right-branch">
            <svg className="vertical-curve" viewBox="0 0 100 40">
              <path 
                d="M50 0 Q50 20, 50 35" 
                className={hasResult && isHighRisk ? 'active' : ''}
              />
              <polygon 
                points="45,32 50,40 55,32" 
                className={hasResult && isHighRisk ? 'active' : ''}
              />
            </svg>
            <div className={`node process ${!hasResult ? 'pending' : (isHighRisk ? 'active' : 'inactive')}`}>
              <span className="node-icon">🤖</span>
              <span className="node-label">专业回复</span>
            </div>
            <svg className="vertical-curve" viewBox="0 0 100 40">
              <path 
                d="M50 0 Q50 20, 50 35" 
                className={hasResult && isHighRisk ? 'active' : ''}
              />
              <polygon 
                points="45,32 50,40 55,32" 
                className={hasResult && isHighRisk ? 'active' : ''}
              />
            </svg>
          </div>
        </div>
        
        {/* 汇聚曲线 */}
        <svg className="converge-curves" viewBox="0 0 280 30">
          {/* 左侧汇聚线 */}
          <path 
            d="M45 0 Q80 0, 110 15 Q140 28, 140 28" 
            className={`converge-path ${hasResult && !isHighRisk ? 'active' : ''}`}
          />
          {/* 右侧汇聚线 */}
          <path 
            d="M235 0 Q200 0, 170 15 Q140 28, 140 28" 
            className={`converge-path ${hasResult && isHighRisk ? 'active' : ''}`}
          />
          <polygon 
            points="135,25 140,33 145,25" 
            className={hasResult ? 'active' : ''}
          />
        </svg>
        
        {/* 结束节点 */}
        <div className="diagram-row">
          <div className={`node end ${hasResult ? 'active' : 'pending'}`}>
            <span className="node-icon">✅</span>
            <span className="node-label">输出结果</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WorkflowDiagram
