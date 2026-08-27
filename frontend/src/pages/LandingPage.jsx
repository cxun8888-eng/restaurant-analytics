import BrandMark from '../components/BrandMark'

export default function LandingPage({ onAuth }) {
  return <main className="landing-page">
    <header className="landing-header">
      <a className="landing-brand" href="/zh" onClick={event => { event.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}><BrandMark variant="square" /><span><b>懂单儿</b><small>RODAS · 餐饮订单数据分析系统</small></span></a>
      <nav className="landing-nav" aria-label="页面导航"><a href="#capabilities">产品能力</a><a href="#workflow">分析流程</a><a href="#for-who">适用门店</a></nav>
      <div className="landing-actions"><button className="landing-login" type="button" onClick={() => onAuth('login')}>登录</button><button className="landing-signup" type="button" onClick={() => onAuth('register')}>免费开始 <span>↗</span></button></div>
    </header>

    <section className="landing-hero">
      <div className="landing-hero-copy"><p className="landing-kicker">RODAS / RESTAURANT ORDER DATA ANALYSIS</p><h1>把平台报表，<br /><em>变成看得懂的经营答案。</em></h1><p className="landing-lede">懂单儿把一份平台订单报表整理成经营地图，从字段识别到经营洞察，让每一次上传都落到下一步行动。</p><div className="landing-hero-actions"><button className="landing-cta" type="button" onClick={() => onAuth('register')}>开始整理订单 <span>→</span></button><a className="landing-text-link" href="#workflow">看看它如何工作 <span>↓</span></a></div><div className="landing-proof"><span>支持主流平台导出</span><i /> <span>智能识别表头</span><i /> <span>数据留在你的账户</span></div></div>
      <div className="landing-ledger" aria-label="经营数据预览"><div className="ledger-top"><span>经营信号 / 2026.08</span><b>本月</b></div><div className="ledger-main"><div><small>本月实收</small><strong>¥128,640</strong><span className="ledger-up">↑ 12.8%</span></div><svg viewBox="0 0 380 150" role="img" aria-label="营业额趋势"><defs><linearGradient id="landing-area" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#a7d2bc" stopOpacity=".32" /><stop offset="1" stopColor="#a7d2bc" stopOpacity="0" /></linearGradient></defs><path d="M0 128 C26 115 41 121 63 96 S101 112 125 79 S162 92 188 58 S222 84 248 54 S285 66 308 30 S345 44 380 13 V150 H0Z" fill="url(#landing-area)" /><path d="M0 128 C26 115 41 121 63 96 S101 112 125 79 S162 92 188 58 S222 84 248 54 S285 66 308 30 S345 44 380 13" fill="none" stroke="#b8ddc8" strokeWidth="3" strokeLinecap="round" /></svg></div><div className="ledger-bottom"><span><b>1,248</b><small>订单数</small></span><span><b>¥103</b><small>平均客单价</small></span><span><b>32</b><small>经营信号</small></span></div><div className="ledger-tabs"><span className="active">当前平台</span><span>美团</span><span>饿了么</span><span>微信</span></div></div>
    </section>

    <div className="landing-platform-strip"><span>一份平台报表，也能看见完整经营</span><b>美团</b><b>饿了么</b><b>微信小程序</b><b>CSV / Excel</b></div>

    <section className="landing-section" id="capabilities"><div className="landing-section-heading"><p className="landing-kicker">WHAT IT SEES</p><h2>数字不只是结果，<br />它们在告诉你下一步。</h2></div><div className="landing-feature-grid"><article><span>01</span><h3>自动识别报表口径</h3><p>不用改表头。懂单儿能识别当前平台的订单号、商品、金额和时间字段，保留原始数据语义。</p><a href="#workflow">了解字段识别 →</a></article><article><span>02</span><h3>从流水读出经营信号</h3><p>营收、客单价、热销商品、时段高峰和异常订单，统一进入一张经营视图。</p><a href="#workflow">查看分析流程 →</a></article><article><span>03</span><h3>把洞察交给下一班</h3><p>用一句话读懂报告，把备货、排班、套餐和促销建议带回真实的门店现场。</p><a href="#for-who">看看适合谁 →</a></article></div></section>

    <section className="landing-workflow" id="workflow"><div className="landing-workflow-intro"><p className="landing-kicker">FROM FILE TO SIGNAL</p><h2>一次上传，<br />四步抵达答案。</h2><p>确定性规则负责准确计算，AI 只在字段含义不清时提供辅助判断。每个结果都可追溯、可核对。</p><button className="landing-outline" type="button" onClick={() => onAuth('register')}>创建我的经营台 <span>↗</span></button></div><div className="landing-steps"><div><b>01</b><span><strong>上传平台报表</strong><small>CSV、XLSX、XLS 均可</small></span></div><div><b>02</b><span><strong>识别与清洗</strong><small>统一字段、修复格式、标记异常</small></span></div><div><b>03</b><span><strong>生成经营视图</strong><small>趋势、商品、用户与异常信号</small></span></div><div><b>04</b><span><strong>给出下一步动作</strong><small>报告、预测和可执行建议</small></span></div></div></section>

    <section className="landing-audience" id="for-who"><div><p className="landing-kicker">MADE FOR THE SHIFT</p><h2>给每天都在做决定的人。</h2></div><div className="audience-notes"><p><b>单店老板</b><span>不用等月底，今天就知道哪道菜在变好。</span></p><p><b>门店运营</b><span>围绕一个平台的真实订单，及时调整备货、排班和促销。</span></p><p><b>餐饮团队</b><span>让报表从“看过”变成“用上”。</span></p></div></section>

    <section className="landing-final"><p className="landing-kicker">READY WHEN YOU ARE</p><h2>让下一张报表，<br />直接告诉你该做什么。</h2><button className="landing-cta" type="button" onClick={() => onAuth('register')}>免费创建经营台 <span>→</span></button></section>
    <footer className="landing-footer"><span>懂单儿 · RODAS</span><span>餐饮订单数据分析系统</span><span>© 2026 莫永信</span></footer>
  </main>
}
