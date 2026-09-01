import BrandMark from '../components/BrandMark'

const CAPABILITIES = [
  { code: 'DATA IN', title: '上传前先看懂报表', copy: '支持 CSV、XLSX 和 XLS。系统先识别表头、数据类型与代表性样例，你确认字段后才正式生成分析数据。' },
  { code: 'BUSINESS', title: '把流水变成经营判断', copy: '营收、订单、客单价、时段和趋势集中呈现，让门店先知道发生了什么，再决定今天做什么。' },
  { code: 'PRODUCT', title: '找到菜品与顾客机会', copy: '从商品排行、套餐关联到 RFM 用户分层，找到值得主推的菜、需要唤回的人和更合适的组合。' },
  { code: 'RISK', title: '异常与预测都有依据', copy: '筛查金额、数量、折扣和组合异常，保留人工复核结果；通过时间回测选择更合适的营收预测方法。' },
  { code: 'REPORT', title: '形成可带走的经营报告', copy: '把指标、异常和建议整理成经营诊断，支持本地生成或调用已配置的 AI，并可导出 Markdown、Word 与 PDF。' },
  { code: 'PUBLISH', title: '从分析走到内容增长', copy: '用 AI 起草抖音、小红书和微博文案，预览后交接到官方页面；发布完成再记录公开数据，形成作品复盘。' }
]

const WORKFLOW = [
  ['01', '导入订单报表', '先预检文件结构，不直接覆盖现有数据'],
  ['02', '确认字段含义', 'AI 与规则给出建议，关键映射由你决定'],
  ['03', '查看经营全景', '概览、商品、用户、异常、预测与报告同步生成'],
  ['04', '把经营动作写成内容', '生成平台文案，在真实发布页面完成素材与账号确认'],
  ['05', '记录表现，再做下一条', '保存公开指标与复盘结论，持续比较内容效果']
]

