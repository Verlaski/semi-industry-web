/* 半导体装备与材料产业链图谱 · 渲染器
   数据与视图分离：所有内容来自 data/*.json，维护只改 JSON。 */
(function () {
  'use strict';

  var ROUTES = ['overview', 'equipment', 'materials', 'landscape', 'sources', 'companies', 'discovery'];
  var STAGE_CLASS = {
    '依赖进口': 's1', '验证导入': 's2', '份额提升': 's3', '批量替代': 's4', '国际领先': 's5'
  };
  var DATA = { meta: null, equipment: null, materials: null, sources: null };
  var REPO;
  var OFFLINE_MASTER;
  var SRC_INDEX = {};   // source_id -> 序号（从 1 开始）
  var SRC_MAP = {};     // source_id -> 条目

  /* ---------- 工具 ---------- */
  function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined && html !== null) e.innerHTML = html;
    return e;
  }
  function stageBadge(stage) {
    if (!stage) return '<span class="stage na">待核</span>';
    var c = STAGE_CLASS[stage] || 'na';
    return '<span class="stage ' + c + '">' + esc(stage) + '</span>';
  }
  function srcRef(id) {
    if (!id || !SRC_MAP[id]) return '';
    var n = SRC_INDEX[id];
    var s = SRC_MAP[id];
    var tip = (s.org || '') + '《' + (s.title || '') + '》' + (s.data_year || s.publish_date || '') + ' · 证据' + (s.level || '?') + '级';
    return '<sup class="src" role="link" tabindex="0" data-src="' + esc(id) + '" title="' + esc(tip) + '">[' + n + ']</sup>';
  }
  function srcRefs(ids) {
    if (!ids) return '';
    if (!Array.isArray(ids)) ids = [ids];
    return ids.map(srcRef).join('');
  }
  function leaderLine(l, withProducts) {
    var s = '<span class="g"><span class="nm">' + companyName(l) + '</span>';
    if (l.country) s += '<span class="ct">(' + esc(l.country) + ')</span>';
    if (l.share) s += '<span class="sh">' + esc(l.share) + '</span>';
    s += srcRef(l.source_id);
    if (withProducts && l.products) s += '<span class="tg">' + esc(l.products) + (l.tag ? ' · ' + esc(l.tag) : '') + '</span>';
    else if (withProducts && l.tag) s += '<span class="tg">' + esc(l.tag) + '</span>';
    return s + '</span>';
  }
  function companyName(leader) {
    var company = REPO && REPO.forLeader(leader);
    return company ? SemiProduct.companyButton(company, leader.name || company.name) + ' ' + SemiProduct.badge(company) : esc(leader.name || leader.company_id || '待补充');
  }
  function subLeaderNames(trackId, subName, role) {
    var rows=REPO.rows.filter(function (row) {return row.track_id===trackId && row.sub_name===subName && row.role===role;});
    var names=rows.map(function (row) {
      var company=REPO.rowMap.get(row);
      return company ? SemiProduct.companyButton(company) : esc(row.raw_name || row.company_id || '待补充');
    }).join(' · ');
    var originals=Array.from(new Set(rows.map(function (row) {return row.name || '';}).filter(function (text) {return /[:：]/.test(text);}))).map(esc);
    return names+(originals.length ? '<small class="sub-leader-original">'+originals.join('<br>')+'</small>' : '');
  }
  function leaderNames(list) {
    return (list || []).map(function (leader) {return '<span class="compact-leader">' + companyName(leader) + '</span>';}).join('');
  }

  /* ---------- 数据加载 ---------- */
  function loadAll() {
    var files = ['meta', 'equipment', 'materials', 'sources'];
    if ((window.SEMI_CONFIG || {}).offline) return Promise.resolve().then(function () {
      var bundle=JSON.parse(document.getElementById('offline-data').textContent);
      files.forEach(function (key) {if(!bundle[key])throw new Error('离线数据缺失');DATA[key]=bundle[key];});
      if(!bundle.companies)throw new Error('离线公司库缺失');
      OFFLINE_MASTER=bundle.companies;
    });
    return Promise.all(files.map(function (k) {
      return fetch('data/' + k + '.json?v=' + encodeURIComponent((window.SEMI_CONFIG || {}).dataVersion || 'local'), {cache:'no-store'}).then(function (r) {
        if (!r.ok) throw new Error(k + '.json HTTP ' + r.status);
        return r.json();
      }).then(function (j) { DATA[k] = j; });
    })).catch(function (err) {
      var loading = document.getElementById('loading');
      loading.innerHTML =
        '<div style="max-width:640px;margin:40px auto;text-align:left;line-height:2">' +
        '<h3 style="color:#b42318">数据加载失败</h3>' +
        '<p>本站通过 <code>fetch()</code> 读取 <code>data/*.json</code>，需通过 HTTP 服务访问，' +
        '直接双击 index.html（file:// 协议）会被浏览器安全策略拦截。</p>' +
        '<p>本机预览：在本目录运行 <code>启动本地预览.bat</code>，或执行 <code>python -m http.server 8000</code> 后访问 <code>http://localhost:8000</code>。</p>' +
        '<p style="color:#68778a">技术细节：' + esc(err.message) + '</p></div>';
      throw err;
    });
  }

  function buildSourceIndex() {
    var list = (DATA.sources && DATA.sources.sources) || [];
    list.forEach(function (s, i) {
      SRC_INDEX[s.source_id] = i + 1;
      SRC_MAP[s.source_id] = s;
    });
  }

  /* ---------- 头尾 ---------- */
  function renderChrome() {
    var m = DATA.meta || {};
    document.getElementById('header-meta').innerHTML =
      '数据更新：<span class="v">' + esc(m.updated || '') + '</span>';
    document.getElementById('footer-inner').innerHTML =
      esc(m.footer_note || '') +
      (m.version_log && m.version_log.length ?
        '<br>最近更新：' + esc(m.version_log[0].date) + ' · ' + esc(m.version_log[0].note) : '');
  }

  /* ---------- 视图一：产业链总图 ---------- */
  function miniTrack(t) {
    var stage = t.localization ? t.localization.stage : null;
    return '<div class="mini-track mini-track-link"><button class="overview-track" data-open-track="' + esc(t.id) + '">' +
      '<span class="nm">' + esc(t.name) + '</span>' + stageBadge(stage) + '</button></div>';
  }

  function structureDiagram() {
    var model=SemiDomain.structureModel(DATA);
    function nodeButton(node,index,type) {
      return '<button class="structure-track" data-chain-node="'+type+':'+index+'">'+esc(node.name)+'<span aria-hidden="true">↗</span></button>';
    }
    var lanes=model.lanes.map(function (lane) {
      var groups=lane.groups.map(function (group) {
        return '<section class="structure-group"><h4>'+esc(group.name)+'<small>'+group.tracks.length+' 赛道</small></h4><div class="structure-tracks">'+group.tracks.map(function (t) {
          return '<button class="structure-track" data-open-track="'+esc(t.id)+'">'+esc(t.name)+'<span aria-hidden="true">↗</span></button>';
        }).join('')+'</div></section>';
      }).join('');
      if(lane.dataset==='materials' && model.baseMaterials.length)groups='<section class="structure-group structure-base"><h4>基础原料</h4><div class="structure-tracks">'+model.baseMaterials.map(function(n,i){return nodeButton(n,i,'base');}).join('')+'</div></section>'+groups;
      return '<section class="structure-lane"><h3>'+esc(lane.name)+'链<span>投入制造与封装 <b aria-hidden="true">→</b></span></h3><div class="structure-lane-groups">'+groups+'</div></section>';
    }).join('');
    return '<figure class="chain-structure"><figcaption>产业链结构<span>点击节点查看详情 ↗</span></figcaption><div class="structure-body"><div class="structure-inputs">'+lanes+'</div><section class="structure-output"><h3>共同应用环节</h3><div class="structure-output-nodes">'+model.downstream.map(function(n,i){return nodeButton(n,i,'downstream');}).join('')+'</div></section></div></figure>';
  }

  function renderOverview() {
    var v = document.getElementById('view-overview');
    var eq = DATA.equipment, ma = DATA.materials, m = DATA.meta || {};
    var upEq = (eq.tracks || []).filter(function (t) { return t.group === '核心零部件与子系统'; });
    var front = (eq.tracks || []).filter(function (t) { return t.group === '前道设备'; });
    var back = (eq.tracks || []).filter(function (t) { return t.group === '后道设备'; });
    var fab = (ma.tracks || []).filter(function (t) { return t.group === '晶圆制造材料'; });
    var pkg = (ma.tracks || []).filter(function (t) { return t.group === '封装材料'; });
    var down = (m.downstream && m.downstream.nodes) || [];

    var html = '';
    html += '<h2 class="section-title">产业链总图</h2>';
    html += '<p class="section-desc" data-footer-note>装备链与材料链并行汇入制造。国产化阶段依次为：依赖进口、验证导入、份额提升、批量替代、国际领先。阶段描述赛道及其适用产品范围，具体依据见详情。</p>';
    html += structureDiagram();

    html += '<div class="lane-label"><span class="tag">装备链</span>核心零部件与子系统 → 半导体制造装备 → 晶圆制造 / 封装测试</div>';
    html += '<div class="flow">';
    html += '<div class="flow-node"><h4>核心零部件与子系统</h4><div class="hint">上游 · 装备的支撑层（' + upEq.length + ' 个赛道）</div>' +
      upEq.map(function (t) { return miniTrack(t, 'equipment'); }).join('') + '</div>';
    html += '<div class="flow-arrow"></div>';
    html += '<div class="flow-node"><h4>半导体制造装备</h4><div class="hint">中游 · 前道 ' + front.length + ' 赛道 · 后道 ' + back.length + ' 赛道</div>' +
      '<div style="margin-bottom:6px"><span class="chain-group-label" style="margin:0">前道设备</span></div>' +
      front.map(function (t) { return miniTrack(t, 'equipment'); }).join('') +
      '<div style="margin:8px 0 6px"><span class="chain-group-label" style="margin:0">后道设备</span></div>' +
      back.map(function (t) { return miniTrack(t, 'equipment'); }).join('') + '</div>';
    html += '<div class="flow-arrow"></div>';
    html += '<div class="flow-node" style="background:var(--navy);border-color:var(--navy)"><h4 style="color:#fff">晶圆制造 · 封装测试</h4>' +
      '<div class="hint" style="color:#9fb4c8">下游 · 装备与材料的共同应用环节</div>' +
      down.map(function (d) {
        return '<div class="mini-track"><span class="nm" style="color:#eaf0f6">' + esc(d.name) + '</span>' +
          '<span style="font-size:11px;color:#9fb4c8">' + esc(d.note || '') + '</span></div>' +
          '<div style="font-size:12px;color:#c8d6e4;padding:0 0 6px">' + esc((d.players || []).join(' · ')) + '</div>';
      }).join('') + '</div>';
    html += '</div>';

    html += '<div class="lane-label mat"><span class="tag">材料链</span>基础原料 → 晶圆制造材料 / 封装材料 → 晶圆制造 / 封装测试</div>';
    html += '<div class="flow">';
    var base = (ma.base_materials || []).map(function (b) {
      return '<div class="mini-track"><span class="nm">' + esc(b.name) + '</span>' +
        '<span style="font-size:11px;color:var(--faint)">' + esc(b.relation || '') + '</span></div>';
    }).join('');
    html += '<div class="flow-node"><h4>基础原料</h4><div class="hint">上游 · 材料的上游（示意，不穷举）</div>' + base + '</div>';
    html += '<div class="flow-arrow"></div>';
    html += '<div class="flow-node"><h4>半导体材料</h4><div class="hint">中游 · 直接进入制造与封装流程的电子材料</div>' +
      '<div style="margin-bottom:6px"><span class="chain-group-label" style="margin:0">晶圆制造材料</span></div>' +
      fab.map(function (t) { return miniTrack(t, 'materials'); }).join('') +
      '<div style="margin:8px 0 6px"><span class="chain-group-label" style="margin:0">封装材料</span></div>' +
      pkg.map(function (t) { return miniTrack(t, 'materials'); }).join('') + '</div>';
    html += '<div class="flow-arrow"></div>';
    html += '<div class="flow-node" style="border-style:dashed;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:6px">' +
      '<div style="font-family:var(--sans);font-weight:700;color:var(--navy)">汇入下游制造</div>' +
      '<div style="font-size:12px;color:var(--muted);text-align:center">晶圆制造 · 封装测试<br>（同装备链下游）</div></div>';
    html += '</div>';

    if (m.overview_note) html += '<div class="note-block">' + esc(m.overview_note) + '</div>';
    v.innerHTML = html;
  }

  /* ---------- 行业子图谱（装备 / 材料共用） ---------- */
  function trackCard(t) {
    var stage = t.localization ? t.localization.stage : null;
    var g = t.global_leaders || [], c = t.china_leaders || [];
    var detail = '';

    if (t.subs && t.subs.length) {
      detail += '<div class="tc-kv"><span class="k">二级细分</span></div><ul class="tc-subs">' +
        t.subs.map(function (s) {
          var line = '<b>' + esc(s.name) + '</b>';
          var parts = [];
          if (s.global_leaders && s.global_leaders.length) parts.push('全球：' + subLeaderNames(t.id, s.name, 'global'));
          if (s.china_leaders && s.china_leaders.length) parts.push('国内：' + subLeaderNames(t.id, s.name, 'china'));
          if (parts.length) line += ' — ' + parts.join('；');
          if (s.note) line += ' <span style="color:var(--faint)">（' + esc(s.note) + '）</span>';
          return '<li>' + line + '</li>';
        }).join('') + '</ul>';
    }
    if (t.market_size) {
      detail += '<div class="tc-kv"><span class="k">市场规模</span>' + esc(t.market_size.value) + esc(t.market_size.unit || '') +
        '（' + esc(t.market_size.year || '') + ' · ' + esc(t.market_size.scope || '') + '）' + srcRef(t.market_size.source_id) + '</div>';
    }
    if (g.length) {
      detail += '<div class="tc-kv"><span class="k">全球龙头</span><div class="leader-cell">' +
        g.map(function (l) { return leaderLine(l, true); }).join('') + '</div></div>';
    }
    detail += '<div class="tc-kv"><span class="k">国内龙头</span><div class="leader-cell">' +
      (c.length ? c.map(function (l) { return leaderLine(l, true); }).join('')
                : '<span class="g" style="color:var(--muted)">国内暂无头部厂商</span>') + '</div></div>';
    if (t.localization) {
      detail += '<div class="tc-kv"><span class="k">国产化</span>' + stageBadge(t.localization.stage) +
        ' <span style="color:var(--muted)">范围：' + esc(t.localization.scope || '—') + '</span>';
      if (t.localization.evidence) detail += '<br><span style="color:var(--ink-2);font-size:12.5px">依据：' + esc(t.localization.evidence) + srcRef(t.localization.source_id) + '</span>';
      detail += '</div>';
    }
    if (t.note) detail += '<div class="tc-kv"><span class="k">注</span><span style="color:var(--muted)">' + esc(t.note) + '</span></div>';

    var folds = function (label, content) {
      return '<details class="track-fold"><summary>' + label + '</summary><div class="fold-content">' + content + '</div></details>';
    };
    var compact = folds('全球龙头 · ' + g.length, g.length ? leaderNames(g) : '暂未收录') +
      folds('国内龙头 · ' + c.length, c.length ? leaderNames(c) : '暂无头部厂商');
    if (t.subs && t.subs.length) compact += folds('二级分类 · ' + t.subs.length,
      t.subs.map(function (s) {
        return '<details class="sub-fold"><summary>' + esc(s.name) + '</summary>' +
          folds('全球龙头', subLeaderNames(t.id, s.name, 'global') || '暂未收录') +
          folds('国内龙头', subLeaderNames(t.id, s.name, 'china') || '暂未收录') + '</details>';
      }).join(''));
    return '<div class="track-card" id="card-' + esc(t.id) + '" data-track="' + esc(t.id) + '">' +
      '<div class="tc-head"><button class="track-open tc-name" data-track-open="' + esc(t.id) + '">' + esc(t.name) + '</button>' + stageBadge(stage) + '</div>' +
      '<div class="tc-leaders">' + compact + '</div>' +
      '<div class="tc-detail">' + detail + '</div></div>';
  }

  function chainColumn(title, tier, cls, bodyHtml) {
    return '<div><div class="chain-col-head ' + cls + '"><span>' + esc(title) + '</span><span class="tier">' + esc(tier) + '</span></div>' +
      '<div class="chain-col-body">' + bodyHtml + '</div></div>';
  }

  function renderIndustry(viewId, data, kind) {
    var v = document.getElementById(viewId);
    var tracks = data.tracks || [];
    var html = '';

    /* 景气度与规模 facts */
    var facts = kind === 'equipment' ? (data.wfe_facts || []) : [];
    var prov = (DATA.meta.prosperity && DATA.meta.prosperity[kind]) || null;
    html += '<h2 class="section-title">' + esc(data.industry || '') + ' · 产业链图谱</h2>';
    html += '<p class="section-desc" data-footer-note>' + esc(data.intro || '') + '</p>';

    if (prov || facts.length) {
      html += '<div class="card-grid" style="margin-bottom:8px">';
      if (prov) {
        html += '<div class="stat-card prosperity-card"><div class="k">行业景气度研判</div>' +
          '<div class="lvl">' + esc(prov.level || '—') + '</div>' +
          '<div class="d">' + esc(prov.evidence || '') + srcRefs(prov.source_ids) + '</div></div>';
      }
      facts.slice(0, 3).forEach(function (f) {
        var longV = String(f.value || '').length > 14;
        html += '<div class="stat-card"><div class="k">' + esc(f.label) + '（' + esc(f.year || '') + ' · ' + esc(f.region || '') + '）</div>' +
          '<div class="v' + (longV ? ' long' : '') + '">' + esc(f.value) + (longV ? '' : '<span class="u"> ' + esc(f.unit || '') + '</span>') + srcRef(f.source_id) + '</div>' +
          (f.note ? '<div class="d">' + esc(f.note) + '</div>' : '') + '</div>';
      });
      html += '</div>';
    }

    /* 主图 */
    if (kind === 'equipment') {
      var up = tracks.filter(function (t) { return t.group === '核心零部件与子系统'; });
      var front = tracks.filter(function (t) { return t.group === '前道设备'; });
      var back = tracks.filter(function (t) { return t.group === '后道设备'; });
      var downNodes = (DATA.meta.downstream && DATA.meta.downstream.nodes) || [];
      html += '<h3 class="section-title" style="font-size:17px">产业链主图</h3>';
      html += '<div class="chain cols-3">';
      html += chainColumn('上游 · 核心零部件与子系统', '一级分类', 'up',
        '<div class="track-grid">' + up.map(trackCard).join('') + '</div>');
      html += '<div class="chain-arrow"></div>';
      html += chainColumn('中游 · 半导体制造装备', '一级分类', 'mid',
        '<div class="chain-group-label">前道设备</div><div class="track-grid">' + front.map(trackCard).join('') + '</div>' +
        '<div class="chain-group-label">后道设备</div><div class="track-grid">' + back.map(trackCard).join('') + '</div>');
      html += '<div class="chain-arrow"></div>';
      html += chainColumn('下游 · 设备客户', '应用环节', 'down',
        downNodes.map(function (d) {
          return '<div class="track-card" style="cursor:default;border-left-color:var(--gold)">' +
            '<div class="tc-head"><span class="tc-name">' + esc(d.name) + '</span></div>' +
            '<div class="tc-leaders">' + esc((d.players || []).join(' · ')) + '</div>' +
            (d.note ? '<div class="tc-leaders" style="color:var(--faint)">' + esc(d.note) + '</div>' : '') + '</div>';
        }).join(''));
      html += '</div>';
    } else {
      var fab = tracks.filter(function (t) { return t.group === '晶圆制造材料'; });
      var pkg = tracks.filter(function (t) { return t.group === '封装材料'; });
      var base = (data.base_materials || []).map(function (b) {
        return '<div class="track-card" style="cursor:default">' +
          '<div class="tc-head"><span class="tc-name">' + esc(b.name) + '</span></div>' +
          '<div class="tc-leaders">' + esc(b.relation || '') + (b.note ? '（' + esc(b.note) + '）' : '') + '</div></div>';
      }).join('');
      html += '<h3 class="section-title" style="font-size:17px">产业链主图</h3>';
      html += '<div class="chain cols-3">';
      html += chainColumn('上游 · 基础原料', '关系示意', 'up', base);
      html += '<div class="chain-arrow"></div>';
      html += chainColumn('中游 · 半导体材料', '一级分类', 'mid',
        '<div class="chain-group-label">晶圆制造材料</div><div class="track-grid">' + fab.map(trackCard).join('') + '</div>' +
        '<div class="chain-group-label">封装材料</div><div class="track-grid">' + pkg.map(trackCard).join('') + '</div>');
      html += '<div class="chain-arrow"></div>';
      html += chainColumn('下游 · 应用环节', '制造流程', 'down',
        '<div class="track-card" style="cursor:default;border-left-color:var(--gold)">' +
        '<div class="tc-head"><span class="tc-name">晶圆制造</span></div>' +
        '<div class="tc-leaders">晶圆制造材料直接进入晶圆厂制造流程</div></div>' +
        '<div class="track-card" style="cursor:default;border-left-color:var(--gold)">' +
        '<div class="tc-head"><span class="tc-name">封装测试</span></div>' +
        '<div class="tc-leaders">封装材料进入 OSAT / 先进封装产线</div></div>');
      html += '</div>';
    }

    /* 总览表 */
    html += '<h3 class="section-title" style="font-size:17px">赛道龙头总览表</h3>';
    html += '<div class="table-toolbar">' +
      '<span class="filter-label">按国产化阶段筛选：</span>' +
      '<button class="filter-btn on" data-stage="">全部</button>' +
      ['依赖进口', '验证导入', '份额提升', '批量替代', '国际领先'].map(function (s) {
        return '<button class="filter-btn" data-stage="' + s + '">' + s + '</button>';
      }).join('') +
      '<span class="spacer"></span>' +
      '<button class="btn" data-csv="' + kind + '">导出 CSV</button></div>';
    html += '<div class="table-wrap"><table class="data" id="table-' + kind + '"><thead><tr>' +
      '<th>环节</th><th>赛道 / 二级细分</th><th>全球龙头</th><th>国内龙头</th><th>规模 / 依据</th><th>国产化阶段</th>' +
      '</tr></thead><tbody>' +
      tracks.map(function (t) {
        var g = t.global_leaders || [], c = t.china_leaders || [];
        var subs = (t.subs || []).map(function (s) { return s.name; }).join('、');
        var scale = '';
        if (t.market_size) scale = esc(t.market_size.value) + esc(t.market_size.unit || '') + '（' + esc(t.market_size.year || '') + '）' + srcRef(t.market_size.source_id);
        var loc = t.localization || {};
        return '<tr data-stage="' + esc(loc.stage || '') + '" id="row-' + esc(t.id) + '">' +
          '<td><span class="pos">' + esc(t.chain_position || '') + '</span><br>' + esc(t.group || '') + '</td>' +
          '<td><b>' + esc(t.name) + '</b>' + (subs ? '<br><span class="pos">' + esc(subs) + '</span>' : '') + '</td>' +
          '<td class="leader-cell">' + g.map(function (l) { return leaderLine(l, false); }).join('') + '</td>' +
          '<td class="leader-cell">' + (c.length ? c.map(function (l) { return leaderLine(l, false); }).join('')
            : '<span style="color:var(--faint)">国内暂无头部厂商</span>') + '</td>' +
          '<td>' + scale + '</td>' +
          '<td>' + stageBadge(loc.stage) + (loc.scope ? '<br><span class="pos">范围：' + esc(loc.scope) + '</span>' : '') + srcRef(loc.source_id) + '</td>' +
          '</tr>';
      }).join('') + '</tbody></table></div>';

    v.innerHTML = html;
  }

  /* ---------- 视图四：竞争格局与国产化 ---------- */
  function renderLandscape() {
    var v = document.getElementById('view-landscape');
    var m = DATA.meta || {};
    var html = '<h2 class="section-title">竞争格局与国产化</h2>';
    html += '<p class="section-desc" data-footer-note>国产化判断均附适用产品范围；集中度与份额请结合年份、指标和来源阅读。</p>';

    /* 景气度 */
    var p = m.prosperity || {};
    html += '<div class="card-grid">';
    ['equipment', 'materials'].forEach(function (k) {
      var it = p[k]; if (!it) return;
      html += '<div class="stat-card prosperity-card"><div class="k">' + (k === 'equipment' ? '半导体装备' : '半导体材料') + ' · 景气度研判</div>' +
        '<div class="lvl">' + esc(it.level || '—') + '</div>' +
        '<div class="d">' + esc(it.evidence || '') + srcRefs(it.source_ids) + '</div></div>';
    });
    html += '</div>';

    /* 关键规模 facts */
    if (m.facts && m.facts.length) {
      html += '<h3 class="section-title" style="font-size:17px">关键市场数据</h3><div class="card-grid">';
      m.facts.forEach(function (f) {
        var longV = String(f.value || '').length > 14;
        html += '<div class="stat-card"><div class="k">' + esc(f.label) + '（' + esc(f.year || '') + ' · ' + esc(f.region || '') + '）</div>' +
          '<div class="v' + (longV ? ' long' : '') + '">' + esc(f.value) + (longV ? '' : '<span class="u"> ' + esc(f.unit || '') + '</span>') + srcRef(f.source_id) + '</div>' +
          (f.note ? '<div class="d">' + esc(f.note) + '</div>' : '') + '</div>';
      });
      html += '</div>';
    }

    /* 驱动力 */
    if (m.drivers && m.drivers.length) {
      html += '<h3 class="section-title" style="font-size:17px">本周期产业驱动力</h3><ul class="verlog">' +
        m.drivers.map(function (d) { return '<li>' + esc(d) + '</li>'; }).join('') + '</ul>';
    }

    /* 设备 Top 厂商表 */
    if (m.equipment_top && m.equipment_top.length) {
      html += '<h3 class="section-title" style="font-size:17px">全球半导体设备厂商收入排名（Top ' + m.equipment_top.length + '）</h3>';
      html += '<div class="table-wrap"><table class="data"><thead><tr><th>排名</th><th>公司（国别）</th><th>收入</th><th>市占率</th><th>核心产品线</th><th>口径年份</th></tr></thead><tbody>' +
        m.equipment_top.map(function (r) {
          return '<tr><td>' + esc(r.rank) + '</td><td><b>' + esc(r.name) + '</b>' + (r.country ? ' <span class="ct">(' + esc(r.country) + ')</span>' : '') + srcRef(r.source_id) + '</td>' +
            '<td>' + esc(r.revenue || '—') + (r.unit && String(r.revenue || '').indexOf('N/A') < 0 ? ' ' + esc(r.unit) : '') + '</td>' +
            '<td>' + esc(r.share || '—') + '</td><td>' + esc(r.products || '') + '</td><td>' + esc(r.year || '') + '</td></tr>';
        }).join('') + '</tbody></table></div>';
    }

    /* 国产化阶段矩阵 */
    html += '<h3 class="section-title" style="font-size:17px">国产化阶段总览</h3>';
    var groups = [
      { label: '装备 · 核心零部件与子系统', tracks: DATA.equipment.tracks.filter(function (t) { return t.group === '核心零部件与子系统'; }) },
      { label: '装备 · 前道设备', tracks: DATA.equipment.tracks.filter(function (t) { return t.group === '前道设备'; }) },
      { label: '装备 · 后道设备', tracks: DATA.equipment.tracks.filter(function (t) { return t.group === '后道设备'; }) },
      { label: '材料 · 晶圆制造材料', tracks: DATA.materials.tracks.filter(function (t) { return t.group === '晶圆制造材料'; }) },
      { label: '材料 · 封装材料', tracks: DATA.materials.tracks.filter(function (t) { return t.group === '封装材料'; }) }
    ];
    html += '<div class="matrix-wrap table-wrap"><table class="matrix"><thead><tr><th>板块</th><th>赛道</th><th>国产化阶段</th><th>适用产品范围</th><th>依据</th></tr></thead><tbody>';
    groups.forEach(function (g) {
      g.tracks.forEach(function (t, i) {
        var loc = t.localization || {};
        html += '<tr>' +
          (i === 0 ? '<td rowspan="' + g.tracks.length + '" style="font-weight:700;color:var(--navy)">' + esc(g.label) + '</td>' : '') +
          '<td>' + esc(t.name) + '</td><td>' + stageBadge(loc.stage) + '</td>' +
          '<td>' + esc(loc.scope || '—') + '</td>' +
          '<td style="max-width:420px">' + esc(loc.evidence || '') + srcRef(loc.source_id) + '</td></tr>';
      });
    });
    html += '</tbody></table></div>';

    /* 格局变化 */
    if (m.trend_notes && m.trend_notes.length) {
      html += '<h3 class="section-title" style="font-size:17px">近年格局变化与技术趋势</h3><ul class="verlog">' +
        m.trend_notes.map(function (t) {
          return '<li>' + esc(t.text || t) + srcRef(t.source_id) + '</li>';
        }).join('') + '</ul>';
    }

    v.innerHTML = html;
  }

  /* ---------- 视图五：数据来源与版本 ---------- */
  function renderSources() {
    var v = document.getElementById('view-sources');
    var list = (DATA.sources && DATA.sources.sources) || [];
    var m = DATA.meta || {};
    var html = '<h2 class="section-title">数据来源与版本记录</h2>';
    html += '<p class="section-desc" data-footer-note>来源角标对应本表。证据等级：A=行业机构正式数据/上市公司一手披露；B=权威研究报告且口径可确认；C=公司官网/公开采访/行业媒体；D=二手转载，不单独支撑核心结论。</p>';
    html += '<div class="table-wrap"><table class="data source-table"><thead><tr>' +
      '<th>Source ID</th><th>机构</th><th>资料名称</th><th>日期 / 年份</th><th>证据</th>' +
      '</tr></thead><tbody>' +
      list.map(function (s, i) {
        return '<tr class="src-row" id="src-' + esc(s.source_id) + '">' +
          '<td><span class="source-id">[' + (i+1) + '] ' + esc(s.source_id) + '</span></td>' +
          '<td><span class="cell-clip" title="' + esc(s.org || '') + '">' + esc(s.org || '') + '</span></td>' +
          '<td><button class="source-open" data-source="' + esc(s.source_id) + '" title="查看资料详情：' + esc(s.title || '') + '">' + esc(s.title || '') + ' ↗</button></td>' +
          '<td>' + esc(s.publish_date || s.data_year || '—') + '</td>' +
          '<td><span class="level ' + esc(s.level || 'D') + '">' + esc(s.level || '?') + '</span></td></tr>';
      }).join('') + '</tbody></table></div>';

    if (m.version_log && m.version_log.length) {
      html += '<h3 class="section-title" style="font-size:17px">版本记录</h3><ul class="verlog">' +
        m.version_log.map(function (l) {
          return '<li><b>' + esc(l.version) + '</b>（' + esc(l.date) + '）：' + esc(l.note) + '</li>';
        }).join('') + '</ul>';
    }
    if (m.methodology_note) html += '<div class="note-block">' + esc(m.methodology_note) + '</div>';
    v.innerHTML = html;
  }

  /* ---------- 交互 ---------- */
  function bindInteractions() {
    document.getElementById('app').addEventListener('click', function (e) {
      if (e.target.closest('[data-company],details,summary,sup.src')) return;
      var card = e.target.closest('.track-card[data-track]');
      if (card && !e.target.closest('a') && !e.target.closest('sup.src')) {
        SemiProduct.openTrack(card.getAttribute('data-track'));
        return;
      }
      var fb = e.target.closest('.filter-btn');
      if (fb) {
        var stage = fb.getAttribute('data-stage');
        var bar = fb.parentElement;
        bar.querySelectorAll('.filter-btn').forEach(function (b) { b.classList.remove('on'); });
        fb.classList.add('on');
        var table = bar.parentElement.querySelector('table.data');
        table.querySelectorAll('tbody tr').forEach(function (tr) {
          tr.style.display = (!stage || tr.getAttribute('data-stage') === stage) ? '' : 'none';
        });
        return;
      }
      var csv = e.target.closest('[data-csv]');
      if (csv) exportCSV(csv.getAttribute('data-csv'));
    });
  }

  function exportCSV(kind) { SemiProduct.exportCSV(kind); }

  /* ---------- 路由 ---------- */
  function showView(route, trackId) {
    if (ROUTES.indexOf(route) < 0) route = 'overview';
    ROUTES.forEach(function (r) {
      document.getElementById('view-' + r).classList.toggle('active', r === route);
    });
    document.querySelectorAll('.site-nav a').forEach(function (a) {
      a.classList.toggle('active', a.getAttribute('data-route') === route);
      if (a.getAttribute('data-route') === route) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    if (trackId) {
      setTimeout(function () {
        var card = document.getElementById('card-' + trackId);
        if (card) {
          SemiProduct.openTrack(trackId);
          card.scrollIntoView({ block: 'center' });
        }
      }, 60);
    } else {
      window.scrollTo(0, 0);
    }
  }

  function route() {
    var hash = location.hash.replace(/^#\//, '') || 'overview';
    var parts = hash.split('?');
    var name = parts[0];
    var trackId = null;
    if (parts[1]) {
      parts[1].split('&').forEach(function (kv) {
        var p = kv.split('=');
        if (p[0] === 'track') trackId = decodeURIComponent(p[1] || '');
      });
    }
    showView(name, trackId);
  }

  /* ---------- 启动 ---------- */
  loadAll().then(function () {
    if ((window.SEMI_CONFIG || {}).offline) {REPO=new SemiDomain.CompanyRepository(DATA,OFFLINE_MASTER);return;}
    return SemiDomain.CompanyRepository.load(DATA).then(function (repository) {REPO=repository;});
  }).then(function () {
    buildSourceIndex();
    SemiProduct.configure({DATA:DATA,REPO:REPO,esc:esc,srcRef:srcRef,stageBadge:stageBadge});
    renderChrome();
    renderOverview();
    renderIndustry('view-equipment', DATA.equipment, 'equipment');
    renderIndustry('view-materials', DATA.materials, 'materials');
    renderLandscape();
    renderSources();
    SemiProduct.init({DATA:DATA,REPO:REPO,esc:esc,srcRef:srcRef,stageBadge:stageBadge});
    document.getElementById('loading').style.display = 'none';
    bindInteractions();
    window.addEventListener('hashchange', route);
    route();
  }).catch(function () {
    var loading=document.getElementById('loading');
    loading.style.display='block';loading.textContent='图谱数据暂时无法加载，请刷新后重试。';
  });
})();
