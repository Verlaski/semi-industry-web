'use strict';
const {SYMBOLS,EastMoneyProvider,TencentProvider}=require('./providers');
function inTradingSession(symbol,now) {
  const spec=SYMBOLS[symbol];
  const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:spec.zone,weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(p=>[p.type,p.value]));
  if(['Sat','Sun'].includes(parts.weekday))return false;
  const minute=+parts.hour*60 + +parts.minute;
  if(spec.market==='美股')return minute>=570&&minute<960;
  return (minute>=570&&minute<(spec.market==='A股'?690:720)) || (minute>=780&&minute<(spec.market==='A股'?900:960));
}
function freshness(quote,now=new Date()) {
  if(!quote || !(quote.price>0) || !Number.isFinite(Date.parse(quote.quote_time)))return 'unavailable';
  if(quote.last_sync_failed)return 'stale';
  if(!inTradingSession(quote.symbol,now))return 'closed';
  return now-new Date(quote.quote_time)>90*60000 || now-new Date(quote.fetched_at)>90*60000 ? 'stale':'ok';
}
function providersFrom(order,fetcher) {
  const factories={EastMoney:()=>new EastMoneyProvider(fetcher),Tencent:()=>new TencentProvider(fetcher)};
  const names=(order || 'EastMoney,Tencent').split(',').map(s=>s.trim());
  if(!names.length||names.some(n=>!factories[n])||new Set(names).size!==names.length)throw new Error('Invalid provider order');
  return names.map(n=>factories[n]());
}
async function synchronize(symbols,store,providers=providersFrom(process.env.QUOTE_PROVIDERS),now=new Date()) {
  return Promise.all(symbols.map(async symbol=>{
    if(!SYMBOLS[symbol])throw new Error('Unsupported symbol');
    const last=await store.get(symbol);
    for(const provider of providers) {
      try {
        const quote=await provider.getQuote(symbol,now);
        if(last && Date.parse(quote.quote_time)<Date.parse(last.quote_time))throw new Error('Provider quote is older than cache');
        quote.status=freshness(quote,now);quote.last_sync_failed=false;
        await store.set(symbol,quote);return quote;
      } catch(error) {
        // 只记录供应商名和失败类别，避免响应/请求细节外泄。
        console.warn('Quote attempt failed',symbol,provider.constructor.name,error.name || 'Error');
      }
    }
    const result=last?{...last,status:'stale',last_sync_failed:true,last_attempt_at:now.toISOString()}:
      {symbol,name:SYMBOLS[symbol].name,market:SYMBOLS[symbol].market,currency:SYMBOLS[symbol].currency,price:null,
        previous_close:null,change:null,change_pct:null,market_cap:null,float_market_cap:null,total_shares:null,
        quote_time:null,fetched_at:null,last_attempt_at:now.toISOString(),provider:null,status:'unavailable',last_sync_failed:true};
    await store.set(symbol,result);return result;
  }));
}
function databaseStore(db) {
  return {async get(symbol){const r=await db.collection('quotes_latest').doc(symbol).get();return r.data?.[0] || null;},
    async set(symbol,quote){const {_id,...safe}=quote;await db.collection('quotes_latest').doc(symbol).set(safe);}};
}
module.exports={inTradingSession,freshness,providersFrom,synchronize,databaseStore};
