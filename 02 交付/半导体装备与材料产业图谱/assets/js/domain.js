/* 纯数据层：浏览器和Node测试共用，不依赖研究草稿或DOM。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SemiDomain = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const regions = {中:'中国',美:'美国',日:'日本',韩:'韩国',台:'中国台湾',荷:'荷兰',德:'德国',英:'英国',法:'法国',奥:'奥地利',新:'新加坡'};
  const norm = s => String(s || '').normalize('NFKC').toUpperCase().replace(/[^\p{L}\p{N}&/-]/gu, '');
  // 标量调用继续兼容公司库；复选框空数组表示该组不限。
  function selection(value) {return (Array.isArray(value) ? value : [value]).filter(Boolean);}
  function selected(value, candidate) {const choices=selection(value);return !choices.length || choices.includes(candidate);}
  function structureModel(data) {
    const lanes=['equipment','materials'].map(dataset=>{
      const source=data[dataset] || {}, groups=new Map();
      (source.tracks || []).forEach(track=>{
        const name=track.group || '其他赛道';
        if(!groups.has(name))groups.set(name,{name,tracks:[]});
        groups.get(name).tracks.push(track);
      });
      return {dataset,name:source.industry || dataset,groups:[...groups.values()]};
    });
    return {lanes,baseMaterials:data.materials?.base_materials || [],downstream:data.meta?.downstream?.nodes || []};
  }
  function topSplit(text, separators) {
    const out = []; let depth = 0, begin = 0;
    for (let i=0;i<text.length;i++) {
      const c=text[i];
      if ('(（'.includes(c)) depth++;
      else if (')）'.includes(c)) depth--;
      else if (!depth && separators.includes(c)) {out.push(text.slice(begin, i).trim()); begin = i+1;}
    }
    out.push(text.slice(begin).trim()); return out.filter(Boolean);
  }
  function pieces(text) {
    const description = topSplit(text, ':：').length > 1;
    return topSplit(text, ';；').flatMap((clause, i) => {
      const parts = topSplit(clause, ':：');
      return i && description && parts.length === 1 ? [] : topSplit(parts[0], '、·');
    });
  }
  function parseName(raw, country) {
    const notes = [], countries = (country || '').split('/').filter(Boolean).map(c => regions[c] || c);
    const hints = [];
    const cleaned = raw.replace(/[（(]([^（）()]*)[）)]/g, (_, inner) => {
      const parts = inner.split(/[，,]/), first = parts[0];
      if (regions[first] || ['中国','日本','美国','韩国','中国台湾','新加坡','荷兰','德国','奥地利'].includes(first)) {
        countries.push(regions[first] || first); if (parts[1]) notes.push(parts.slice(1).join('，'));
      } else {
        const code = inner.match(/(?:[A-Z]\d{5,6}|\b\d{5,6}(?:\.[A-Z]+)?\b)/g);
        if (code) hints.push(...code);
        notes.push(inner);
      }
      return ' ';
    }).replace(/\s+/g, ' ').trim();
    let cn = '', en = '';
    const combo = /[/／]/.test(cleaned);
    const cjk = /[\u3400-\u9fff]/.exec(cleaned);
    if (combo) {if (cjk) cn = cleaned; else en = cleaned;}
    else if (!cjk) en = cleaned;
    else {
      const cnFirst = /^(.+?[\u3400-\u9fff][^\s]*)\s+([A-Za-z].*)$/.exec(cleaned);
      if (cnFirst && !/[\u3400-\u9fff]/.test(cnFirst[2])) {cn = cnFirst[1]; en = cnFirst[2];}
      else if (cjk.index) {en = cleaned.slice(0,cjk.index).trim(); cn = cleaned.slice(cjk.index).trim();}
      else cn = cleaned;
    }
    return {cn,en,cleaned,combo,notes,ticker_hints:[...new Set(hints)],countries:[...new Set(countries)]};
  }
  function leaderRows(data) {
    const rows = [];
    ['equipment','materials'].forEach(dataset => {
      (data[dataset].tracks || []).forEach(track => {
        [{obj:track,sub:''}, ...(track.subs || []).map(obj => ({obj,sub:obj.name}))].forEach(({obj,sub}) => {
          ['global','china'].forEach(role => (obj[role+'_leaders'] || []).forEach((leader, index) => {
            const raw = typeof leader === 'string' ? {name:leader} : leader;
            if (raw.company_id && !raw.name) {
              rows.push({dataset,track_id:track.id,track_name:track.name,sub_name:sub,role,index,raw_name:'',...raw}); return;
            }
            pieces(raw.name || '').forEach((name, piece) => rows.push({dataset,track_id:track.id,track_name:track.name,
              sub_name:sub,role,index,piece,raw_name:name,...raw,parsed:parseName(name,raw.country)}));
          }));
        });
      });
    });
    return rows;
  }
  class CompanyRepository {
    constructor(data, official) {
      this.data = data; this.rows = leaderRows(data); this.mode = official ? 'official' : 'compatibility';
      this.companies = []; this.rowMap = new Map(); this.byKey = new Map();
      if (official) this.fromOfficial(official); else this.fromLeaders();
    }
    static async load(data, fetcher) {
      const version=typeof window!=='undefined' && window.SEMI_CONFIG ? window.SEMI_CONFIG.dataVersion || 'local' : 'local';
      const response = await (fetcher || fetch)('data/companies.json?v='+encodeURIComponent(version),{cache:'no-store'});
      if (response.status === 404) return new CompanyRepository(data, null);
      if (!response.ok) throw new Error('正式公司数据暂不可用，请稍后再试');
      return new CompanyRepository(data, await response.json());
    }
    fromOfficial(official) {
      const list = Array.isArray(official) ? official : official.companies;
      if (!Array.isArray(list)) throw new Error('正式公司数据格式需要维护人员检查');
      list.forEach(c => {
        if (!c.company_id || this.byKey.has(c.company_id)) throw new Error('正式公司编号缺失或重复');
        const vm = {runtime_key:c.company_id, name:c.name_cn || c.name_en || c.short_name || c.company_id,
          name_cn:c.name_cn || '',name_en:c.name_en || '',country_region:c.country_region || '',
          listing_status:['上市','非上市'].includes(c.listing_status) ? c.listing_status : '',
          listings:Array.isArray(c.listings) ? c.listings : [],aliases:c.aliases || [],ticker_hints:[],
          occurrences:[],combo:false,verified_master:true};
        this.companies.push(vm); this.byKey.set(vm.runtime_key,vm);
      });
      this.rows.forEach(row => {
        let c = this.byKey.get(row.company_id);
        if (!c && row.parsed) {
          const p = row.parsed;
          const matches = this.companies.filter(x => [x.name_cn,x.name_en,...x.aliases].filter(Boolean).some(n => [p.cn,p.en,p.cleaned].filter(Boolean).some(v => norm(n) === norm(v))));
          if (matches.length === 1) c = matches[0];
        }
        if (c) this.attach(c,row);
      });
    }
    fromLeaders() {
      const groups = [], aliasMap = new Map();
      this.rows.forEach(row => {
        const p = row.parsed; if (!p || !p.cleaned) return;
        const tokens = p.combo ? ['full:'+norm(p.cleaned)] : [p.cn && 'cn:'+norm(p.cn),p.en && 'en:'+norm(p.en)].filter(Boolean);
        const matches = [...new Set(tokens.map(t => aliasMap.get(t)).filter(Boolean))];
        let c = matches[0];
        if (!c) {c = {name_cn:p.cn,name_en:p.en,aliases:[],ticker_hints:[],countries:[],occurrences:[],combo:p.combo,listing_status:'',listings:[],verified_master:false};groups.push(c);}
        matches.slice(1).forEach(other => {
          other.occurrences.forEach(o => this.attach(c,o));
          c.aliases.push(...other.aliases); c.ticker_hints.push(...other.ticker_hints);c.countries.push(...other.countries);
          if (!c.name_cn) c.name_cn=other.name_cn;if(!c.name_en)c.name_en=other.name_en;
          for (const [token,target] of aliasMap) if (target===other) aliasMap.set(token,c);
          groups.splice(groups.indexOf(other),1);
        });
        if (!c.name_cn) c.name_cn=p.cn;if (!c.name_en)c.name_en=p.en;
        c.aliases.push(p.cn,p.en,p.cleaned,row.raw_name);c.ticker_hints.push(...p.ticker_hints);c.countries.push(...p.countries);
        this.attach(c,row);tokens.forEach(t => aliasMap.set(t,c));
      });
      groups.forEach(c => {
        c.aliases=[...new Set(c.aliases.filter(Boolean))];c.ticker_hints=[...new Set(c.ticker_hints)];
        c.country_region=[...new Set(c.countries)].join('/');
        c.name=c.name_cn || c.name_en;c.runtime_key='legacy:'+norm(c.name_en || c.name_cn);
        if (this.byKey.has(c.runtime_key)) c.runtime_key += ':'+groups.indexOf(c);
        this.byKey.set(c.runtime_key,c);this.companies.push(c);
      });
    }
    attach(c,row) {c.occurrences.push(row);this.rowMap.set(row,c);}
    find(key) {return this.byKey.get(key);}
    forLeader(leader, trackId) {
      const row = this.rows.find(r => (!trackId || r.track_id===trackId) && (leader.company_id ? r.company_id===leader.company_id : r.name===leader.name));
      return row ? this.rowMap.get(row) : null;
    }
    filter(filters, discovery) {
      return this.companies.filter(c => {
        if (discovery && (c.combo || !c.occurrences.length)) return false;
        const text=[c.name,c.name_en,...c.aliases,...c.ticker_hints,...c.listings.map(l=>l.ticker)].join(' ').toLowerCase();
        if (filters.search && !text.includes(filters.search.toLowerCase())) return false;
        if (!selected(filters.status,c.listing_status)) return false;
        if (selection(filters.market).length && !c.listings.some(l=>selected(filters.market,marketGroup(l.market)))) return false;
        if (selection(filters.track).length && !c.occurrences.some(o=>selected(filters.track,o.track_id))) return false;
        const domestic = c.country_region==='中国' || (!c.country_region && c.occurrences.some(o=>o.role==='china'));
        const overseas = c.country_region && !c.country_region.includes('中国') && !c.country_region.includes('/');
        const regions=selection(filters.region);
        if (regions.length && !((regions.includes('domestic') && domestic) ||
          (regions.includes('overseas') && (overseas || ['中国台湾','中国香港'].includes(c.country_region))))) return false;
        return true;
      });
    }
  }
  function marketGroup(market) {return ['A股','港股','美股'].includes(market) ? market : '其他海外';}
  function primaryListing(c) {return c.listings.find(l=>l.primary===true) || c.listings[0];}
  function recommendation(c,track) {
    const occurrence = c.occurrences.find(o=>selected(track,o.track_id));
    if (!occurrence) return '该公司为本图谱已收录的核心企业之一。';
    let reason=(occurrence.role==='china'?'中国':'全球')+'龙头名单收录企业，涉及'+occurrence.track_name+'。';
    if (c.listing_status==='上市') reason+='已上市，可持续跟踪公开披露。';
    else if (c.listing_status==='非上市') reason+='未上市，可持续观察IPO及资本运作进展。';
    return reason;
  }
  function draw(pool,count,random) {
    if (!Number.isInteger(count) || count<1) throw new Error('抽取数量无效');
    const unique=[...new Map(pool.map(c=>[c.runtime_key,c])).values()];
    if(unique.length<count)throw new Error('符合条件的企业只有'+unique.length+'家，请放宽筛选条件或选择单抽。');
    const copy=unique.slice();const rng=random || Math.random;
    for(let i=copy.length-1;i>0;i--){const n=rng();if(!Number.isFinite(n)||n<0||n>=1)throw new Error('随机源异常');const j=Math.floor(n*(i+1));[copy[i],copy[j]]=[copy[j],copy[i]];}
    return copy.slice(0,count);
  }
  function csvCell(value) {
    let s=String(value==null?'':value);
    if (/^[\s]*[=+@-]/.test(s)) s="'"+s;
    return '"'+s.replace(/"/g,'""')+'"';
  }
  function csvText(rows) {return '\ufeff'+rows.map(row=>row.map(csvCell).join(',')).join('\r\n');}
  function csvTables(data,kind,repo) {
    if(kind==='sources') {
      const keys=['source_id','org','title','publish_date','data_year','metric','caliber','region','url','access_date','type','level','remark'];
      return [{name:'sources.csv',rows:[keys,...data.sources.sources.map(s=>keys.map(k=>s[k] || ''))]}];
    }
    if(kind==='companies') {
      if(repo.mode!=='official')throw new Error('正式公司数据库尚未接入，当前无已核验公司主表可导出。');
      return [
        {name:'companies.csv',rows:[['company_id','name_cn','name_en','country_region','listing_status'],...repo.companies.map(c=>[c.runtime_key,c.name_cn,c.name_en,c.country_region,c.listing_status])]},
        {name:'company_listings.csv',rows:[['company_id','listing_id','market','exchange','ticker','primary'],...repo.companies.flatMap(c=>c.listings.map(l=>[c.runtime_key,l.listing_id,l.market,l.exchange,l.ticker,l.primary]))]},
        {name:'track_company_relations.csv',rows:[['company_id','dataset','track_id','sub_name','role','share','source_id'],...repo.companies.flatMap(c=>c.occurrences.map(o=>[c.runtime_key,o.dataset,o.track_id,o.sub_name,o.role,o.share,o.source_id]))]}
      ];
    }
    const tracks=data[kind].tracks;
    const trackKeys=['track_id','name','group','chain_position','sub_name','sub_note','market_value','market_unit','market_year','market_scope','market_source_id','localization_stage','localization_scope','localization_evidence','localization_source_id','note'];
    const trackRows=tracks.flatMap(t=>[{name:'',note:''},...(t.subs || [])].map(sub=>{
      const m=t.market_size || {},l=t.localization || {};
      return [t.id,t.name,t.group,t.chain_position,sub.name,sub.note,m.value,m.unit,m.year,m.scope,m.source_id,l.stage,l.scope,l.evidence,l.source_id,t.note];
    }));
    const leaders=leaderRows(data).filter(r=>r.dataset===kind).map(r=>[r.track_id,r.track_name,r.sub_name,r.role,r.parsed ? r.parsed.cleaned : '',r.raw_name,r.parsed ? r.parsed.countries.join('/') : r.country || '',r.share || '',r.products || '',r.tag || '',r.source_id || '',r.company_id || '',r.name || '',r.parsed ? r.parsed.ticker_hints.join(';') : '']);
    return [{name:kind+'_tracks.csv',rows:[trackKeys,...trackRows]},
      {name:kind+'_leaders.csv',rows:[['track_id','track_name','sub_name','role','name','raw_name','country','share','products','tag','source_id','company_id','source_text','ticker_hints'],...leaders]}];
  }
  // 编辑性跟踪范围；不是市场评级。只读取已有关系，绝不推断上市身份。
  const FOCUS_TRACKS=new Set(['eq-f-litho','eq-f-etch','eq-f-depo','ma-f-wafer','ma-f-resist','ma-f-cmp']);
  function cardCategory(company, trackId) {
    const rows=company.occurrences.filter(o=>selected(trackId,o.track_id));
    const core=rows.find(o=>FOCUS_TRACKS.has(o.track_id) && !o.sub_name && ['china','global'].includes(o.role));
    if(core)return {key:'gold',label:'核心龙头',stars:5,reason:'重点跟踪赛道 · 一级龙头名单',trackId:core.track_id,subName:core.sub_name};
    const follow=rows.find(o=>o.sub_name || /龙头|国产|替代|核心|第一/.test(o.tag || '') ||
      (company.listing_status==='非上市' && /重点|重要|核心/.test(o.tag || '')));
    if(follow)return {key:'purple',label:'重点跟踪',stars:4,reason:'细分龙头或重点产业标签',trackId:follow.track_id,subName:follow.sub_name};
    return {key:'blue',label:'产业观察',stars:3,reason:'产业图谱收录'};
  }
  // 仅三只既有试运行证券。此显示桥不修改公司上市身份，不读取ticker_hints猜代码。
  const PREVIEW_QUOTES={'legacy:AMEC':'688012.SH','legacy:ASMPT':'00522.HK','legacy:APPLIEDMATERIALS':'AMAT.US'};
  function quoteSymbol(company) {
    if(company.verified_master)return company.listing_status==='上市' ? primaryListing(company)?.ticker || '' : '';
    return PREVIEW_QUOTES[company.runtime_key] || '';
  }
  function quoteDisplay(quote) {
    const empty={price:'—',change:'—',pct:'—',cap:'—',trend:'flat'};
    if(!quote || !Number.isFinite(quote.price) || quote.price<=0 || quote.status==='unavailable')return empty;
    const signed=value=>Number.isFinite(value) ? (value>0?'+':'')+value.toFixed(2) : '—';
    return {price:quote.price.toFixed(2)+' '+(quote.currency || ''),change:signed(quote.change),pct:Number.isFinite(quote.change_pct)?signed(quote.change_pct)+'%':'—',
      cap:Number.isFinite(quote.market_cap)&&quote.market_cap>0?(quote.market_cap/1e8).toFixed(2)+'亿 '+(quote.currency || ''):'—',
      trend:Number.isFinite(quote.change_pct)?(quote.change_pct>0?'up':quote.change_pct<0?'down':'flat'):'flat'};
  }
  function preparationMessages(random) {
    const pools=[
      ['产业雷达上线，今天遇见谁？','把赛道地图摊开，下一位主角在哪？','研究搭子招募中，先来点新面孔！','给下一次研究留一点随机的快乐。','打开产业盲盒，灵感正在排队。','装备与材料集合，发现之旅出发！','今天的跟踪清单，想加哪位新朋友？','请接收一份来自产业深处的小惊喜。','赛道很多，先认识一家有趣的公司。','给研究清单松松土，种点新灵感。'],
      ['给候选清单洗个牌，惊喜正在路上…','熟悉的赛道，也能发现新面孔。','让装备和材料的名字，换个出场顺序。','翻翻已有名单，把下一站线索整理好。','给清单留一点未知，给研究留一点好奇。','不赶路，先看看产业地图里的风景。','候选企业排好队，马上轮到你认识。','把细分赛道的小线索，装进这次清单。','下一位研究搭子，正在候场。','寻找新面孔的快乐，就藏在这几秒。'],
      ['跟踪标签贴好啦，准备揭晓！','清单打包完毕，接住这份灵感！','研究搭子已就位，马上见面！','卡面已就位，三、二、一！','这一站的产业新朋友，马上出场。','惊喜不剧透，揭晓交给下一秒。','把好奇心准备好，你的清单来了。','新线索已装袋，欢迎开启下一次研究。','下一份研究灵感，即将送达。','出场顺序排好啦，开卡见！']
    ];
    const rng=random || Math.random;
    return pools.map(pool=>pool[Math.floor(rng()*pool.length)]);
  }
  return {CompanyRepository,leaderRows,parseName,pieces,norm,selection,selected,structureModel,marketGroup,primaryListing,recommendation,draw,csvText,csvTables,cardCategory,quoteSymbol,quoteDisplay,preparationMessages};
});
