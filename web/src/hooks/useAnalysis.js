import { useState, useCallback } from 'react'
import { analyzeText } from '../services/api'
import { DEFAULT_MODE } from '../constants/modes'

/**
 * 获取当前时间字符串
 */
function getTimeStr() {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour12: false })
}

/**
 * 根据模式和结果生成执行日志
 */
function generateLogs(mode, result) {
  const logs = []
  const baseTime = Date.now()

  // 通用：开始节点
  logs.push({
    time: getTimeStr(),
    node: 'START',
    message: '工作流启动',
    status: 'success'
  })

  if (mode === 'workflow') {
    // 预警工作流的完整日志
    if (result.sentiment) {
      logs.push({
        time: getTimeStr(),
        node: '情感分析',
        message: `检测到 ${result.sentiment.label} 情绪 (置信度: ${(result.sentiment.confidence * 100).toFixed(0)}%)`,
        status: 'success'
      })
    }
    if (result.risk) {
      logs.push({
        time: getTimeStr(),
        node: '风险评估',
        message: `风险等级: ${result.risk.level}, 得分: ${result.risk.score}`,
        status: 'success'
      })
    }
    logs.push({
      time: getTimeStr(),
      node: '路由决策',
      message: `判定风险等级为 ${result.risk_level}，进入${result.alert_triggered ? '预警' : '常规'}分支`,
      status: 'success'
    })
    if (result.alert_triggered) {
      logs.push({
        time: getTimeStr(),
        node: '预警触发',
        message: '⚠️ 已触发预警通知',
        status: 'success'
      })
    }
    if (result.knowledge_results?.length > 0) {
      logs.push({
        time: getTimeStr(),
        node: '知识检索',
        message: `检索到 ${result.knowledge_results.length} 条相关知识`,
        status: 'success'
      })
    }
    logs.push({
      time: getTimeStr(),
      node: '回复生成',
      message: '智能回复生成完成',
      status: 'success'
    })
  } else if (mode === 'knowledge') {
    // 知识库查询日志
    logs.push({
      time: getTimeStr(),
      node: '向量检索',
      message: '正在 ChromaDB 中进行语义检索...',
      status: 'success'
    })
    logs.push({
      time: getTimeStr(),
      node: '结果排序',
      message: result.found ? `找到 ${result.results?.length || 0} 条匹配结果` : '未找到相关结果',
      status: 'success'
    })
  } else {
    // 综合分析 / 单项分析日志
    if (result.sentiment) {
      logs.push({
        time: getTimeStr(),
        node: '情感分析',
        message: `分析完成: ${result.sentiment.label}`,
        status: 'success'
      })
    }
    if (result.topic) {
      logs.push({
        time: getTimeStr(),
        node: '主题聚类',
        message: `识别主题: ${result.topic.primary_topic}`,
        status: 'success'
      })
    }
    if (result.risk) {
      logs.push({
        time: getTimeStr(),
        node: '风险筛查',
        message: `风险等级: ${result.risk.level}`,
        status: 'success'
      })
    }
  }

  // 通用：结束节点
  logs.push({
    time: getTimeStr(),
    node: 'END',
    message: '工作流执行完成',
    status: 'success'
  })

  return logs
}

/**
 * 分析功能的自定义 Hook
 */
export function useAnalysis() {
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [activeMode, setActiveMode] = useState(DEFAULT_MODE)
  const [logs, setLogs] = useState([])

  const analyze = useCallback(async () => {
    if (!inputText.trim()) {
      setError('请输入文本')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setLogs([{
      time: getTimeStr(),
      node: 'START',
      message: '工作流启动，正在处理...',
      status: 'running'
    }])

    try {
      const response = await analyzeText(inputText, activeMode)
      
      if (response.success) {
        setResult(response.data)
        // 根据结果生成执行日志
        setLogs(generateLogs(activeMode, response.data))
      } else {
        setError(response.error)
        setLogs([{
          time: getTimeStr(),
          node: 'ERROR',
          message: response.error,
          status: 'error'
        }])
      }
    } catch (err) {
      setError(`请求失败: ${err.message}。请确保后端 API 已启动。`)
      setLogs([{
        time: getTimeStr(),
        node: 'ERROR',
        message: `请求失败: ${err.message}`,
        status: 'error'
      }])
    } finally {
      setLoading(false)
    }
  }, [inputText, activeMode])

  // 切换模式时清空日志
  const handleSetActiveMode = useCallback((mode) => {
    setActiveMode(mode)
    setLogs([])
    setResult(null)
    setError(null)
  }, [])

  return {
    inputText,
    setInputText,
    loading,
    result,
    error,
    activeMode,
    setActiveMode: handleSetActiveMode,
    analyze,
    logs,
  }
}
