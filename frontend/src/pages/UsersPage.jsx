import { Card, DataTable, money, num } from '../components/ui'

const pct = value => `${Number(value || 0).toFixed(1)}%`

const SEGMENT_META = {
  '重要价值': { tone: 'vip', detail: '近期活跃、频次和贡献都高', action: '会员维护' },
  '潜力客户': { tone: 'potential', detail: '已经活跃，值得推动客单升级', action: '引导升级' },
  '重要保持': { tone: 'keep', detail: '贡献不错，但最近消费变少', action: '降低复购门槛' },
  '新客户': { tone: 'new', detail: '刚完成消费，等待第二次购买', action: '推动二次消费' },
  '重要挽留': { tone: 'recall', detail: '过去贡献高，近期开始沉默', action: '本周召回' },
  '一般价值': { tone: 'normal', detail: '消费贡献一般，适合低成本触达', action: '常规运营' },
  '流失高价值': { tone: 'risk', detail: '高价值顾客，当前流失风险最高', action: '优先挽回' },
  '流失客户': { tone: 'lost', detail: '长期未消费，先控制触达成本', action: '低成本唤回' },
  '普通客户': { tone: 'normal', detail: '保持稳定触达，观察是否升级', action: '保持触达' }
}

function getMeta(segment) {
  return SEGMENT_META[segment] || { tone: 'normal', detail: '根据当前消费行为持续观察', action: '保持触达' }
}

function countOf(rows, segment) {
  return Number(rows.find(row => row.segment === segment)?.count || 0)
}

function clusterTone(row, medianRecency, medianFrequency) {
  const recent = Number(row.recency || 0) <= medianRecency
  const frequent = Number(row.frequency || 0) >= medianFrequency
  if (recent && frequent) return '最近常来'
  if (recent) return '刚来过'
  if (frequent) return '以前常来'
  return '偶尔来'
}

function recentText(value) {
  const days = Math.round(Number(value || 0))
  return days <= 1 ? '刚刚来过' : `约 ${days} 天前`
}

function clusterGuidance(tone) {
  if (tone === '最近常来') return { title: '常来顾客', intro: '最近还在持续消费，关系保持得很好。', action: '继续保持体验，可尝试会员权益。', tone: 'positive' }
  if (tone === '刚来过') return { title: '刚消费过', intro: '刚完成消费，下一次购买还没有形成习惯。', action: '3–7 天后提醒再次到店。', tone: 'new' }
  if (tone === '以前常来') return { title: '沉默顾客', intro: '过去来得勤，最近一段时间没有回来。', action: '发一张回归优惠，邀请再次到店。', tone: 'warning' }
  return { title: '偶尔到店', intro: '消费时间不固定，暂时还看不出稳定习惯。', action: '用低成本内容保持联系。', tone: 'neutral' }
}

function priorityReason(segment) {
  if (segment === '流失高价值') return '过去贡献高，先把关系拉回来，避免继续流失。'
  if (segment === '重要挽留') return '以前消费不错，降低门槛更容易让他回来。'
  if (segment === '潜力客户') return '已经有消费兴趣，可以用组合优惠提高客单。'
  return '先用轻量触达验证需求，再决定投入多少。'
}

function SegmentPreferenceList({ rows = [] }) {
  if (!rows.length) return <div className="users-empty-state"><strong>暂无消费时间偏好。</strong><span>订单积累到可识别时段后，会自动生成触达建议。</span></div>
  return <div className="users-preference-list">{rows.map(row => { const meta = getMeta(row.segment); return <article className={`users-preference-row tone-${meta.tone}`} key={row.segment}><div className="users-preference-person"><i /><span><strong>{row.segment}</strong><small>{num(row.customer_count)} 位顾客</small></span></div><dl><div><dt>常来时段</dt><dd>{row.peak_visit || '暂不明显'}</dd></div><div><dt>常购商品</dt><dd>{row.favorite_product || '暂不明显'}</dd></div><div><dt>平均每单</dt><dd>{money(row.avg_order_value)}</dd></div><div className="is-contact"><dt>建议触达</dt><dd>{row.contact_time || '按需联系'}</dd></div></dl><div className="users-preference-action"><span>推荐做法</span><strong>{row.recommendation || row.offer_strategy}</strong><small>{row.offer_strategy}</small></div></article> })}</div>
}

