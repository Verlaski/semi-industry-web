/* V1.1交互：正式公司库可插拔；后端行情及报告；无在线LLM。 */
(function () {
  'use strict';
  const D = window.SemiDomain;
  let data, repo, esc, src, stage, returnFocus, drawn=[];
  const drawerHistory=[];
  let drawerFrame;
  const trackMap = new Map();
  const quoteCache=new Map();
  let celebrationTimer, preparationTimer, preparationStepTimer;
  const starIcon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m12 2 2.8 6.5L22 12l-7.2 3.5L12 22l-2.8-6.5L2 12l7.2-3.5Z"/></svg>';
  const stackIcon='<svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="3" y="6" width="15" height="19" rx="2" transform="rotate(-10 3 6)"/><rect x="10" y="2" width="15" height="20" rx="2"/><path d="m17.5 6 1.4 3.5 3.6 1.5-3.6 1.5-1.4 3.5-1.4-3.5-3.6-1.5 3.6-1.5Z"/></svg>';
  const config = () => window.SEMI_CONFIG || {};
  function notify(message) {
    const box=document.getElementById('product-status');box.textContent=message;box.hidden=false;
    clearTimeout(notify.timer);notify.timer=setTimeout(()=>box.hidden=true,5500);
  }
  function badge(c) {
    if(c.listing_status==='非上市') {
      if(c.ipo_status==='A股IPO在审')return '<span class="market-badge ipo">IPO在审</span>'+(c.ipo_detail?' <span class="ipo-detail">'+esc(c.ipo_detail)+'</span>':'');
      return '<span class="market-badge unlisted">非上市</span>';
    }
    const listing=D.primaryListing(c);
    if(c.listing_status!=='上市'||!listing)return '<span class="market-badge unknown">上市信息待补充</span>';
    const group=D.marketGroup(listing.market);
    const cls={'A股':'a','港股':'hk','美股':'us','其他海外':'overseas'}[group];
    return '<span class="market-badge '+cls+'">'+esc(group)+'</span> <span class="ticker">'+esc(listing.ticker || '')+'</span>';
  }
  function companyButton(c,label) {return c ? '<button class="company-link" data-company="'+esc(c.runtime_key)+'">'+esc(label || c.name)+'<span class="company-arrow" aria-hidden="true"> ↗</span></button>' : esc(label || '');}
  function legend() {return '<div class="market-legend" aria-label="资本市场图例"><span>资本市场</span><span class="market-badge a">A股</span><span class="market-badge hk">港股</span><span class="market-badge us">美股</span><span class="market-badge overseas">其他海外上市</span><span class="market-badge ipo">IPO在审</span><span class="market-badge unlisted">非上市</span></div>';}
  function drawerSection(title,content) {return '<section class="drawer-section"><h3 class="drawer-section-title">'+esc(title)+'</h3>'+content+'</section>';}
  function updateDrawerBack() {
    const back=document.getElementById('drawer-back');
    back.hidden=!drawerHistory.length;back.textContent='返回上级';
    back.title=drawerHistory.length ? '返回：'+drawerHistory[drawerHistory.length-1].title : '';
  }
  function positionDrawer(scrollTop,focusTarget) {
    cancelAnimationFrame(drawerFrame);
    const drawer=document.getElementById('detail-drawer');
    drawer.scrollTop=scrollTop;
    drawerFrame=requestAnimationFrame(()=>{
      (focusTarget?.isConnected ? focusTarget : drawer).focus({preventScroll:true});
      drawer.scrollTop=scrollTop;
    });
  }
  function backDrawer() {
    const previous=drawerHistory.pop();if(!previous)return;
    document.getElementById('drawer-body').replaceChildren(...previous.nodes);
    updateDrawerBack();positionDrawer(previous.scrollTop,previous.focus);
  }
  function openDrawer(html) {
    const layer=document.getElementById('drawer-layer'),body=document.getElementById('drawer-body');
    if(layer.hidden){returnFocus=document.activeElement;drawerHistory.length=0;}
    else drawerHistory.push({nodes:[...body.childNodes],scrollTop:document.getElementById('detail-drawer').scrollTop,
      focus:document.activeElement,title:document.getElementById('drawer-title')?.textContent || '详情'});
    body.innerHTML=html;layer.hidden=false;
    // 复用赛道详情的已有字段，只调整抽屉中的信息层级，不修改主图卡片。
    document.querySelectorAll('#drawer-body .tc-kv').forEach(block=>{
      const label=block.querySelector(':scope > .k');if(!label)return;
      const heading=document.createElement('h3');heading.className='drawer-section-title';heading.textContent=label.textContent==='注'?'补充说明':label.textContent==='国产化'?'国产化进展':label.textContent;
      if(block.nextElementSibling?.matches('.tc-subs'))block.append(block.nextElementSibling);
      label.replaceWith(heading);block.classList.add('drawer-section');
    });
    document.body.classList.add('drawer-visible');document.getElementById('app').inert=true;
    document.getElementById('site-nav').inert=true;
    updateDrawerBack();positionDrawer(0);
  }
  function closeDrawer() {
    const layer=document.getElementById('drawer-layer');if(layer.hidden)return;
    layer.hidden=true;document.body.classList.remove('drawer-visible');document.getElementById('app').inert=false;
    document.getElementById('site-nav').inert=false;drawerHistory.length=0;
    cancelAnimationFrame(drawerFrame);updateDrawerBack();document.getElementById('detail-drawer').scrollTop=0;
    if(returnFocus && returnFocus.isConnected)returnFocus.focus();
  }
  function openTrack(id) {
    const t=trackMap.get(id);if(!t)return;
    const card=document.getElementById('card-'+id);
    const detail=card && card.querySelector('.tc-detail');
    const html='<div class="drawer-eyebrow">'+esc(t.dataset==='equipment'?'半导体装备':'半导体材料')+' · '+esc(t.group)+'</div><h2 id="drawer-title">'+esc(t.name)+'</h2><p class="drawer-subtitle">'+esc(t.chain_position || '')+' '+stage(t.localization && t.localization.stage)+'</p>'+
      (detail?detail.innerHTML:'<p>详情数据待补充。</p>');
    openDrawer(html);
  }
  function openChainNode(key) {
    const [type,index]=key.split(':');
    const nodes=type==='base' ? D.structureModel(data).baseMaterials : type==='downstream' ? D.structureModel(data).downstream : [];
    const node=nodes[Number(index)];if(!node)return;
    const html='<div class="drawer-eyebrow">'+(type==='base'?'材料链 · 基础原料':'装备与材料 · 共同应用环节')+'</div><h2 id="drawer-title">'+esc(node.name)+'</h2>'+
      (node.relation?drawerSection('产业关系','<p>'+esc(node.relation)+'</p>'):'')+(node.note?drawerSection('环节说明','<p>'+esc(node.note)+'</p>'):'')+
      (node.players?.length?drawerSection('代表性厂商','<p>'+node.players.map(esc).join(' · ')+'</p>'):'');
    openDrawer(html);
  }
  function openSource(id) {
    const source=data.sources.sources.find(s=>s.source_id===id);if(!source)return;
    const fields={org:'发布机构',publish_date:'发布日期',data_year:'数据年份',metric:'指标',caliber:'统计口径',region:'覆盖范围',type:'资料类型',level:'证据等级',access_date:'查阅日期',remark:'备注'};
    let html='<div class="drawer-eyebrow source-id">'+esc(source.source_id)+'</div><h2 id="drawer-title">'+esc(source.title)+'</h2><section class="drawer-section"><h3 class="drawer-section-title">资料信息</h3><dl class="source-facts">';
    Object.entries(fields).forEach(([key,label])=>{if(source[key])html+='<div><dt>'+label+'</dt><dd>'+esc(source[key])+'</dd></div>';});
    html+='</dl></section>';
    try{const url=new URL(source.url);if(['http:','https:'].includes(url.protocol))html+='<a class="btn source-external" href="'+esc(url.href)+'" target="_blank" rel="noopener">打开原始资料 ↗</a>';}catch(error){/* 没有有效链接时保留已收录的来源字段。 */}
    openDrawer(html);
  }
  function openCompany(key) {
    const c=repo.find(key);if(!c)return;
    const listing=D.primaryListing(c);
    const names=[['中文名称',c.name_cn],['英文名称',c.name_en]]
      .filter(([,value])=>typeof value==='string' && value.trim())
      .map(([label,value])=>'<div><dt>'+label+'</dt><dd>'+esc(value)+'</dd></div>').join('');
    let html='<div class="drawer-eyebrow">公司详情'+(c.verified_master?'':' · 赛道名单兼容展示')+'</div><h2 id="drawer-title">'+esc(c.name)+'</h2>'+
      drawerSection('基本信息','<div class="company-facts">'+badge(c)+'<span>'+esc(c.country_region || '国家地区待补充')+'</span></div>'+
        (names?'<dl class="source-facts company-names">'+names+'</dl>':''));
    let notes='';
    if(!c.verified_master)notes+='<p class="quiet-note">当前名称来自已收录赛道。上市身份及主体关系待正式公司数据库补充。</p>';
    if(c.combo)notes+='<p class="quiet-note">该记录包含组合名称，待研究人员确认主体关系；不参与机会抽卡。</p>';
    if(c.ticker_hints.length)notes+='<p class="quiet-note">原始代码线索：'+esc(c.ticker_hints.join('、'))+'（未作证券代码确认）</p>';
    if(notes)html+=drawerSection('数据说明',notes);
    if(c.ipo_status==='A股IPO在审')html+=drawerSection('IPO进展','<p class="ipo-banner">A股IPO在审：'+esc(c.ipo_detail || '')+'</p>');
    if(listing)html+=drawerSection(config().offline?'上市信息':'上市与行情','<p>交易所：'+esc(listing.exchange || '待补充')+'</p>'+(config().offline?'':'<div data-company-quote="'+esc(listing.ticker || '')+'"></div>'));
    html+='<section class="drawer-section"><h3 class="drawer-section-title">产业关系</h3>';
    const seen=new Set();
    c.occurrences.forEach(o=>{
      const k=[o.track_id,o.sub_name,o.role,o.share,o.raw_name].join('|');if(seen.has(k))return;seen.add(k);
      html+='<section class="relation-block"><button class="relation-track" data-open-track="'+esc(o.track_id)+'">'+esc(o.track_name)+(o.sub_name?' / '+esc(o.sub_name):'')+' →</button><div class="relation-role">'+(o.role==='china'?'中国龙头':'全球龙头')+'</div>'+
        (o.share?'<p>份额 / 排名：'+esc(o.share)+'</p>':'')+(o.products?'<p>产品：'+esc(o.products)+'</p>':'')+
        (o.tag?'<p>'+esc(o.tag)+'</p>':'')+(!o.share&&o.name&&/[:：]/.test(o.name)?'<p class="quiet-note">原始说明：'+esc(o.name)+'</p>':'')+src(o.source_id)+'</section>';
    });
    if(!c.occurrences.length)html+='<p class="quiet-note">赛道关系待补充。</p>';
    html+='</section>';
    openDrawer(html);
    if(listing && /\.(SH|SZ|BJ|HK|US)$/.test(listing.ticker || ''))loadQuotes(listing.ticker);
  }
  function filterControls(prefix, search) {
    const options=[...trackMap.values()].map(t=>'<option value="'+esc(t.id)+'">'+esc(t.name)+'</option>').join('');
    return '<div class="company-filters" id="'+prefix+'-filters">'+
      (search?'<label class="search-label">搜索公司<input type="search" name="search" placeholder="中文、英文、别名或代码" autocomplete="off"></label>':'')+
      '<label>地域<select name="region"><option value="">全部地域</option><option value="domestic">国内</option><option value="overseas">海外及港澳台</option></select></label>'+
      '<label>上市状态<select name="status"><option value="">全部状态</option><option value="上市">已上市</option><option value="非上市">未上市</option></select></label>'+
      (search?'<label>资本市场<select name="market"><option value="">全部市场</option><option>A股</option><option>港股</option><option>美股</option><option value="其他海外">其他海外上市</option></select></label>':'')+
      '<label>赛道<select name="track"><option value="">全部赛道</option>'+options+'</select></label></div>';
  }
  function discoveryFilters() {
    const checkbox=(name,value,label)=>'<label class="filter-choice"><input type="checkbox" name="'+name+'" value="'+esc(value)+'"><span>'+esc(label)+'</span></label>';
    const model=D.structureModel(data);
    let groupIndex=0;
    const groups=model.lanes.map(lane=>'<section class="filter-lane"><h4>'+esc(lane.name)+'</h4>'+lane.groups.map(group=>{
      const scope=String(groupIndex++);
      return '<details class="filter-track-group" data-check-scope="'+scope+'"><summary>'+esc(group.name)+'<span data-group-count>不限</span></summary><div class="filter-group-actions"><button type="button" data-check-group="'+scope+'" data-check-action="all">全选本组</button><button type="button" data-check-group="'+scope+'" data-check-action="clear">清空本组</button></div><div class="filter-options">'+group.tracks.map(t=>checkbox('track',t.id,t.name)).join('')+'</div></details>';
    }).join('')+'</section>').join('');
    const dropdown=(name,label,content)=>'<details class="filter-dropdown" data-filter-menu="'+name+'"><summary><span class="filter-label">'+label+'</span><span class="filter-summary" data-filter-summary="'+name+'">不限</span></summary><div class="filter-dropdown-panel"><fieldset><legend class="sr-only">'+label+'</legend><div class="filter-options">'+content+'</div></fieldset></div></details>';
    return '<div class="discovery-filters" id="discovery-filters"><div class="filter-bar"><p>可多选，未勾选的类别不限</p><button type="button" class="filter-reset" data-reset-discovery>重置筛选</button></div><div class="filter-row">'+
      dropdown('region','地域',checkbox('region','domestic','国内')+checkbox('region','overseas','海外及港澳台'))+
      dropdown('status','上市状态',checkbox('status','上市','已上市')+checkbox('status','非上市','未上市'))+
      '<details class="filter-dropdown filter-dropdown-tracks" data-filter-menu="track"><summary><span class="filter-label">赛道范围</span><span class="filter-summary" id="track-filter-summary">全部赛道</span></summary><div class="filter-dropdown-panel"><p id="selected-track-names" class="selected-track-names" hidden></p><div class="track-filter-groups">'+groups+'</div></div></details></div></div>';
  }
  function values(prefix) {
    const result={};
    document.querySelectorAll('#'+prefix+'-filters [name]').forEach(el=>{
      if(el.type==='checkbox'){if(!result[el.name])result[el.name]=[];if(el.checked)result[el.name].push(el.value);}
      else result[el.name]=el.value;
    });
    return result;
  }
  function renderCompanies() {
    const view=document.getElementById('view-companies');
    view.innerHTML='<h2 class="section-title">龙头公司库</h2><p class="section-desc">从公司反查产业关系、产品与来源。'+(repo.mode==='official'?'已接入正式公司数据库。':'当前为赛道名单兼容展示；上市字段待正式公司数据库补充。')+'</p>'+legend()+
      '<div class="page-actions">'+(repo.mode==='official'?['companies','company_listings','track_company_relations'].map((name,i)=>'<button class="btn" data-export="companies" data-export-table="'+name+'.csv">下载'+['公司','上市信息','赛道关系'][i]+' CSV</button>').join(''):'<button class="btn" data-export="companies">下载公司 CSV</button>')+'</div>'+filterControls('companies',true)+
      '<p class="quiet-note" data-footer-note>地域按原始国别分组；缺少国别时，国内龙头角色可进入国内组，该分组不代表注册地核验。未确认上市身份的企业不进入已上市或未上市筛选。表内行情覆盖注册表内全部 A股/港股/美股证券（listing_id 与正式公司主表关联），其余市场记录显示—；每小时同步，红涨绿跌，市值按原币种以亿元列示。顶部更新时间是行情缓存获取时间，单元格提示保留行情时间与状态。</p><p id="company-quote-updated" class="quote-updated" role="status">最近更新时间：正在读取…</p><div id="company-results"></div>';
    view.querySelectorAll('#companies-filters input,#companies-filters select').forEach(el=>el.addEventListener('input',renderCompanyRows));
    if(config().offline){view.querySelector('#company-quote-updated').remove();view.querySelector('[data-footer-note]').textContent='地域按已收录国别分组。离线版本仅展示公司、上市信息和赛道关系，不含行情数据。';}
    renderCompanyRows();loadQuotes();
  }
  function renderCompanyRows() {
    const list=repo.filter(values('companies'));
    document.getElementById('company-results').innerHTML='<p class="result-count">'+list.length+' 个公司记录</p>'+(list.length?
      '<div class="table-wrap" tabindex="0" role="region" aria-label="公司表，可在表内滚动查看，表头固定"><table class="data company-table"><thead><tr><th>公司</th><th>资本市场</th><th>国家 / 地区</th>'+(config().offline?'':'<th>最新价</th><th>涨跌额</th><th>涨跌幅</th><th>总市值</th>')+'<th>涉及赛道</th></tr></thead><tbody>'+list.map(c=>
        '<tr><td>'+companyButton(c)+'<small class="english-name">'+esc(c.name_en || '')+(c.combo?' · 组合待拆分':'')+'</small></td><td>'+badge(c)+'</td><td>'+esc(c.country_region || '待补充')+'</td>'+(config().offline?'':['price','change','pct','cap'].map(field=>'<td class="quote-cell" data-quote-symbol="'+esc(D.quoteSymbol(c))+'" data-quote-field="'+field+'">—</td>').join(''))+'<td>'+[...new Map(c.occurrences.map(o=>[o.track_id,o])).values()].map(o=>'<button class="relation-track" data-open-track="'+esc(o.track_id)+'">'+esc(o.track_name)+'</button>').join(' · ')+'</td></tr>').join('')+'</tbody></table></div>':'<div class="empty-state">暂无符合条件的记录。未核验上市身份的公司不会被归为“未上市”，可调整筛选条件。</div>');
    updateQuoteCells();
  }
  function updateQuoteCells(){
    document.querySelectorAll('#company-results [data-quote-field]').forEach(cell=>{
      const q=quoteCache.get(cell.dataset.quoteSymbol),values=D.quoteDisplay(q),field=cell.dataset.quoteField;
      cell.textContent=values[field];cell.className='quote-cell'+(field==='cap'?'':' quote-'+values.trend);
      cell.title=q?[q.symbol,'行情时间 '+D.formatQuoteTime(q.quote_time),'缓存获取 '+D.formatQuoteTime(q.fetched_at),quoteStatus[q.status] || '待确认',q.last_sync_failed?'同步失败，保留旧值':''].filter(Boolean).join(' · '):'行情关联待补充';
    });
  }
  function renderDiscovery() {
    document.getElementById('view-discovery').innerHTML='<div class="discovery-heading"><div><p class="drawer-eyebrow">产业发现 / DISCOVERY</p><h2 class="section-title">AI推荐跟踪龙头</h2><p class="section-desc">发现一家，或开启一份十家跟踪清单。</p></div><div class="draw-stamp">下一家<br><small>值得了解的公司</small></div></div>'+
      discoveryFilters()+'<p id="discovery-count" class="result-count" role="status" aria-live="polite"></p><p class="quiet-note" data-footer-note>候选来自已有龙头名单，排除组合主体；条件内均匀随机、无放回，无在线 AI 模型评分或个人偏好分析。复选框同组条件取并集，不同类别取交集；未勾选的类别不限。已上市/未上市均不含尚未确认上市身份的企业。金卡：光刻、刻蚀、薄膜沉积、硅片、光刻胶、CMP材料六个产品设定的重点跟踪赛道的一级龙头；紫卡：其他二级细分龙头，或原始标签含龙头、国产、替代、核心、第一等跟踪线索（重要未上市企业需有已核验上市状态及重点/重要/核心标签）；其余蓝卡。该范围是产品跟踪配置，不代表研究评级；等级按当前筛选赛道关系计算，概率不加权。准备进度表示揭晓动画进度。</p>'+
      '<div class="draw-actions"><button class="btn primary draw-single" data-draw="1">'+starIcon+'<span>单抽<small>发现一家</small></span></button><button class="btn primary draw-ten" data-draw="10">'+stackIcon+'<span>十连抽<small>开启跟踪清单</small></span><b aria-hidden="true">×10</b></button><button class="btn" id="copy-draw" disabled>复制清单</button><span id="draw-state" role="status" aria-live="polite"></span></div><div class="card-key" aria-label="卡片等级"><span class="gold">★★★★★ 核心龙头</span><span class="purple">★★★★ 重点跟踪</span><span class="blue">★★★ 产业观察</span></div><p class="card-disclaimer">卡面等级表示产业图谱中的跟踪标签，不构成投资评级。</p><div id="draw-results" class="draw-results" aria-busy="false"><div class="draw-invitation">下一站，产业深处。<br><small>设置条件，揭晓你的研究清单。</small></div></div>';
    const filters=document.getElementById('discovery-filters');
    filters.addEventListener('change',resetDiscoveryResults);
    filters.addEventListener('click',event=>{
      const reset=event.target.closest('[data-reset-discovery]'),group=event.target.closest('[data-check-group]');
      if(!reset&&!group)return;
      const scope=reset ? filters : filters.querySelector('[data-check-scope="'+group.dataset.checkGroup+'"]');
      scope.querySelectorAll('input[type="checkbox"]').forEach(input=>input.checked=!reset && group.dataset.checkAction==='all');
      resetDiscoveryResults();
    });
    document.addEventListener('click',event=>{
      filters.querySelectorAll('[data-filter-menu][open]').forEach(menu=>{if(!menu.contains(event.target))menu.open=false;});
    });
    filters.addEventListener('keydown',event=>{
      if(event.key!=='Escape')return;
      const menu=event.target.closest('[data-filter-menu][open]');if(!menu)return;
      event.preventDefault();menu.open=false;menu.querySelector('summary').focus();
    });
    const fitDropdowns=()=>filters.querySelectorAll('[data-filter-menu][open]').forEach(menu=>{
      const panel=menu.querySelector('.filter-dropdown-panel');
      panel.style.setProperty('--filter-menu-height',Math.max(120,window.innerHeight-panel.getBoundingClientRect().top-12)+'px');
    });
    filters.addEventListener('toggle',event=>{if(event.target.matches('[data-filter-menu]') && event.target.open)fitDropdowns();},true);
    window.addEventListener('resize',fitDropdowns);
    window.addEventListener('scroll',fitDropdowns,{passive:true});
    window.addEventListener('hashchange',()=>filters.querySelectorAll('[data-filter-menu][open]').forEach(menu=>menu.open=false));
    updateCandidateCount();
  }
  function resetDiscoveryResults() {
    cancelPreparation();clearCelebration();updateCandidateCount();drawn=[];document.getElementById('copy-draw').disabled=true;
    document.getElementById('draw-state').textContent='';
    document.getElementById('draw-results').innerHTML='<div class="empty-state">筛选条件已更新，抽取一份新清单。</div>';
  }
  function updateCandidateCount() {
    const filters=values('discovery'),tracks=filters.track;
    document.getElementById('discovery-count').textContent='当前符合条件：'+repo.filter(filters,true).length+' 家';
    document.getElementById('track-filter-summary').textContent=tracks.length ? '已选 '+tracks.length+' 个赛道' : '全部 '+trackMap.size+' 个赛道';
    ['region','status'].forEach(name=>{
      const labels=[...document.querySelectorAll('#discovery-filters input[name="'+name+'"]:checked')].map(input=>input.nextElementSibling.textContent);
      const summary=document.querySelector('[data-filter-summary="'+name+'"]');summary.textContent=labels.join('、') || '不限';summary.title=summary.textContent;
    });
    document.querySelectorAll('.filter-track-group').forEach(group=>{
      const checked=group.querySelectorAll('input:checked').length,total=group.querySelectorAll('input').length;
      group.querySelector('[data-group-count]').textContent=checked ? checked+' / '+total : '不限';
    });
    const names=document.getElementById('selected-track-names');names.hidden=!tracks.length;
    names.textContent=tracks.map(id=>trackMap.get(id).name).join(' · ');
  }
  function cancelPreparation(){clearTimeout(preparationTimer);clearInterval(preparationStepTimer);document.querySelectorAll('[data-draw]').forEach(button=>button.disabled=false);const results=document.getElementById('draw-results');results.setAttribute('aria-busy','false');if(results.querySelector('.draw-preparation')){results.innerHTML='<div class="draw-invitation">准备已取消，随时开启新清单。</div>';document.getElementById('draw-state').textContent='';}}
  function startDraw(count){
    let selected;
    try{selected=D.draw(repo.filter(values('discovery'),true),count);}catch(error){document.getElementById('draw-state').textContent=error.message;return;}
    cancelPreparation();clearCelebration();drawn=[];document.getElementById('copy-draw').disabled=true;
    if(matchMedia('(prefers-reduced-motion: reduce)').matches){drawCards(count,selected);return;}
    document.querySelectorAll('[data-draw]').forEach(button=>button.disabled=true);
    document.getElementById('draw-state').textContent='跟踪清单准备中';
    const messages=D.preparationMessages();
    const results=document.getElementById('draw-results');results.setAttribute('aria-busy','true');
    results.innerHTML='<div class="draw-preparation"><div class="preparation-orbit" aria-hidden="true">'+stackIcon+'</div><p id="preparation-message" role="status">'+messages[0]+'</p><progress id="preparation-progress" max="100" value="0" aria-label="卡片揭晓进度"></progress><small>准备你的 '+count+' 家跟踪清单</small></div>';
    const started=performance.now();
    preparationStepTimer=setInterval(()=>{const elapsed=performance.now()-started;document.getElementById('preparation-progress').value=Math.min(98,Math.round(elapsed/2400*100));document.getElementById('preparation-message').textContent=messages[Math.min(2,Math.floor(elapsed/800))];},80);
    preparationTimer=setTimeout(()=>{cancelPreparation();drawCards(count,selected);},2400);
  }
  function drawCards(count, selected) {
    clearCelebration();
    const filters=values('discovery');
    drawn=selected;
    document.getElementById('draw-state').textContent='已揭晓 '+drawn.length+' 家';
    document.getElementById('copy-draw').disabled=false;
    document.getElementById('draw-results').innerHTML=drawn.map((c,i)=>{
      const category=D.cardCategory(c,filters.track);
      const occurrence=c.occurrences.find(o=>o.track_id===category.trackId && o.sub_name===category.subName)||c.occurrences.find(o=>D.selected(filters.track,o.track_id));
      const t=trackMap.get(occurrence.track_id);const reason=D.recommendation(c,occurrence.track_id)+(t && t.localization && t.localization.stage?'该赛道国产化阶段：'+t.localization.stage+'。':'');
      return '<article class="discovery-card reveal card-'+category.key+'" style="--reveal-delay:'+Math.min(i*35,250)+'ms"><div class="card-topline"><span class="card-number">'+String(i+1).padStart(2,'0')+' / '+String(count).padStart(2,'0')+'</span><span class="card-category">'+esc(category.label)+'</span></div><div class="card-stars" aria-label="'+category.stars+'星跟踪标签">'+'★'.repeat(category.stars)+'</div><div class="card-emblem" aria-hidden="true">'+starIcon+'</div><h3>'+companyButton(c)+'</h3><div>'+badge(c)+'</div><p class="card-country">'+esc(c.country_region || '国家地区待补充')+'</p><div class="card-track">'+esc(occurrence.track_name)+(occurrence.sub_name?' / '+esc(occurrence.sub_name):'')+'</div><div class="card-reason"><small>'+esc(category.reason)+'</small><p>'+esc(reason)+'</p></div>'+src(occurrence.source_id)+'</article>';
    }).join('');
    celebrationTimer=setTimeout(celebrate,950);
  }
  function clearCelebration(){clearTimeout(celebrationTimer);document.getElementById('draw-confetti')?.remove();}
  function celebrate(){
    if(matchMedia('(prefers-reduced-motion: reduce)').matches || !document.getElementById('view-discovery').classList.contains('active'))return;
    const layer=document.createElement('div');layer.id='draw-confetti';layer.setAttribute('aria-hidden','true');
    const colors=['#dfff00','#087f98','#7043a4','#e4b56b','#52bfcb'];
    for(let i=0;i<48;i++){const ribbon=document.createElement('i');ribbon.style.cssText='--x:'+Math.random()*100+'vw;--drift:'+(Math.random()*160-80)+'px;--spin:'+(180+Math.random()*540)+'deg;--delay:'+Math.random()*.35+'s;--color:'+colors[i%colors.length];layer.append(ribbon);}
    document.body.append(layer);celebrationTimer=setTimeout(clearCelebration,3400);
  }
  function offerList(text) {
    document.getElementById('copy-list-panel')?.remove();
    const panel=document.createElement('section');panel.id='copy-list-panel';panel.className='copy-list-panel';
    panel.innerHTML='<label>本次跟踪清单<textarea readonly aria-label="本次跟踪清单" rows="12">'+esc(text)+'</textarea></label><p class="quiet-note">复制受浏览器限制，可选中文本复制，或下载清单。</p><button class="btn" data-download-list>下载清单文本</button>';
    document.getElementById('draw-results').append(panel);
    const field=panel.querySelector('textarea');field.focus();field.select();notify('清单已展开，可复制或下载。');
  }
  async function request(path,options) {
    if(config().offline)throw new Error('离线版本不连接在线服务。');
    if(!config().apiBase)throw new Error('在线服务尚未配置，请使用已发布的网站。');
    const r=await fetch(config().apiBase+path,{...options,signal:AbortSignal.timeout(65000)});
    const body=await r.json();if(!r.ok)throw new Error(body.message || '服务暂时繁忙，请稍后再试。');return body;
  }
  const quoteStatus={ok:'交易中',closed:'收盘行情',latest_close:'最新收盘',stale:'缓存待更新',unavailable:'暂无有效行情'};
  function quoteMarkup(q) {
    const valid=typeof q.price==='number'&&Number.isFinite(q.price)&&q.price>0;
    return '<div class="quote-card"><div class="quote-label">'+esc(q.name || q.symbol)+' <span class="ticker">'+esc(q.symbol)+'</span></div><div class="quote-price">'+(valid?esc(q.price.toFixed(2)):'—')+' <small>'+esc(q.currency || '')+'</small></div><div class="quote-change">'+(valid && typeof q.change_pct==='number'?esc((q.change_pct>0?'+':'')+q.change_pct.toFixed(2))+'%':'')+' · '+esc(quoteStatus[q.status] || '待确认')+'</div><div class="quote-time">行情时间 '+esc(D.formatQuoteTime(q.quote_time))+'<br>获取时间 '+esc(D.formatQuoteTime(q.fetched_at))+'<br>来源 '+esc(q.provider || '待补充')+(typeof q.market_cap==='number'?'<br>总市值 '+esc(q.market_cap.toLocaleString('zh-CN'))+' '+esc(q.currency):'')+'</div></div>';
  }
  async function loadQuotes(symbol) {
    if(config().offline)return;
    const panel=symbol?document.querySelector('[data-company-quote]'):null;if(symbol&&!panel)return;
    try {const response=await request('/api/quotes'+(symbol?'?symbols='+encodeURIComponent(symbol):''));
      if(panel?.isConnected)panel.innerHTML=response.quotes.map(quoteMarkup).join('');
      else if(!symbol){response.quotes.forEach(q=>quoteCache.set(q.symbol,q));updateQuoteCells();
        const times=response.quotes.map(q=>Date.parse(q.fetched_at)).filter(Number.isFinite);
        const stamp=document.getElementById('company-quote-updated');
        stamp.textContent='最近更新时间：'+(times.length?D.formatQuoteTime(Math.max(...times)):'暂无有效缓存');stamp.title='最近一次成功获取行情缓存的时间；各证券行情时间见单元格提示';}
    }catch(error){if(panel)panel.textContent=error.message;else {const stamp=document.getElementById('company-quote-updated');if(!quoteCache.size)stamp.textContent='最近更新时间：行情暂不可用';stamp.title=error.message;}}
  }
  function download(name,text,type) {
    const url=URL.createObjectURL(new Blob([text],{type:type || 'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function exportCSV(kind,filename) {
    try {const tables=D.csvTables(data,kind,repo).filter(table=>!filename || table.name===filename);tables.forEach((table,i)=>setTimeout(()=>download(table.name,D.csvText(table.rows)),i*180));notify('已导出 '+tables.length+' 张结构化表。');}
    catch(error){notify(error.message);}
  }
  async function report(button) {
    const type=button.dataset.report;button.disabled=true;button.textContent='正在生成报告…';
    try {const result=await request('/api/reports',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({report_type:type,filters:{}})});
      const url=new URL(result.download_url);
      if(url.origin!==new URL(config().apiBase).origin)throw new Error('报告下载地址校验失败。');
      const response=await fetch(url);if(!response.ok)throw new Error('下载链接已过期，请重新生成。');
      const blob=await response.blob();const objectURL=URL.createObjectURL(blob);const a=document.createElement('a');
      a.href=objectURL;a.download=result.filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(objectURL),1500);
      notify(result.cached?'报告已从缓存下载。':'报告已生成并下载。');
    }catch(error){notify(error.name==='TimeoutError'?'报告生成较慢，请稍后重试。':error.message);}
    finally {button.disabled=false;button.textContent='下载 PDF';}
  }
  function addActions() {
    ['overview','equipment','materials','landscape','sources'].forEach(kind=>{
      const section=document.getElementById('view-'+kind);const bar=document.createElement('div');bar.className='page-actions';
      bar.innerHTML=(kind==='sources'?'<button class="btn" data-export="sources">下载来源 CSV</button>':config().offline?'':'<button class="btn" data-report="'+kind+'">下载 PDF</button>')+
        (['equipment','materials'].includes(kind)?'<button class="btn" data-export="'+kind+'" data-export-table="'+kind+'_tracks.csv">下载赛道 CSV</button><button class="btn" data-export="'+kind+'" data-export-table="'+kind+'_leaders.csv">下载龙头 CSV</button>':'');
      if(!bar.innerHTML)return;
      const heading=section.querySelector('.section-desc') || section.firstElementChild;heading.after(bar);
      if(['equipment','materials'].includes(kind)){const key=document.createElement('div');key.innerHTML=legend();bar.after(key);}
    });
  }
  const mapFoldAnimations=new Map();
  function stopMapFold(details) {
    const state=mapFoldAnimations.get(details);
    if(state){state.animation.cancel();mapFoldAnimations.delete(details);}
    details.style.removeProperty('overflow');
  }
  function setMapFold(details,expanded,fromHeight) {
    const previous=mapFoldAnimations.get(details);
    if(fromHeight===undefined && (previous?previous.expanded===expanded:details.open===expanded))return;
    // Read the current animated height before cancelling, so rapid clicks reverse smoothly.
    const from=fromHeight ?? details.getBoundingClientRect().height;
    stopMapFold(details);
    details.open=expanded;
    details.firstElementChild.setAttribute('aria-expanded',String(expanded));
    const to=details.getBoundingClientRect().height;
    if(matchMedia('(prefers-reduced-motion: reduce)').matches || !details.animate || !details.getClientRects().length || Math.abs(to-from)<1)return;
    // Keep content rendered until the closing animation has finished.
    details.open=true;
    details.style.overflow='hidden';
    const animation=details.animate([{height:from+'px'},{height:to+'px'}],{duration:240,easing:'cubic-bezier(.2,.7,.2,1)'});
    mapFoldAnimations.set(details,{animation,expanded});
    animation.onfinish=()=>{
      if(mapFoldAnimations.get(details)?.animation!==animation)return;
      details.open=expanded;
      details.style.removeProperty('overflow');
      mapFoldAnimations.delete(details);
    };
  }
  function setAllMapFolds(section,expanded) {
    const folds=[...section.querySelectorAll('.track-fold,.sub-fold')];
    const roots=folds.filter(d=>!d.parentElement.closest('.track-fold,.sub-fold'));
    const heights=roots.map(d=>d.getBoundingClientRect().height);
    folds.forEach(d=>{
      stopMapFold(d);d.open=expanded;
      d.firstElementChild.setAttribute('aria-expanded',String(expanded));
    });
    // Animate only outer rows while updating every nested row, avoiding competing heights.
    roots.forEach((d,i)=>setMapFold(d,expanded,heights[i]));
  }
  function finishMapFolds() {
    for(const [details,state] of mapFoldAnimations){
      stopMapFold(details);details.open=state.expanded;
      details.firstElementChild.setAttribute('aria-expanded',String(state.expanded));
    }
  }
  function refineLayout() {
    const nav=document.getElementById('site-nav');
    new ResizeObserver(()=>document.documentElement.style.setProperty('--nav-height',nav.getBoundingClientRect().height+'px')).observe(nav);
    ['equipment','materials'].forEach(kind=>{
      const view=document.getElementById('view-'+kind), chain=view.querySelector('.chain');
      const wrapper=document.createElement('section');wrapper.className='map-section';wrapper.setAttribute('aria-label','产业链主图');
      const title=chain.previousElementSibling;chain.before(wrapper);
      const sticky=document.createElement('div');sticky.className='map-sticky';
      const toolbar=document.createElement('div');toolbar.className='map-toolbar';toolbar.append(title);
      toolbar.insertAdjacentHTML('beforeend','<div class="map-actions"><button class="btn" data-folds="open">展开全部</button><button class="btn" data-folds="close">收起全部</button></div>');
      const heads=document.createElement('div');heads.className='map-headings';
      chain.querySelectorAll('.chain-col-head').forEach((head,i)=>{const clone=head.cloneNode(true);clone.style.gridColumn=String(i*2+1);heads.append(clone);});
      sticky.append(toolbar,heads);wrapper.append(sticky,chain);
      new ResizeObserver(()=>wrapper.style.setProperty('--map-toolbar-height',toolbar.getBoundingClientRect().height+'px')).observe(toolbar);
      view.querySelectorAll('.stat-card').forEach(card=>{card.tabIndex=0;});
    });
    const footer=document.getElementById('footer-inner');
    const notes=document.createElement('details');notes.className='reading-notes';
    notes.innerHTML='<summary>阅读说明与数据口径</summary><div class="reading-notes-body"></div>';
    const body=notes.querySelector('div');
    document.querySelectorAll('.view').forEach(view=>{
      const candidates=[...view.querySelectorAll('[data-footer-note],.note-block')];
      if(view.id==='view-companies'){
        const desc=view.querySelector('.section-desc');
        candidates.unshift(desc.cloneNode(true));desc.textContent='从公司出发，查看赛道、产品与来源。';
      }
      if(!candidates.length)return;
      const section=document.createElement('section');
      const heading=document.createElement('h3');heading.textContent=view.querySelector('h2').textContent;section.append(heading);
      candidates.forEach(note=>{note.className='quiet-note';section.append(note);});body.append(section);
    });
    const typography=document.createElement('p');typography.className='quiet-note';typography.textContent='字体：Noto Sans SC（SIL Open Font License 1.1），本地加载。正文与股票代码使用 Sans，Source ID 使用等宽字体。';body.append(typography);
    document.querySelectorAll('.view .market-legend').forEach(key=>key.remove());
    body.insertAdjacentHTML('beforeend',legend());footer.prepend(notes);
    document.querySelectorAll('.table-wrap').forEach(wrap=>{wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','数据表，可在表内滚动查看，表头固定');});
    document.addEventListener('click',event=>{
      const fold=event.target.closest('[data-folds]');
      if(fold){setAllMapFolds(fold.closest('.map-section'),fold.dataset.folds==='open');return;}
      const summary=event.target.closest('.track-fold>summary,.sub-fold>summary');
      if(summary?.closest('.map-section')){
        event.preventDefault();
        const details=summary.parentElement;
        setMapFold(details,!(mapFoldAnimations.get(details)?.expanded ?? details.open));
      }
    });
    window.addEventListener('hashchange',()=>{cancelPreparation();clearCelebration();finishMapFolds();});
    matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change',event=>{if(event.matches)finishMapFolds();});
  }
  function bind() {
    document.addEventListener('click',event=>{
      const target=event.target.closest('button,[data-close-drawer],sup.src');if(!target)return;
      if(target.matches('[data-close-drawer]'))closeDrawer();
      else if(target.matches('[data-company]'))openCompany(target.dataset.company);
      else if(target.matches('[data-open-track]'))openTrack(target.dataset.openTrack);
      else if(target.matches('[data-chain-node]'))openChainNode(target.dataset.chainNode);
      else if(target.matches('[data-source]'))openSource(target.dataset.source);
      else if(target.matches('[data-report]'))report(target);
      else if(target.matches('[data-export]'))exportCSV(target.dataset.export,target.dataset.exportTable);
      else if(target.matches('[data-draw]'))startDraw(Number(target.dataset.draw));
      else if(target.matches('[data-download-list]'))download('本次跟踪清单.txt',document.querySelector('#copy-list-panel textarea').value,'text/plain;charset=utf-8');
      else if(target.id==='copy-draw'){
        const text='本次跟踪清单\n\n'+drawn.map((c,i)=>`${i+1}. ${c.name}｜${[...new Set(c.occurrences.map(o=>o.track_name))].join('/')}｜${c.listing_status || '上市信息待补充'}`).join('\n');
        if(navigator.clipboard)Promise.race([navigator.clipboard.writeText(text),new Promise((_,reject)=>setTimeout(()=>reject(new Error('Clipboard timeout')),1800))]).then(()=>notify('跟踪清单已复制。')).catch(()=>offerList(text));
        else offerList(text);
      }else if(target.id==='drawer-back')backDrawer();
      else if(target.matches('sup.src'))openSource(target.dataset.src);
    });
    document.addEventListener('keydown',e=>{
      if(e.target.matches('sup.src')&&['Enter',' '].includes(e.key)){e.preventDefault();e.target.click();return;}
      if(document.getElementById('drawer-layer').hidden)return;
      if(e.key==='Escape'){e.preventDefault();closeDrawer();return;}
      if(e.key==='Tab'){
        const list=[...document.querySelectorAll('#detail-drawer button,#detail-drawer a,#detail-drawer input,#detail-drawer [tabindex="0"]')].filter(el=>!el.hidden && el.getClientRects().length && !el.disabled);
        const first=list[0],last=list[list.length-1];
        if(e.shiftKey&&(document.activeElement===first||document.activeElement.id==='detail-drawer')){e.preventDefault();last?.focus();}
        else if(!e.shiftKey&&(document.activeElement===last||document.activeElement.id==='detail-drawer')){e.preventDefault();first?.focus();}
      }
    });
    window.addEventListener('hashchange',closeDrawer);
    if(!config().offline)setInterval(()=>{if(document.getElementById('view-companies').classList.contains('active'))loadQuotes();},3600000);
  }
  function configure(context) {
    data=context.DATA;repo=context.REPO;esc=context.esc;src=context.srcRef;stage=context.stageBadge;
    ['equipment','materials'].forEach(dataset=>data[dataset].tracks.forEach(t=>trackMap.set(t.id,{...t,dataset})));
  }
  function init(context) {
    configure(context);
    if(config().offline){document.documentElement.classList.add('offline-mode');document.getElementById('header-meta').insertAdjacentHTML('beforeend','<span class="offline-edition">离线版本</span>');}
    const save=document.getElementById('offline-save');
    if(save){
      save.title='离线包准备中';
      if(config().offlineDownload){
        try{const url=new URL(config().offlineDownload);if(url.protocol!=='https:')throw new Error('下载地址必须使用 HTTPS');
          save.href=url.href;save.removeAttribute('aria-disabled');save.title='下载离线网页压缩包（不含行情）';save.setAttribute('download','');
        }catch(error){console.warn('离线包地址配置无效');}
      }
    }
    renderCompanies();renderDiscovery();addActions();refineLayout();bind();
  }
  window.SemiProduct={configure,init,openTrack,openCompany,openSource,closeDrawer,companyButton,badge,exportCSV};
})();
