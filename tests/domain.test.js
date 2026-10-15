'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const D=require('../02 交付/半导体装备与材料产业图谱/assets/js/domain');
const base=path.join(__dirname,'../02 交付/半导体装备与材料产业图谱/data');
const data=Object.fromEntries(['meta','equipment','materials','sources'].map(n=>[n,JSON.parse(fs.readFileSync(path.join(base,n+'.json'),'utf8'))]));
test('兼容模型覆盖一级二级引用，组合主体不进入抽卡',()=>{
  const repo=new D.CompanyRepository(data,null);
  assert.equal(repo.rows.length,408);assert.equal(repo.companies.length,249);
  assert.equal(repo.companies.reduce((sum,c)=>sum+c.occurrences.length,0),408);
  assert(repo.filter({},true).every(c=>!c.combo));
  assert.equal(repo.filter({status:'非上市'}).length,0);
  const amec=repo.companies.find(c=>c.name_en==='AMEC');assert.equal(amec.occurrences.length,2);assert.equal(amec.listing_status,'');
  assert(repo.filter({track:'eq-f-etch'}).some(c=>c.name_en==='AMEC'));
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
  assert.equal(tables[1].rows.length,294+1); // equipment 145一级 + 137二级 + 12并列增量。
  assert(tables[1].rows.some(r=>r[2]));assert(D.csvText(tables[0].rows).startsWith('\ufeff'));
  assert.equal(D.csvText([['=1+1','a"b','第一行\n第二行']]),'\ufeff"\'=1+1","a""b","第一行\n第二行"');
  assert(D.csvTables(data,'sources')[0].rows.length>1);
});