export default function LandingPage({ onAuth }) {
  return <main className="landing-page">
    <header className="landing-header">
      <a className="landing-brand" href="/zh" onClick={event => { event.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}><BrandMark variant="square" /><span><b>懂单儿</b><small>RODAS · 餐饮经营分析与内容增长系统</small></span></a>
      <nav className="landing-nav" aria-label="页面导航"><a href="#capabilities">能力全景</a><a href="#workflow">经营闭环</a><a href="#trust">数据边界</a><a href="#for-who">适用门店</a></nav>
      <div className="landing-actions"><button className="landing-login" type="button" onClick={() => onAuth('login')}>登录</button><button className="landing-signup" type="button" onClick={() => onAuth('register')}>免费开始 <span>↗</span></button></div>
    </header>

    <section className="landing-hero">
      <div className="landing-hero-copy">
        <p className="landing-kicker">RODAS / FROM ORDER TO ACTION</p>
        <h1>把一张订单表，<br /><em>走成一轮经营闭环。</em></h1>
        <p className="landing-lede">懂单儿把平台报表整理成经营判断，再把判断变成内容行动。你可以从数据上传一路完成分析、发布和复盘，不再让报表停在“看过”。</p>
        <div className="landing-hero-actions"><button className="landing-cta" type="button" onClick={() => onAuth('register')}>创建我的经营台 <span>→</span></button><a className="landing-text-link" href="#workflow">查看完整流程 <span>↓</span></a></div>
        <div className="landing-proof"><span>字段先确认再分析</span><i /><span>AI 可选，不影响本地分析</span><i /><span>发布始终由你最终确认</span></div>
      </div>

      <div className="landing-loop-board" aria-label="懂单儿经营闭环演示">
        <header><span>DEMO / 本次经营闭环</span><b><i /> 数据已就绪</b></header>
        <div className="landing-loop-list">
          <article><em>01</em><span><small>订单进入</small><strong>12,486 笔订单完成整理</strong></span><b>已确认</b></article>
          <article><em>02</em><span><small>经营判断</small><strong>晚市套餐存在增长机会</strong></span><b>+12.8%</b></article>
          <article><em>03</em><span><small>内容行动</small><strong>抖音 · 小红书 · 微博</strong></span><b>待发布</b></article>
          <article><em>04</em><span><small>作品复盘</small><strong>保存公开表现与下一步建议</strong></span><b>持续记录</b></article>
        </div>
        <aside><span>今天先做什么</span><strong>把晚市套餐写成一条本地生活内容</strong><small>依据：18:00—21:00 客单价上升，双人套餐关联度较高。</small></aside>
        <footer><span>数据</span><i>→</i><span>判断</span><i>→</i><span>发布</span><i>→</i><span>复盘</span></footer>
      </div>
    </section>

    <div className="landing-platform-strip"><span>一套工作台，连接经营与内容</span><b>CSV / Excel</b><b>DeepSeek / 豆包 / OpenAI / Gemini</b><b>抖音 / 小红书 / 微博</b><b>PublishLoop 发布桥接</b></div>

    <section className="landing-section" id="capabilities">
      <div className="landing-section-heading"><div><p className="landing-kicker">WHAT RODAS DOES</p><h2>不只告诉你数字，<br />还把下一步接起来。</h2></div><p className="landing-section-note">从数据清洗到内容复盘，九个工作板块共享同一份经过确认的数据。</p></div>
      <div className="landing-feature-grid">{CAPABILITIES.map(item => <article key={item.code}><span>{item.code}</span><h3>{item.title}</h3><p>{item.copy}</p></article>)}</div>
    </section>

    <section className="landing-workflow" id="workflow">
      <div className="landing-workflow-intro"><p className="landing-kicker">ONE OPERATING LOOP</p><h2>每一步都能核对，<br />每次行动都有回路。</h2><p>系统不会跳过你的判断：字段由你确认，异常由你复核，文案由你核对，账号、素材和最终发布仍在官方平台完成。</p><button className="landing-outline" type="button" onClick={() => onAuth('register')}>从第一张报表开始 <span>↗</span></button></div>
      <div className="landing-steps">{WORKFLOW.map(([index, title, detail]) => <div key={index}><b>{index}</b><span><strong>{title}</strong><small>{detail}</small></span></div>)}</div>
    </section>

    <section className="landing-trust" id="trust">
      <header><p className="landing-kicker">CLEAR BOUNDARIES</p><h2>自动化做辅助，<br />关键决定留给你。</h2><p>懂单儿只处理完成分析和内容交接所需的数据，不接管平台账号，也不会代替你完成最终发布。</p></header>
      <div className="landing-trust-grid">
        <article><span>订单数据</span><h3>按账户隔离保存</h3><p>上传前先预检，确认字段后再生成数据集；报表和分析结果不会混入其他账户。</p></article>
        <article><span>AI 服务</span><h3>你选择是否接入</h3><p>未配置 AI 时仍可使用内置规则和本地报告；密钥保存在当前浏览器，不进入发布文案。</p></article>
        <article><span>平台发布</span><h3>只交接公开文案</h3><p>标题、正文和话题交给浏览器扩展；账号、Cookie、本地素材与发布确认留在官方页面。</p></article>
      </div>
    </section>

    <section className="landing-audience" id="for-who"><div><p className="landing-kicker">BUILT FOR DAILY OPERATIONS</p><h2>给每天都在做决定的人。</h2></div><div className="audience-notes"><p><b>单店老板</b><span>快速看懂今天的生意，并知道下一步先改什么。</span></p><p><b>门店运营</b><span>把商品、顾客与时段机会变成可执行的营销内容。</span></p><p><b>餐饮团队</b><span>让分析、复核、发布和复盘在同一套工作流里留痕。</span></p></div></section>

    <section className="landing-final"><p className="landing-kicker">START WITH ONE FILE</p><h2>从下一张报表开始，<br />让每次行动都有依据。</h2><p>上传一份脱敏订单文件，先看看懂单儿能读出什么。</p><button className="landing-cta" type="button" onClick={() => onAuth('register')}>免费创建经营台 <span>→</span></button></section>
    <footer className="landing-footer"><span>懂单儿 · RODAS</span><span>经营分析 · 内容发布 · 作品复盘</span><span>© 2026 莫永信</span></footer>
  </main>
}
