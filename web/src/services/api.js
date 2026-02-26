import axios from 'axios'

// ========== 创建 axios 实例 ==========
const request = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 30000, // 30秒超时（AI 分析可能较慢）
  headers: {
    'Content-Type': 'application/json',
  },
})

// ========== 请求拦截器 ==========
request.interceptors.request.use(
  (config) => {
    // 可在此添加 token 等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    
    // 开发环境打印请求日志
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config.data)
    }
    return config
  },
  (error) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

// ========== 响应拦截器 ==========
request.interceptors.response.use(
  (response) => {
    // 开发环境打印响应日志
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.url}`, response.data)
    }
    
    // 直接返回 data，简化调用
    return response.data
  },
  (error) => {
    // 统一错误处理
    let errorMessage = '请求失败'
    
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response
      switch (status) {
        case 400:
          errorMessage = data.detail || '请求参数错误'
          break
        case 401:
          errorMessage = '未授权，请重新登录'
          break
        case 403:
          errorMessage = '拒绝访问'
          break
        case 404:
          errorMessage = '请求的资源不存在'
          break
        case 500:
          errorMessage = '服务器内部错误'
          break
        default:
          errorMessage = data.detail || `请求错误 (${status})`
      }
    } else if (error.code === 'ECONNABORTED') {
      errorMessage = '请求超时，请稍后重试'
    } else if (error.message === 'Network Error') {
      errorMessage = '网络连接失败，请检查后端服务是否启动'
    }
    
    console.error('[API Error]', errorMessage, error)
    return Promise.reject(new Error(errorMessage))
  }
)

// ========== API 端点配置 ==========
const API_ENDPOINTS = {
  analyze: '/api/analyze',
  workflow: '/api/workflow/alert',
  knowledge: '/api/knowledge',
}

/**
 * 获取 API 端点和请求体
 */
function getEndpointConfig(mode, inputText) {
  switch (mode) {
    case 'full':
    case 'sentiment':
    case 'topic':
    case 'risk':
      return {
        url: API_ENDPOINTS.analyze,
        data: { text: inputText, mode },
      }
    case 'workflow':
      return {
        url: API_ENDPOINTS.workflow,
        data: { text: inputText },
      }
    case 'knowledge':
      return {
        url: API_ENDPOINTS.knowledge,
        data: { query: inputText },
      }
    default:
      return {
        url: API_ENDPOINTS.analyze,
        data: { text: inputText, mode: 'full' },
      }
  }
}

// ========== 导出 API 方法 ==========

/**
 * 调用分析 API
 * @param {string} inputText - 要分析的文本
 * @param {string} mode - 分析模式
 * @returns {Promise<{success: boolean, data?: any, error?: string}>}
 */
export async function analyzeText(inputText, mode) {
  try {
    const { url, data } = getEndpointConfig(mode, inputText)
    const response = await request.post(url, data)
    
    if (response.success) {
      return { success: true, data: response.data }
    } else {
      return { success: false, error: response.detail || '分析失败' }
    }
  } catch (error) {
    return { success: false, error: error.message }
  }
}

// 导出 axios 实例，方便其他地方使用
export { request }
export default request
