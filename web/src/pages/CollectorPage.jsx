import { useState, useEffect } from 'react'
import { keywordCrawl, fetchCollectorStatus, clearTestData } from '../services/dashboardApi'

const PLATFORMS = [
  { code: 'wb', name: '微博', desc: '社会话题、校园生活' },
  { code: 'zhihu', name: '知乎', desc: '深度问答、经验分享' },
  { code: 'xhs', name: '小红书', desc: '校园生活、学习经验' },
  { code: 'bili', name: 'B站', desc: '学习资源、校园vlog' },
  { code: 'tieba', name: '贴吧', desc: '校园贴吧讨论' },
  { code: 'dy', name: '抖音', desc: '校园短视频' },
  { code: 'ks', name: '快手', desc: '校园生活记录' },
]

const PRESET_KEYWORDS = [
  'XX大学 食堂', 'XX大学 宿舍', 'XX大学 考试',
  'XX大学 选课', 'XX大学 就业', 'XX大学 图书馆',
  'XX大学 奖学金', 'XX大学 实习', 'XX大学 考研',
]

export default function CollectorPage() {
  const [keywordText, setKeywordText] = useState('XX大学 食堂\nXX大学 宿舍')
  const [selectedPlatforms, setSelectedPlatforms] = useState(['wb'])
  const [maxNotes, setMaxNotes] = useState(10)
  const [headless, setHeadless] = useState(false)
  const [importing, setImporting] = useState(true)

  const [crawling, setCrawling] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [clearResult, setClearResult] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [collector, setCollector] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    fetchCollectorStatus().then(setCollector).catch(() => {})
  }, [])

  async function handleClear() {
    if (!window.confirm('确认清空所有数据（包括测试数据和已采集数据）？\n清空后只有重新采集才能看到数据。')) return
    setClearing(true)
    setClearResult(null)
    try {
      const data = await clearTestData()
      setClearResult(data)
    } catch (e) {
      setClearResult({ message: '清空失败: ' + e.message })
    } finally {
      setClearing(false)
    }
  }

  function togglePlatform(code) {
    setSelectedPlatforms(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    )
  }

  function addPresetKeywords() {
    const current = keywordText.trim()
    const existing = new Set(current.split('\n').map(k => k.trim()).filter(Boolean))
    const toAdd = PRESET_KEYWORDS.filter(k => !existing.has(k))
    if (toAdd.length > 0) {
      setKeywordText(current ? current + '\n' + toAdd.join('\n') : toAdd.join('\n'))
    }
  }

  async function handleCrawl() {
    const keywords = keywordText.split('\n').map(k => k.trim()).filter(k => k.length > 0)
    if (keywords.length === 0) { setError('请输入至少一个关键词'); return }
    if (selectedPlatforms.length === 0) { setError('请选择至少一个平台'); return }

    setCrawling(true)
    setResult(null)
    setError(null)

    try {
      const data = await keywordCrawl({
        keywords,
        platforms: selectedPlatforms,
        maxNotes,
        headless,
        importToDb: importing,
      })
      setResult(data)
      setHistory(prev => [{
        time: new Date().toLocaleTimeString(),
        keywords: keywords.length,
        platforms: selectedPlatforms.join(', '),
        items: data?.crawl_result?.total_items || 0,
        imported: data?.import_result?.imported || 0,
      }, ...prev.slice(0, 9)])
    } catch (e) {
      setError(e.message || '采集失败')
    } finally {
      setCrawling(false)
    }
  }

  const s = {
    input: {
      width: '100%', padding: '0.6rem 0.75rem', background: 'var(--bg-card)',
      border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)',
      fontSize: '0.85rem', resize: 'vertical', fontFamily: 'inherit',
    },
    chip: (active) => ({
      padding: '0.4rem 0.9rem', borderRadius: 20, fontSize: '0.8rem', cursor: 'pointer',
      border: `1.5px solid ${active ? 'var(--accent)' : 'var(--border)'}`,
      background: active ? 'rgba(124,92,231,0.12)' : 'transparent',
      color: active ? 'var(--accent)' : 'var(--text-secondary)',
      fontWeight: active ? 600 : 400, transition: '0.2s',
    }),
    stat: {
      padding: '1rem', borderRadius: 10, background: 'var(--bg-secondary)',
      border: '1px solid var(--border)', textAlign: 'center',
    },
    badge: (color) => ({
      display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: 12,
      fontSize: '0.72rem', fontWeight: 600, background: `${color}18`, color,
    }),
  }

  return (
    <div>
      <div className="grid-2 mb-15">
        {/* 关键词输入 */}
        <div className="card">
          <div className="card-title">搜索关键词</div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0 0 0.75rem' }}>
            每行一个关键词，系统会在选中的平台上搜索这些关键词并采集内容
          </p>
          <textarea
            value={keywordText}
            onChange={e => setKeywordText(e.target.value)}
            rows={6}
            placeholder="XX大学 食堂&#10;XX大学 宿舍&#10;XX大学 考研"
            style={s.input}
          />
          <div style={{ marginTop: '0.6rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button style={{ ...s.chip(false), fontSize: '0.75rem' }} onClick={addPresetKeywords}>
              + 填入预设校园关键词
            </button>
            <button style={{ ...s.chip(false), fontSize: '0.75rem' }}
              onClick={() => setKeywordText('')}>
              清空
            </button>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: '2' }}>
              当前 {keywordText.split('\n').filter(k => k.trim()).length} 个关键词
            </span>
          </div>
        </div>

        {/* 平台选择 + 参数 */}
        <div className="card">
          <div className="card-title">采集平台</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.2rem' }}>
            {PLATFORMS.map(p => (
              <div key={p.code} onClick={() => togglePlatform(p.code)} style={s.chip(selectedPlatforms.includes(p.code))}>
                {p.name}
              </div>
            ))}
          </div>

          <div className="card-title" style={{ marginTop: 0 }}>采集参数</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem' }}>每平台最大采集数</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input type="range" min={5} max={50} step={5} value={maxNotes}
                  onChange={e => setMaxNotes(Number(e.target.value))}
                  style={{ width: 120, accentColor: 'var(--accent)' }} />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, minWidth: 28, textAlign: 'right' }}>{maxNotes}</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '0.85rem' }}>显示浏览器窗口</span>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', margin: '0.15rem 0 0' }}>
                  首次使用需开启以扫码登录，之后可关闭
                </p>
              </div>
              <label style={{ position: 'relative', display: 'inline-block', width: 44, height: 24 }}>
                <input type="checkbox" checked={!headless}
                  onChange={e => setHeadless(!e.target.checked)}
                  style={{ opacity: 0, width: 0, height: 0 }} />
                <span style={{
                  position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
                  background: !headless ? 'var(--accent)' : 'var(--border)',
                  borderRadius: 12, transition: '0.3s',
                }}>
                  <span style={{
                    position: 'absolute', height: 18, width: 18, left: !headless ? 22 : 3, bottom: 3,
                    background: 'white', borderRadius: '50%', transition: '0.3s',
                  }} />
                </span>
              </label>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem' }}>自动情感分析并入库</span>
              <label style={{ position: 'relative', display: 'inline-block', width: 44, height: 24 }}>
                <input type="checkbox" checked={importing}
                  onChange={e => setImporting(e.target.checked)}
                  style={{ opacity: 0, width: 0, height: 0 }} />
                <span style={{
                  position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
                  background: importing ? 'var(--accent)' : 'var(--border)',
                  borderRadius: 12, transition: '0.3s',
                }}>
                  <span style={{
                    position: 'absolute', height: 18, width: 18, left: importing ? 22 : 3, bottom: 3,
                    background: 'white', borderRadius: '50%', transition: '0.3s',
                  }} />
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* 启动按钮 */}
      <div style={{ marginBottom: '1.5rem' }}>
        <button
          className="btn btn-primary"
          onClick={handleCrawl}
          disabled={crawling}
          style={{ padding: '0.75rem 2.5rem', fontSize: '0.95rem', fontWeight: 600 }}
        >
          {crawling ? '采集中...请耐心等待（可能需要 1~5 分钟）' : '开始采集'}
        </button>
        {crawling && (
          <p style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            系统正在各平台搜索关键词并采集内容，首次使用会弹出浏览器窗口让你扫码登录
          </p>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="card" style={{ borderColor: '#ff4757', marginBottom: '1rem' }}>
          <div style={{ color: '#ff4757', fontWeight: 600, fontSize: '0.9rem' }}>采集失败</div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>{error}</p>
        </div>
      )}

      {/* 采集结果 */}
      {result && (
        <div className="card mb-15">
          <div className="card-title">采集结果</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
            <div style={s.stat}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent)' }}>
                {result.crawl_result?.total_items || 0}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>采集内容数</div>
            </div>
            <div style={s.stat}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#00c48c' }}>
                {result.import_result?.imported || 0}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>入库记录数</div>
            </div>
            <div style={s.stat}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#ffa502' }}>
                {result.import_result?.alerts_created || 0}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>风险预警数</div>
            </div>
            <div style={s.stat}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {result.keywords_used?.length || 0}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>搜索关键词</div>
            </div>
          </div>

          {/* 各平台详情 */}
          {result.crawl_result?.platform_results && (
            <div>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '0.5rem' }}>平台详情</div>
              {Object.entries(result.crawl_result.platform_results).map(([plat, r]) => (
                <div key={plat} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '0.6rem 0', borderBottom: '1px solid var(--border)',
                  fontSize: '0.82rem',
                }}>
                  <span style={{ fontWeight: 500 }}>{r.platform_name || plat}</span>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <span>{r.items_count || 0} 条内容</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{r.duration_seconds || 0}s</span>
                    <span style={s.badge(r.success ? '#00c48c' : '#ff4757')}>
                      {r.success ? '成功' : '失败'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 采集历史 */}
      {/* 数据管理 */}
      <div className="card mb-15">
        <div className="card-title">数据管理</div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
          清空数据库中的所有记录（包括 generate_data.py 生成的测试数据和之前采集的数据），
          清空后前端所有页面只展示你重新采集的真实数据。
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            onClick={handleClear}
            disabled={clearing || crawling}
            style={{
              padding: '0.5rem 1.5rem', fontSize: '0.85rem', fontWeight: 600,
              background: '#ff475720', color: '#ff4757', border: '1.5px solid #ff4757',
              borderRadius: 8, cursor: clearing ? 'not-allowed' : 'pointer',
            }}
          >
            {clearing ? '清空中...' : '清空所有数据'}
          </button>
          {clearResult && (
            <span style={{ fontSize: '0.8rem', color: '#00c48c' }}>
              {clearResult.message || `已清空: sentiment_records ${clearResult.deleted?.sentiment_records || 0} 条, alerts ${clearResult.deleted?.alerts || 0} 条`}
            </span>
          )}
        </div>
      </div>

      {history.length > 0 && (
        <div className="card">
          <div className="card-title">本次会话采集历史</div>
          <table style={{ width: '100%', fontSize: '0.8rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                <th style={{ padding: '0.4rem 0', fontWeight: 500 }}>时间</th>
                <th style={{ padding: '0.4rem 0', fontWeight: 500 }}>关键词数</th>
                <th style={{ padding: '0.4rem 0', fontWeight: 500 }}>平台</th>
                <th style={{ padding: '0.4rem 0', fontWeight: 500 }}>采集数</th>
                <th style={{ padding: '0.4rem 0', fontWeight: 500 }}>入库数</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h, i) => (
                <tr key={i} style={{ borderTop: '1px solid var(--border)' }}>
                  <td style={{ padding: '0.5rem 0' }}>{h.time}</td>
                  <td>{h.keywords}</td>
                  <td>{h.platforms}</td>
                  <td style={{ fontWeight: 600 }}>{h.items}</td>
                  <td style={{ fontWeight: 600, color: '#00c48c' }}>{h.imported}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
