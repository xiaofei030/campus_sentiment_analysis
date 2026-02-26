import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { fetchOverview, fetchSentimentTrend, fetchEmotions } from '../services/dashboardApi'

// 正面/负面/中性情绪词库
const POS_WORDS = new Set(['喜悦', '兴奋', '满足', '自豪', '感恩', '期待', '轻松', '幸福', '希望', '快乐', '开心', '高兴', '愉快', '振奋'])
const NEG_WORDS = new Set(['焦虑', '压力', '沮丧', '迷茫', '孤独', '恐惧', '愤怒', '失望', '无助', '悲伤', '烦躁', '紧张', '担忧', '不安', '郁闷'])
const NEU_WORDS = new Set(['平静', '一般', '无感', '淡定', '正常', '平常', '普通'])

export default function SentimentPage() {
  const [overview, setOverview] = useState(null)
  const [trend, setTrend] = useState([])
  const [emotions, setEmotions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const [ov, tr, em] = await Promise.all([
          fetchOverview(7), fetchSentimentTrend(7), fetchEmotions(30)
        ])
        setOverview(ov); setTrend(tr || []); setEmotions(em || [])
      } catch (e) { console.error(e) }
      finally { setLoading(false) }
    })()
  }, [])

  if (loading) return <div className="page-loading"><div className="spinner" /><p>加载中...</p></div>

  const total = overview?.total_records || 1
  const pieData = [
    { name: '正面', value: overview?.positive_count || 0, color: '#70a1ff' },
    { name: '负面', value: overview?.negative_count || 0, color: '#ff6b81' },
    { name: '中性', value: overview?.neutral_count || 0, color: '#ffa502' },
  ]

  // 分类高频词 - 优先从词库匹配，剩余按情感比例分配
  const posEmotions = emotions.filter(e => POS_WORDS.has(e.word)).slice(0, 6)
  const negEmotions = emotions.filter(e => NEG_WORDS.has(e.word)).slice(0, 6)
  const neuEmotions = emotions.filter(e => NEU_WORDS.has(e.word)).slice(0, 4)

  // 如果分类结果太少，用未分类词填充
  const classified = new Set([...posEmotions, ...negEmotions, ...neuEmotions].map(e => e.word))
  const unclassified = emotions.filter(e => !classified.has(e.word))
  while (posEmotions.length < 3 && unclassified.length > 0) posEmotions.push(unclassified.shift())
  while (negEmotions.length < 3 && unclassified.length > 0) negEmotions.push(unclassified.shift())
  while (neuEmotions.length < 2 && unclassified.length > 0) neuEmotions.push(unclassified.shift())

  // 周趋势数据
  const weekTrend = trend.map(d => ({
    ...d,
    positive_rate: d.total > 0 ? Math.round(d.positive / d.total * 100) : 0,
    negative_rate: d.total > 0 ? Math.round(d.negative / d.total * 100) : 0,
  }))

  return (
    <div>
      {/* 统计卡片 */}
      <div className="stat-cards-row mb-15">
        <div className="stat-card">
          <div>
            <div className="stat-label">总记录数</div>
            <div className="stat-value">{overview?.total_records?.toLocaleString() || 0}</div>
          </div>
          <span className="stat-icon">📊</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">正面情感</div>
            <div className="stat-value" style={{ color: '#70a1ff' }}>
              {overview?.total_records ? Math.round(overview.positive_count / overview.total_records * 100) : 0}%
            </div>
          </div>
          <span className="stat-icon">😊</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">负面情感</div>
            <div className="stat-value" style={{ color: '#ff6b81' }}>{overview?.negative_rate || 0}%</div>
          </div>
          <span className="stat-icon">😟</span>
        </div>
        <div className="stat-card">
          <div>
            <div className="stat-label">情绪词汇量</div>
            <div className="stat-value">{emotions.length}</div>
          </div>
          <span className="stat-icon">💬</span>
        </div>
      </div>

      {/* 整体分布 + 周趋势 */}
      <div className="grid-2 mb-15">
        <div className="card">
          <div className="card-title">整体情感分布</div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '0.5rem', fontSize: '0.8rem' }}>
            {pieData.map((p, i) => (
              <span key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <span style={{ width: 10, height: 10, background: p.color, borderRadius: 2 }} />
                {p.name} {Math.round(p.value / total * 100)}%
              </span>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={110} dataKey="value"
                label={({ name, value }) => `${name} ${Math.round(value / total * 100)}%`}
                labelLine={{ stroke: 'var(--text-secondary)' }}>
                {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">情感趋势(周)</div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={weekTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" stroke="var(--text-secondary)" tick={{ fontSize: 11 }}
                tickFormatter={v => {
                  const d = new Date(v)
                  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
                }} />
              <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 11 }} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Legend />
              <Line type="monotone" dataKey="positive_rate" name="正面%" stroke="#70a1ff" strokeWidth={2.5} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="negative_rate" name="负面%" stroke="#ff6b81" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 高频词 */}
      <div className="grid-1-1-1">
        <div className="card">
          <div className="card-title">正面高频词</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', padding: '0.5rem 0' }}>
            {posEmotions.map((e, i) => (
              <span key={i} style={{
                fontSize: '1.1rem', color: '#00c48c',
                padding: '0.3rem 0.6rem', background: 'rgba(0,196,140,0.08)', borderRadius: 6,
              }}>
                {e.word}
                <span style={{ fontSize: '0.7rem', marginLeft: 4, opacity: 0.7 }}>{e.count}</span>
              </span>
            ))}
            {posEmotions.length === 0 && <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>暂无数据</span>}
          </div>
        </div>

        <div className="card">
          <div className="card-title">负面高频词</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', padding: '0.5rem 0' }}>
            {negEmotions.map((e, i) => (
              <span key={i} style={{
                fontSize: '1.1rem', color: '#ff4757',
                padding: '0.3rem 0.6rem', background: 'rgba(255,71,87,0.08)', borderRadius: 6,
              }}>
                {e.word}
                <span style={{ fontSize: '0.7rem', marginLeft: 4, opacity: 0.7 }}>{e.count}</span>
              </span>
            ))}
            {negEmotions.length === 0 && <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>暂无数据</span>}
          </div>
        </div>

        <div className="card">
          <div className="card-title">中性高频词</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', padding: '0.5rem 0' }}>
            {neuEmotions.map((e, i) => (
              <span key={i} style={{
                fontSize: '1.1rem', color: '#70a1ff',
                padding: '0.3rem 0.6rem', background: 'rgba(112,161,255,0.08)', borderRadius: 6,
              }}>
                {e.word}
                <span style={{ fontSize: '0.7rem', marginLeft: 4, opacity: 0.7 }}>{e.count}</span>
              </span>
            ))}
            {neuEmotions.length === 0 && <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>暂无数据</span>}
          </div>
        </div>
      </div>
    </div>
  )
}
