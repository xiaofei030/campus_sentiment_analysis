import { NavLink, useLocation } from 'react-router-dom'
import { useState } from 'react'
import './Layout.css'

const NAV_ITEMS = [
  { path: '/', icon: '📊', label: '总览仪表板' },
  { path: '/monitoring', icon: '👁', label: '舆情监测' },
  { path: '/sentiment', icon: '💜', label: '情感分析' },
  { path: '/topics', icon: '#', label: '热点话题' },
  { path: '/alerts', icon: '🔔', label: '预警中心' },
  { path: '/reports', icon: '📄', label: '分析报告' },
  { path: '/collector', icon: '🔍', label: '数据采集' },
  { path: '/settings', icon: '⚙', label: '系统设置' },
]

const PAGE_TITLES = {
  '/': { title: '总览仪表板', sub: '实时监测 · 智能分析 · 精准预警' },
  '/monitoring': { title: '舆情监测', sub: '实时监测 · 智能分析 · 精准预警' },
  '/sentiment': { title: '情感分析', sub: '实时监测 · 智能分析 · 精准预警' },
  '/topics': { title: '热点话题', sub: '实时监测 · 智能分析 · 精准预警' },
  '/alerts': { title: '预警中心', sub: '实时监测 · 智能分析 · 精准预警' },
  '/reports': { title: '分析报告', sub: '实时监测 · 智能分析 · 精准预警' },
  '/collector': { title: '数据采集', sub: '关键词爬取 · 多平台搜索 · 一键入库' },
  '/settings': { title: '系统设置', sub: '实时监测 · 智能分析 · 精准预警' },
  '/analysis': { title: '智能分析', sub: '多Agent协作 · MCP · Skill系统' },
}

const TIME_OPTIONS = ['过去24小时', '过去7天', '过去30天', '过去90天']

export default function Layout({ children }) {
  const location = useLocation()
  const pageInfo = PAGE_TITLES[location.pathname] || PAGE_TITLES['/']
  const [timeRange, setTimeRange] = useState('过去24小时')
  const [showTimeDropdown, setShowTimeDropdown] = useState(false)

  return (
    <div className="layout">
      {/* ===== 侧边栏 ===== */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <circle cx="16" cy="16" r="14" fill="url(#grad)" />
              <path d="M10 16l4 4 8-8" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              <defs><linearGradient id="grad" x1="0" y1="0" x2="32" y2="32">
                <stop stopColor="#7c5ce7"/><stop offset="1" stopColor="#a29bfe"/>
              </linearGradient></defs>
            </svg>
          </div>
          <div className="brand-text">
            <span className="brand-name">舆情监测</span>
            <span className="brand-version">v2.1.0 · 专业版</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="link-icon">{item.icon}</span>
              <span className="link-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-user">
          <div className="user-avatar">管</div>
          <div className="user-info">
            <span className="user-name">管理员</span>
            <span className="user-email">admin@campus.edu</span>
          </div>
        </div>
      </aside>

      {/* ===== 主内容区 ===== */}
      <div className="layout-main">
        {/* 顶栏 */}
        <header className="topbar">
          <div className="topbar-left">
            <h1 className="page-title">{pageInfo.title}</h1>
            <p className="page-subtitle">{pageInfo.sub}</p>
          </div>
          <div className="topbar-right">
            <div className="time-dropdown" onClick={() => setShowTimeDropdown(!showTimeDropdown)}>
              <span>{timeRange}</span>
              <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                <path d="M3 5l3 3 3-3"/>
              </svg>
              {showTimeDropdown && (
                <div className="dropdown-menu">
                  {TIME_OPTIONS.map(opt => (
                    <div key={opt} className={`dropdown-item ${timeRange === opt ? 'selected' : ''}`}
                      onClick={(e) => { e.stopPropagation(); setTimeRange(opt); setShowTimeDropdown(false) }}>
                      {opt}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button className="topbar-bell">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M10 2a6 6 0 016 6v3l2 2H2l2-2V8a6 6 0 016-6z"/>
                <path d="M8 17a2 2 0 004 0"/>
              </svg>
              <span className="bell-dot"></span>
            </button>
            <div className="topbar-avatar">管</div>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="page-content">
          {children}
        </main>

        {/* 底部状态 */}
        <footer className="layout-footer">
          <span className="status-dot"></span>
          <span>实时监测中</span>
        </footer>
      </div>
    </div>
  )
}
