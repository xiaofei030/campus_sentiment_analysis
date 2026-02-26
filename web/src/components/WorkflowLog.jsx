import { useEffect, useRef } from 'react'
import './WorkflowLog.css'

/**
 * 工作流执行日志组件
 * 展示 LangGraph 工作流的执行过程
 */
function WorkflowLog({ logs, isRunning }) {
  const logEndRef = useRef(null)

  // 自动滚动到最新日志
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="workflow-log">
      <div className="log-header">
        <span className="log-title">📋 工作流执行日志</span>
        {isRunning && <span className="log-status running">执行中...</span>}
      </div>
      <div className="log-content">
        {logs.length === 0 ? (
          <div className="log-empty">等待执行...</div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} className={`log-item ${log.status}`}>
              <span className="log-time">{log.time}</span>
              <span className={`log-icon ${log.status}`}>
                {log.status === 'success' ? '✓' : log.status === 'running' ? '◐' : '○'}
              </span>
              <span className="log-node">[{log.node}]</span>
              <span className="log-message">{log.message}</span>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  )
}

export default WorkflowLog
