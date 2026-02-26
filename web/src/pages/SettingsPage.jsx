import { useState, useEffect } from 'react'
import { fetchSettings, saveSettings, fetchCollectorStatus } from '../services/dashboardApi'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    notification: true,
    alertThreshold: '10%',
    keywords: '食堂,宿舍,热水,教务,考试,图书馆',
    crawlInterval: '30',
    autoAnalysis: true,
    emailAlert: false,
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [collector, setCollector] = useState(null)
  const [loadingSettings, setLoadingSettings] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const [s, c] = await Promise.all([
          fetchSettings().catch(() => null),
          fetchCollectorStatus().catch(() => null),
        ])
        if (s) setSettings(prev => ({ ...prev, ...s }))
        if (c) setCollector(c)
      } catch (e) { console.error(e) }
      finally { setLoadingSettings(false) }
    })()
  }, [])

  async function handleSave() {
    setSaving(true)
    setSaved(false)
    try {
      await saveSettings(settings)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      console.error(e)
      alert(`保存失败: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  if (loadingSettings) return <div className="page-loading"><div className="spinner" /><p>加载设置中...</p></div>

  function Toggle({ checked, onChange }) {
    return (
      <label style={{ position: 'relative', display: 'inline-block', width: 44, height: 24 }}>
        <input type="checkbox" checked={checked} onChange={onChange}
          style={{ opacity: 0, width: 0, height: 0 }} />
        <span style={{
          position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
          background: checked ? 'var(--accent)' : 'var(--border)',
          borderRadius: 12, transition: '0.3s',
        }}>
          <span style={{
            position: 'absolute', height: 18, width: 18, left: checked ? 22 : 3, bottom: 3,
            background: 'white', borderRadius: '50%', transition: '0.3s',
          }} />
        </span>
      </label>
    )
  }

  const inputStyle = {
    padding: '0.4rem 0.75rem', background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: 8, color: 'var(--text-primary)', fontSize: '0.85rem',
  }

  return (
    <div>
      <div className="grid-2 mb-15">
        {/* 基本设置 */}
        <div className="card" style={{ maxWidth: 700 }}>
          <div className="card-title">基本设置</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '0.5rem 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem' }}>通知推送</span>
              <Toggle checked={settings.notification}
                onChange={e => setSettings({ ...settings, notification: e.target.checked })} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem' }}>邮件预警</span>
              <Toggle checked={settings.emailAlert}
                onChange={e => setSettings({ ...settings, emailAlert: e.target.checked })} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem' }}>预警阈值(负面占比)</span>
              <select value={settings.alertThreshold}
                onChange={e => setSettings({ ...settings, alertThreshold: e.target.value })}
                style={inputStyle}>
                <option>5%</option><option>10%</option><option>15%</option><option>20%</option>
              </select>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem' }}>自动情感分析</span>
              <Toggle checked={settings.autoAnalysis}
                onChange={e => setSettings({ ...settings, autoAnalysis: e.target.checked })} />
            </div>
          </div>
        </div>

        {/* 采集设置 */}
        <div className="card" style={{ maxWidth: 700 }}>
          <div className="card-title">数据采集设置</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '0.5rem 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem' }}>监测关键词</span>
              <input type="text" value={settings.keywords}
                onChange={e => setSettings({ ...settings, keywords: e.target.value })}
                style={{ ...inputStyle, width: 260 }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem' }}>数据采集频率(分钟)</span>
              <select value={settings.crawlInterval}
                onChange={e => setSettings({ ...settings, crawlInterval: e.target.value })}
                style={inputStyle}>
                <option value="15">15</option><option value="30">30</option><option value="60">60</option><option value="120">120</option>
              </select>
            </div>

            {/* 数据采集器状态 */}
            {collector && (
              <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  数据采集器状态
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: collector.available ? '#00c48c' : '#ff4757'
                  }} />
                  <span style={{ color: collector.available ? '#00c48c' : '#ff4757' }}>
                    {collector.available ? '就绪' : '不可用'}
                  </span>
                </div>
                {collector.news_sources && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    支持新闻源：{collector.news_sources} 个平台
                  </div>
                )}
                {collector.capabilities && (
                  <div style={{ marginTop: '0.25rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    能力：{collector.capabilities.join('、')}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 保存按钮 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}
          style={{ padding: '0.6rem 2rem' }}>
          {saving ? '保存中...' : '保存设置'}
        </button>
        {saved && (
          <span style={{ color: '#00c48c', fontSize: '0.88rem', fontWeight: 600 }}>
            ✓ 设置已保存
          </span>
        )}
      </div>
    </div>
  )
}
