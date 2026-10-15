'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const D=require('../02 交付/半导体装备与材料产业图谱/assets/js/domain');
const base=path.join(__dirname,'../02 交付/半导体装备与材料产业图谱/data');
const data=Object.fromEntries(['meta','equipment','materials','sources'].map(n=>[n,JSON.parse(fs.readFileSync(path.join(base,n+'.json'),'utf8'))]));
test('结构模型完整收录真实赛道、原料与下游，新增分组无需改图',()=>{
  const model=D.structureModel(data);
  const tracks=model.lanes.flatMap(l=>l.groups.flatMap(g=>g.tracks));
  const actual=[...data.equipment.tracks,...data.materials.tracks];
  assert.deepEqual(tracks.map(t=>t.id).sort(),actual.map(t=>t.id).sort());
  assert.equal(new Set(tracks.map(t=>t.id)).size,actual.length);
  assert.deepEqual(model.baseMaterials,data.materials.base_materials);
  assert.deepEqual(model.downstream,data.meta.downstream.nodes);
  const extended={...data,equipment:{...data.equipment,tracks:[...data.equipment.tracks,{id:'future',name:'新增赛道',group:'新增分组'}]}};
  assert.equal(D.structureModel(extended).lanes[0].groups.at(-1).tracks[0].id,'future');
});
test('多选组内OR、组间AND，清空不限，上市未知不能混入状态筛选',()=>{
  const fixture={equipment:{tracks:[{id:'a',name:'A',global_leaders:[{company_id:'cn'},{company_id:'us'},{company_id:'unknown'}]},{id:'b',name:'B',china_leaders:[{company_id:'private'}]}]},materials:{tracks:[]}};
  const repo=new D.CompanyRepository(fixture,{companies:[
    {company_id:'cn',name_cn:'国内上市',country_region:'中国',listing_status:'上市'},
    {company_id:'us',name_en:'Overseas',country_region:'美国',listing_status:'上市'},
    {company_id:'private',name_cn:'国内非上市',country_region:'中国',listing_status:'非上市'},
    {company_id:'unknown',name_cn:'未知',country_region:'中国',listing_status:''}
  ]});
  const ids=f=>repo.filter(f,true).map(c=>c.runtime_key).sort();
  assert.deepEqual(ids({region:['domestic'],track:['a','b'],status:['上市','非上市']}),['cn','private']);
  assert.deepEqual(ids({region:['domestic','overseas'],status:['上市']}),['cn','us']);
  assert.deepEqual(ids({track:['b']}),['private']);
  assert.deepEqual(ids({region:[],status:[],track:[]}),ids({}));
  assert.deepEqual(ids({region:'domestic',track:'a',status:'上市'}),['cn']);
});
test('多选赛道的卡面与推荐文案只使用选中关系',()=>{
  const c={occurrences:[{track_id:'eq-f-etch',track_name:'刻蚀',role:'global',sub_name:''},{track_id:'other',track_name:'其他',role:'china',sub_name:'细分'},{track_id:'blue',track_name:'观察',role:'global'}]};
  assert.equal(D.cardCategory(c,['other','blue']).key,'purple');
  assert.equal(D.cardCategory(c,['other','blue']).trackId,'other');
  assert.match(D.recommendation(c,['blue','other']),/其他/);
  assert.doesNotMatch(D.recommendation(c,['blue','other']),/刻蚀/);
  assert.equal(D.cardCategory(c,[]).key,'gold');
});
test('正式主表按主上市地ticker关联行情，兼容模式不提供关联且不猜测证券代码',()=>{
  const official=JSON.parse(fs.readFileSync(path.join(base,'companies.json'),'utf8'));
  const repo=new D.CompanyRepository(data,official);
  assert.equal(repo.mode,'official');
  assert.equal(D.quoteSymbol(repo.find('AMEC')),'688012.SH');
  assert.equal(D.quoteSymbol(repo.find('ACMSH')),'688082.SH');
  const compat=new D.CompanyRepository(data,null);
  assert.equal(compat.companies.filter(c=>D.quoteSymbol(c)).length,0);
  assert.equal(D.quoteSymbol({runtime_key:'other',ticker_hints:['688012'],listings:[]}), '');
  assert.equal(D.quoteSymbol({verified_master:true,listing_status:'',listings:[]}), '');
  assert.equal(D.quoteSymbol({verified_master:true,listing_status:'上市',listings:[{ticker:'00522.HK'}]}),'00522.HK');
});
test('行情红涨绿跌对应正负数，市值保留币种，缺失数据不填0',()=>{
  const q={price:100,change:2,change_pct:2.04,market_cap:1.2e10,currency:'HKD',status:'closed'};
  assert.deepEqual(D.quoteDisplay(q),{price:'100.00 HKD',change:'+2.00',pct:'+2.04%',cap:'120.00亿 HKD',trend:'up'});
  assert.equal(D.quoteDisplay({...q,change:-2,change_pct:-2}).trend,'down');
  assert.equal(D.quoteDisplay({...q,change_pct:0}).pct,'0.00%');
  assert.equal(D.quoteDisplay({...q,price:null}).price,'—');
  assert.equal(D.quoteDisplay({...q,market_cap:null}).cap,'—');
  assert.equal(D.quoteDisplay(null).price,'—');
});
test('卡面等级取已有赛道关系，筛选范围生效，未知上市身份不影响等级',()=>{
  const c={listing_status:'',occurrences:[{track_id:'eq-f-etch',role:'global',sub_name:''},{track_id:'other',role:'china',sub_name:'细分'}]};
  assert.equal(D.cardCategory(c).key,'gold');
  assert.equal(D.cardCategory(c).trackId,'eq-f-etch');
  assert.equal(D.cardCategory(c,'eq-f-etch').stars,5);
  assert.equal(D.cardCategory(c,'other').key,'purple');
  assert.equal(D.cardCategory(c,'missing').key,'blue');
  assert.equal(D.cardCategory({occurrences:[]}).key,'blue');
  assert.equal(D.cardCategory({occurrences:[{track_id:'other',tag:'国产MFC龙头'}]}).key,'purple');
  assert.equal(D.cardCategory({listing_status:'非上市',occurrences:[{track_id:'other'}]}).key,'blue');
});
test('正式主表全量接入：一级二级引用全部attach，无组合主体',()=>{
  const official=JSON.parse(fs.readFileSync(path.join(base,'companies.json'),'utf8'));
  const repo=new D.CompanyRepository(data,official);
  // 迁移后 426 条引用（原 408 + 斜杠组合拆分增量），全部经 company_id attach
  assert.equal(repo.rows.length,426);
  assert.equal(repo.companies.length,245);
  assert.equal(repo.companies.reduce((sum,c)=>sum+c.occurrences.length,0),426);
  assert(repo.filter({},true).every(c=>!c.combo));
  assert(repo.filter({status:'非上市'}).length>0);
  const amec=repo.find('AMEC');assert(amec.occurrences.length>=2);
  assert(repo.filter({track:'eq-f-etch'}).some(c=>c.runtime_key==='AMEC'));
});
test('公司库只在404时回退，错误的正式库不悄悄替代',async()=>{
  const fallback=await D.CompanyRepository.load(data,async()=>({status:404}));assert.equal(fallback.mode,'compatibility');
  await assert.rejects(()=>D.CompanyRepository.load(data,async()=>({status:503,ok:false})),/暂不可用/);
  assert.throws(()=>new D.CompanyRepository(data,{companies:{}}),/格式/);
});
test('正式主库支持company_id引用、上市身份、多地上市和别名',()=>{
  const fixture={equipment:{tracks:[{id:'eq',name:'设备',china_leaders:[{company_id:'CONFIRMED',share:'来源口径',source_id:'S'}]}]},materials:{tracks:[]}};
  const repo=new D.CompanyRepository(fixture,{companies:[{company_id:'CONFIRMED',name_cn:'测试公司',aliases:['别名'],country_region:'中国',listing_status:'上市',listings:[{market:'美股',ticker:'X.US'},{market:'A股',ticker:'000001.SZ',primary:true}]}]});
  assert.equal(repo.filter({search:'别名',market:'A股',status:'上市',track:'eq'}).length,1);
  assert.equal(D.primaryListing(repo.companies[0]).ticker,'000001.SZ');assert.equal(repo.companies[0].occurrences.length,1);
  assert.equal(D.csvTables(fixture,'companies',repo).length,3);
});
test('十连无放回、条件池不足提示、均匀洗牌没有越界',()=>{
  const pool=Array.from({length:20},(_,i)=>({runtime_key:String(i)}));
  const drawn=D.draw(pool,10,()=>.5);assert.equal(new Set(drawn.map(c=>c.runtime_key)).size,10);
  assert.throws(()=>D.draw(pool.slice(0,2),10),/只有2家/);assert.throws(()=>D.draw(pool,10,()=>1),/随机源/);
});
test('CSV有BOM、标准转义、公式防护；赛道和leader拆表含二级',()=>{
  const tables=D.csvTables(data,'equipment');assert.equal(tables.length,2);
  assert.equal(tables[1].rows.length,307+1); // equipment 迁移后 307 条 leader 引用（含组合拆分增量）。
  assert(tables[1].rows.some(r=>r[2]));assert(D.csvText(tables[0].rows).startsWith('\ufeff'));
  assert.equal(D.csvText([['=1+1','a"b','第一行\n第二行']]),'\ufeff"\'=1+1","a""b","第一行\n第二行"');
  assert(D.csvTables(data,'sources')[0].rows.length>1);
});
