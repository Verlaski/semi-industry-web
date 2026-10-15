'use strict';
// 证券注册表由 tools/build_quote_registry.py 依据正式公司主表 companies.json 生成，
// 手工改动会被下次生成覆盖；listing_id 为正式公司主表上市身份外键。
const SYMBOLS = Object.freeze(require('./symbols.generated.js'));
function numeric(value) {if(value===null||value===undefined||value===''||value==='-')return null;const n=Number(value);return Number.isFinite(n)?n:null;}
function localTimeISO(text,zone) {
  const parts=text.replace(/\D/g,'').match(/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$/);
  if(!parts)throw new Error('Invalid provider quote time');
  const wanted=Date.UTC(...[Number(parts[1]),Number(parts[2])-1,...parts.slice(3).map(Number)]);
  let time=wanted;
  const fmt=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
  for(let i=0;i<3;i++){
    const p=Object.fromEntries(fmt.formatToParts(new Date(time)).map(x=>[x.type,x.value]));
    const current=Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute,+p.second);
    time+=wanted-current;
  }
  return new Date(time).toISOString();
}
function standard(symbol,fields,provider,now) {
  const meta=SYMBOLS[symbol];
  const price=numeric(fields.price),previous=numeric(fields.previous_close);
  const timestamp=new Date(fields.quote_time).getTime();
  if(!(price>0)||!(previous>0)||!Number.isFinite(timestamp)||timestamp>now.getTime()+300000)throw new Error('Invalid quote payload');
  return {symbol,name:meta.name,market:meta.market,price,previous_close:previous,
    change:Number((price-previous).toFixed(6)),change_pct:Number(((price/previous-1)*100).toFixed(6)),
    market_cap:numeric(fields.market_cap),float_market_cap:numeric(fields.float_market_cap),total_shares:numeric(fields.total_shares),
    currency:meta.currency,quote_time:new Date(timestamp).toISOString(),fetched_at:now.toISOString(),provider,status:'ok'};
}
async function getResponse(fetcher,url,headers) {
  const response=await fetcher(url,{headers,signal:AbortSignal.timeout(8000)});
  if(!response.ok)throw new Error('Provider HTTP '+response.status);
  return response;
}
class MarketDataProvider {
  constructor(fetcher=fetch){this.fetcher=fetcher;}
  async getQuote(){throw new Error('Provider must implement getQuote');}
  async getQuotes(symbols,now=new Date()){return Promise.all(symbols.map(symbol=>this.getQuote(symbol,now)));}
}
class EastMoneyProvider extends MarketDataProvider {
  parse(symbol,payload,now=new Date()) {
    const d=payload.data;if(!d||!Number.isInteger(d.f59)||d.f59<0||d.f59>5)throw new Error('Missing EastMoney precision');
    const scale=10**d.f59;
    const expected=SYMBOLS[symbol].eastmoney.split('.')[1];
    if(String(d.f57).toUpperCase()!==expected.toUpperCase())throw new Error('Wrong symbol from provider');
    return standard(symbol,{price:numeric(d.f43)===null?null:d.f43/scale,previous_close:numeric(d.f60)===null?null:d.f60/scale,
      quote_time:new Date(Number(d.f86)*1000).toISOString(),market_cap:d.f116,float_market_cap:d.f117,total_shares:d.f84},'EastMoney',now);
  }
  async getQuote(symbol,now=new Date()) {
    if(!SYMBOLS[symbol])throw new Error('Unsupported symbol');
    const url='https://push2.eastmoney.com/api/qt/stock/get?secid='+SYMBOLS[symbol].eastmoney+'&fields=f43,f57,f58,f59,f60,f84,f86,f116,f117';
    const response=await getResponse(this.fetcher,url,{'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'});
    return this.parse(symbol,await response.json(),now);
  }
}
class TencentProvider extends MarketDataProvider {
  parse(symbol,text,now=new Date()) {
    const id=SYMBOLS[symbol].tencent;
    const match=new RegExp('v_'+id+'="([^"]+)"').exec(text);if(!match)throw new Error('Tencent symbol missing');
    const a=match[1].split('~');if(a.length<46)throw new Error('Tencent payload incomplete');
    const shareIndex=/\.(SH|SZ|BJ)$/.test(symbol)?73:symbol.endsWith('.HK')?70:62;
    const cap=value=>numeric(value)===null?null:Number((Number(value)*1e8).toFixed(2));
    return standard(symbol,{price:a[3],previous_close:a[4],quote_time:localTimeISO(a[30],SYMBOLS[symbol].zone),
      market_cap:cap(a[45]),float_market_cap:cap(a[44]),total_shares:a[shareIndex]},'Tencent',now);
  }
  async getQuote(symbol,now=new Date()) {
    if(!SYMBOLS[symbol])throw new Error('Unsupported symbol');
    const response=await getResponse(this.fetcher,'https://qt.gtimg.cn/q='+SYMBOLS[symbol].tencent,{'User-Agent':'Mozilla/5.0'});
    return this.parse(symbol,new TextDecoder('gb18030').decode(await response.arrayBuffer()),now);
  }
}
module.exports={SYMBOLS,numeric,localTimeISO,standard,MarketDataProvider,EastMoneyProvider,TencentProvider};