export default function UsersPage({ users }) {
  const rfm = users?.rfm || []
  const segments = users?.segments || []
  const clusters = users?.clusters || []
  const preferences = users?.preferences || []
  const totalUsers = rfm.length
  const totalSpend = rfm.reduce((sum, row) => sum + Number(row.monetary || 0), 0)
  const avgSpend = totalUsers ? totalSpend / totalUsers : 0
  const repeatUsers = rfm.filter(row => Number(row.frequency || 0) > 1).length
  const activeUsers = rfm.filter(row => Number(row.recency || 0) <= 30).length
  const highValue = countOf(segments, '重要价值') + countOf(segments, '潜力客户')
  const recall = countOf(segments, '重要挽留') + countOf(segments, '流失高价值')
  const topCustomer = [...rfm].sort((a, b) => Number(b.monetary || 0) - Number(a.monetary || 0))[0]
  const topSegment = segments[0]
  const segmentMax = Math.max(...segments.map(row => Number(row.count || 0)), 1)
  const activeRate = totalUsers ? activeUsers / totalUsers * 100 : 0
  const repeatRate = totalUsers ? repeatUsers / totalUsers * 100 : 0
  const highValueRate = totalUsers ? highValue / totalUsers * 100 : 0
  const medianRecency = rfm.length ? [...rfm].map(row => Number(row.recency || 0)).sort((a, b) => a - b)[Math.floor(rfm.length / 2)] : 0
  const medianFrequency = rfm.length ? [...rfm].map(row => Number(row.frequency || 0)).sort((a, b) => a - b)[Math.floor(rfm.length / 2)] : 0

  const priorities = [
    { segment: '流失高价值', label: '立即触达', text: '专属回归券 + 人工联系', tone: 'risk', reason: priorityReason('流失高价值') },
    { segment: '重要挽留', label: '本周唤回', text: '降低复购门槛，给出明确回归理由', tone: 'recall', reason: priorityReason('重要挽留') },
    { segment: '潜力客户', label: '推动升级', text: '用高客单新品和组合优惠承接兴趣', tone: 'potential', reason: priorityReason('潜力客户') }
  ].map(item => ({ ...item, count: countOf(segments, item.segment) })).filter(item => item.count > 0)
  if (topSegment && priorities.length < 3 && !priorities.some(item => item.segment === topSegment.segment)) {
    priorities.push({ segment: topSegment.segment, label: '规模最大', text: getMeta(topSegment.segment).action, tone: getMeta(topSegment.segment).tone, reason: priorityReason(topSegment.segment), count: Number(topSegment.count || 0) })
  }

  return <main className="users-page">
    <section className="users-heading">
      <div><p className="eyebrow">04 / CUSTOMER LENS</p><h2>用户分析</h2><p>不是把顾客分成几类，而是找出下一次最值得触达的人。</p></div>
      <div className="users-heading-note"><span>用户分层</span><strong>{num(totalUsers)} 位顾客</strong><small>{users ? '按消费行为整理' : '上传订单后生成'}</small></div>
    </section>

    <section className="users-hero">
      <div className="users-hero-copy"><span className="users-kicker">THE NEXT CUSTOMER MOVE</span><h3>{recall > 0 ? <>先召回 <em>{num(recall)}</em> 位高价值顾客</> : highValue > 0 ? <>先经营 <em>{num(highValue)}</em> 位高价值顾客</> : '等待顾客数据进入'}</h3><p>{recall > 0 ? '他们曾经贡献过营收，只是最近没有回来。把预算先放在这批人身上，比向所有顾客群发更有把握。' : '系统会根据顾客最近来店、消费次数和累计消费，找出最值得投入的顾客群。'}</p><div className="users-hero-tags"><span>最近有没有来过</span><span>来过几次</span><span>一共花了多少</span></div></div>
      <div className="users-hero-side"><div className="users-hero-ring"><strong>{pct(activeRate)}</strong><span>近 30 天仍活跃</span></div><div className="users-hero-leader"><small>当前贡献最高</small><b>{topCustomer ? `用户 ${topCustomer.customer_id}` : '—'}</b><span>{topCustomer ? `累计消费 ${money(topCustomer.monetary)}` : '等待数据'}</span></div></div>
    </section>

    <section className="users-stat-row"><div><span>消费顾客</span><strong>{num(totalUsers)}</strong><small>参与当前周期消费</small></div><div><span>复购顾客</span><strong>{num(repeatUsers)}</strong><small>复购率 {pct(repeatRate)}</small></div><div><span>高价值用户</span><strong>{num(highValue)}</strong><small>重要价值 + 潜力客户</small></div><div className={recall > 0 ? 'is-alert' : ''}><span>召回优先级</span><strong>{num(recall)}</strong><small>重要挽留 + 流失高价值</small></div></section>

    <section className="users-main-grid">
      <Card className="users-segment-card" title="用户价值地图" subtitle="把最近一次消费、消费频次和金额翻译成触达优先级。" action={<span className="users-card-tag">RFM 分层</span>}>
        {segments.length ? <div className="users-segment-list">{segments.map((row, index) => { const segment = String(row.segment || '未命名分层'); const meta = getMeta(segment); const count = Number(row.count || 0); return <div className={`users-segment-row tone-${meta.tone}`} key={`${segment}-${index}`}><div className="users-segment-main"><i className="users-segment-dot" /><span><strong>{segment}</strong><small>{meta.detail}</small></span></div><b>{num(count)}<small>{pct(totalUsers ? count / totalUsers * 100 : 0)}</small></b><div className="users-segment-track"><i style={{ width: `${count / segmentMax * 100}%` }} /></div><span className="users-segment-action">{meta.action}</span></div> })}</div> : <div className="users-empty-state"><strong>上传订单后，这里会出现用户价值地图。</strong><span>系统会自动计算 RFM 分层，并把结果翻译成运营动作。</span></div>}
      </Card>

      <Card className="users-playbook-card" title="今天先做什么" subtitle="把分层结果直接变成一张触达清单。">
        <div className="users-playbook-list">{priorities.length ? priorities.slice(0, 3).map((item, index) => <div className={`users-playbook-item tone-${item.tone}`} key={item.segment}><span className="users-playbook-index">{String(index + 1).padStart(2, '0')}</span><span><strong>{item.segment}<em>{item.label}</em></strong><small>{item.text}</small><span className="users-playbook-why">{item.reason}</span></span><b>{num(item.count)}<small>人</small></b></div>) : <div className="users-empty-state compact"><strong>暂时没有召回优先级。</strong><span>上传订单后，系统会根据用户最近消费和贡献自动生成建议。</span></div>}</div>
        {priorities.length > 0 && <div className="users-playbook-strategy"><div><span>执行顺序</span><strong>先召回，再维护，最后升级</strong></div><p>先处理红色标签的人群；完成触达后，再安排会员维护，最后把优惠给到有升级潜力的顾客。</p></div>}
      </Card>
    </section>

    <Card className="users-preferences-card" title="什么时候联系这群顾客" subtitle="不展示复杂热力图，直接告诉你每类顾客常来时间、常购商品和建议触达时机。" action={<span className="users-card-tag">触达时机</span>}><SegmentPreferenceList rows={preferences} /></Card>

    <section className="users-insight-grid">
      <Card className="users-cluster-card" title="顾客最近的状态" subtitle="系统把消费习惯相近的人放在一起，方便你决定下一步怎么联系。">
        {clusters.length ? <div className="users-cluster-grid">{clusters.slice(0, 6).map((row, index) => { const tone = clusterTone(row, medianRecency, medianFrequency); const profile = clusterGuidance(tone); return <div className={`users-cluster-item tone-${profile.tone}`} key={`${row.cluster}-${index}`}><div className="users-cluster-item-top"><span>行为状态</span><strong>{profile.title}</strong></div><div className="users-cluster-count"><b>{num(row.count)}</b><span>位顾客</span></div><p className="users-cluster-intro">{profile.intro}</p><div className="users-cluster-stats"><div><span>上次消费</span><strong>{recentText(row.recency)}</strong></div><div><span>平均消费次数</span><strong>{num(row.frequency)} 次</strong></div><div><span>人均消费金额</span><strong>{money(row.monetary)}</strong></div></div><p className="users-cluster-guidance"><span>下一步</span>{profile.action}</p></div>})}</div> : <div className="users-empty-state"><strong>暂无顾客状态。</strong><span>上传订单后，系统会按消费行为自动整理。</span></div>}
      </Card>
      <Card className="users-signal-card" title="复购与召回信号" subtitle="先看顾客是否回来，再决定优惠应该给谁。">
        <div className="users-signal-list"><div><div><span>近 30 天活跃</span><b>{num(activeUsers)}<small>人 · {pct(activeRate)}</small></b></div><i><em style={{ width: `${activeRate}%` }} /></i></div><div><div><span>发生过复购</span><b>{num(repeatUsers)}<small>人 · {pct(repeatRate)}</small></b></div><i><em style={{ width: `${repeatRate}%` }} /></i></div><div><div><span>高价值占比</span><b>{num(highValue)}<small>人 · {pct(highValueRate)}</small></b></div><i><em className="signal-hot" style={{ width: `${highValueRate}%` }} /></i></div></div><div className="users-signal-summary"><span>顾客平均累计消费</span><strong>{money(avgSpend)}</strong><small>按用户汇总实付金额计算</small></div></Card>
    </section>

    <details className="users-details"><summary><span>查看用户价值明细</span><small>搜索、排序和分页 · {num(totalUsers)} 位顾客</small></summary><DataTable rows={rfm} columns={[['customer_id', '用户'], ['recency', '最近消费'], ['frequency', '频次'], ['monetary', '金额'], ['RFM_score', '总分'], ['segment', '分层'], ['strategy', '策略']]} /></details>
    <details className="users-details"><summary><span>查看分析依据</span><small>分群计算与参考数据</small></summary><div className="users-model-grid"><div><h3>顾客群参考</h3><DataTable rows={clusters} searchable={false} columns={[["cluster", "顾客群"], ["recency", "最近消费"], ["frequency", "消费次数"], ["monetary", "累计消费"], ["count", "人数"]]} /></div><div><h3>分群数量参考</h3><DataTable rows={users?.elbow || []} searchable={false} columns={[["k", "顾客群数量"], ["inertia", "参考值"]]} /></div></div></details>
  </main>
}
