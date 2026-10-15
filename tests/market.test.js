'use strict';
const test=require('node:test');const assert=require('node:assert/strict');
const {EastMoneyProvider,TencentProvider,localTimeISO,standard}=require('../backend/market/providers');
const {freshness,synchronize,providersFrom}=require('../backend/market/service');
const now=new Date('2026-10-15T06:00:00Z');
function sample(symbol='688012.SH'){return standard(symbol,{price:100,previous_close:80,quote_time:now.toISOString(),market_cap:100000,total_shares:1000},'Fixture',now);}
test('EastMoney精度取f59，港美股不固定除100',()=>{
  const provider=new EastMoneyProvider();
  const quote=provider.parse('00522.HK',{data:{f57:'00522',f59:3,f43:135700,f60:149100,f86:now/1000,f116:56913697218.1,f117:56913697218.1,f84:419408233}},now);
  assert.equal(quote.price,135.7);assert.equal(quote.currency,'HKD');assert.equal(quote.quote_time,now.toISOString());
  assert.throws(()=>provider.parse('00522.HK',{data:{f57:'00522',f59:3,f43:0,f60:149100,f86:now/1000}},now),/Invalid quote/);
  assert.throws(()=>provider.parse('00522.HK',{data:{f57:'99999',f59:3}},now),/Wrong symbol/);
});
test('Tencent解析国别字段位置和市场时间，夏令时与冬令时不同',()=>{
  assert.equal(localTimeISO('2026-10-14 16:00:02','America/New_York'),'2026-10-14T20:00:02.000Z');
  assert.equal(localTimeISO('20260115160002','America/New_York'),'2026-01-15T21:00:02.000Z');
  const a=Array(74).fill('');a[3]='446.63';a[4]='464.24';a[30]='2026-10-14 16:00:02';a[44]='3534.10959';a[45]='3544.44426';a[62]='793597443';
  const q=new TencentProvider().parse('AMAT.US','v_usAMAT="'+a.join('~')+'";',now);
  assert.equal(q.price,446.63);assert.equal(q.total_shares,793597443);assert.equal(q.market_cap,354444426000);
});
test('90分钟stale只适用于预期交易时段，收盘后允许旧收盘价',()=>{
  const q=sample();assert.equal(freshness(q,now),'ok');
  assert.equal(freshness({...q,quote_time:'2026-10-15T03:00:00Z'},now),'stale');
  assert.equal(freshness(q,new Date('2026-10-15T10:00:00Z')),'closed');
  assert.equal(freshness(sample('AMAT.US'),now),'closed');
  assert.equal(freshness({...q,last_sync_failed:true},now),'stale');
});
test('主备切换、双失败保留最后有效值，不用抓取时间冒充行情时间',async()=>{
  const map=new Map();const store={get:async s=>map.get(s),set:async(s,q)=>map.set(s,q)};
  const bad={getQuote:async()=>{throw new Error('offline');}};
  const good={getQuote:async()=>sample()};
  await synchronize(['688012.SH'],store,[bad,good],now);assert.equal(map.get('688012.SH').price,100);
  const later=new Date(now.getTime()+3600000);await synchronize(['688012.SH'],store,[bad,bad],later);
  assert.equal(map.get('688012.SH').price,100);assert.equal(map.get('688012.SH').fetched_at,now.toISOString());assert.equal(map.get('688012.SH').status,'stale');
  const noData=await synchronize(['00522.HK'],store,[bad],later);assert.equal(noData[0].price,null);assert.equal(noData[0].status,'unavailable');
  assert.throws(()=>providersFrom('bogus'),/Invalid provider/);assert.equal(providersFrom('Tencent,EastMoney')[0].constructor.name,'TencentProvider');
});
