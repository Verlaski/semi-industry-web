'use strict';
const cloudbase=require('@cloudbase/node-sdk');
const crypto=require('node:crypto');
const path=require('node:path');
const fs=require('node:fs');
const {SYMBOLS}=require('./market/providers');
const {freshness,databaseStore}=require('./market/service');
const revision=require('./data-revision.json');
const titles={overview:'半导体装备与材料产业链总览',equipment:'半导体装备产业图谱',materials:'半导体材料产业图谱',landscape:'半导体竞争格局与国产化'};
const validTracks=new Set(['equipment','materials'].flatMap(name=>JSON.parse(fs.readFileSync(path.join(__dirname,'data',name+'.json'),'utf8')).tracks.map(t=>t.id)));
const stages=['依赖进口','验证导入','份额提升','批量替代','国际领先'];
function cors(event) {
  const origin=event.headers?.origin || event.headers?.Origin || '';
  const allowed=(process.env.ALLOWED_ORIGINS || '').split(',');
  return {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
    ...(allowed.includes(origin)?{'Access-Control-Allow-Origin':origin,'Vary':'Origin'}:{}),
    'Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'Content-Type',
    'Access-Control-Expose-Headers':'Content-Disposition'};
}
function response(event,statusCode,body,extra) {return {statusCode,headers:{...cors(event),...extra},body:typeof body==='string'?body:JSON.stringify(body),isBase64Encoded:false};}
function httpError(code,message){const e=new Error(message);e.statusCode=code;return e;}
function sign(key,expires) {
  const secret=process.env.REPORT_SIGNING_SECRET;
  if(!secret || secret.length<32)throw new Error('Report signing configuration missing');
  return crypto.createHmac('sha256',secret).update(key+'|'+expires).digest('hex');
}
function verify(key,expires,signature) {
  if(!/^[a-f0-9]{64}$/.test(key||'') || !/^\d{10,13}$/.test(String(expires)) || !/^[a-f0-9]{64}$/.test(signature||''))return false;
  if(+expires<Date.now() || +expires>Date.now()+31*60000)return false;
  const expected=sign(key,expires);return crypto.timingSafeEqual(Buffer.from(expected,'hex'),Buffer.from(signature,'hex'));
}
async function getDoc(db,collection,id) {return (await db.collection(collection).doc(id).get()).data?.[0] || null;}
async function quotesFor(db,symbols) {
  const store=databaseStore(db);
  return Promise.all(symbols.map(async symbol=>{
    const quote=await store.get(symbol);
    if(!quote)return {symbol,name:SYMBOLS[symbol].name,market:SYMBOLS[symbol].market,currency:SYMBOLS[symbol].currency,
      price:null,previous_close:null,change:null,change_pct:null,market_cap:null,float_market_cap:null,total_shares:null,
      quote_time:null,fetched_at:null,provider:null,status:'unavailable'};
    const {_id,...safe}=quote;return {...safe,status:freshness(quote)};
  }));
}
function validatedRequest(body) {
  if(!body || typeof body!=='object'||Array.isArray(body) || Object.keys(body).some(k=>!['report_type','filters'].includes(k)))throw httpError(400,'报告请求格式不正确。');
  const report_type=body.report_type;
  if(!Object.hasOwn(titles,report_type))throw httpError(400,'暂不支持该报告类型。');
  const filters=body.filters || {};
  if(typeof filters!=='object'||Array.isArray(filters)||Object.keys(filters).some(k=>!['track_id','stage'].includes(k)))throw httpError(400,'不支持该筛选条件。');
  if(Object.values(filters).some(value=>typeof value!=='string'))throw httpError(400,'筛选条件必须为文字。');
  if(filters.track_id && !validTracks.has(filters.track_id))throw httpError(400,'赛道不存在。');
  if(filters.stage && !stages.includes(filters.stage))throw httpError(400,'国产化阶段不存在。');
  return {report_type,filters:Object.fromEntries(Object.entries(filters).filter(([,v])=>v).sort(([a],[b])=>a.localeCompare(b)))};
}
async function createReport(app,db,body) {
  const {report_type,filters}=validatedRequest(body);
  const quoteHour=new Date().toISOString().slice(0,13);
  const key=crypto.createHash('sha256').update(JSON.stringify([report_type,revision.data_version,revision.renderer_version,quoteHour,filters])).digest('hex');
  let cache=await getDoc(db,'report_cache',key);let cached=cache?.state==='ready';
  if(!cached) {
    const lock={state:'generating',created_at:Date.now(),expires_at:Date.now()+6*3600000,report_type,data_version:revision.data_version};
    if(cache?.state==='generating'&&Date.now()-cache.created_at<180000)throw httpError(503,'报告正在生成，请稍后再试。');
    if(!cache){
      try {await db.collection('report_cache').add({...lock,_id:key});}
      catch(error){throw httpError(503,'报告正在生成，请稍后再试。');}
    }else await db.collection('report_cache').doc(key).set(lock);
    try {
      const invoked=await app.callFunction({name:'generateReport',data:{report_type,filters,quotes:await quotesFor(db,Object.keys(SYMBOLS))}});
      const generated=typeof invoked.result==='string'?JSON.parse(invoked.result):invoked.result;
      if(!generated?.pdf_base64 || generated.data_version!==revision.data_version)throw new Error('Report revision mismatch');
      const raw=Buffer.from(generated.pdf_base64,'base64');
      if(raw.length>3000000 || raw.subarray(0,5).toString()!=='%PDF-')throw new Error('Invalid report binary');
      const chunks=generated.pdf_base64.match(/.{1,500000}/g) || [];
      const expires_at=Date.now()+6*3600000;
      for(let i=0;i<chunks.length;i++)await db.collection('report_files').doc(key+'-'+i).set({data:chunks[i],expires_at});
      const stamp=generated.generated_at.replace(/\D/g,'').slice(0,12);
      cache={state:'ready',report_type,data_version:generated.data_version,generated_at:generated.generated_at,
        filename:titles[report_type]+'_'+stamp.slice(0,8)+'_'+stamp.slice(8)+'.pdf',chunks:chunks.length,bytes:raw.length,
        quote_hour:quoteHour,filters,expires_at};
      await db.collection('report_cache').doc(key).set(cache);
    }catch(error){await db.collection('report_cache').doc(key).update({state:'failed'});console.error('Report generation failed',error.name || 'Error');throw httpError(503,'报告生成暂时失败，请稍后重试。');}
  }
  const expires=String(Date.now()+30*60000);
  const base=process.env.API_BASE;
  if(!base?.startsWith('https://'))throw new Error('API URL configuration missing');
  return {download_url:base+'/api/reports/file?key='+key+'&expires='+expires+'&signature='+sign(key,expires),
    filename:cache.filename,data_version:cache.data_version,generated_at:cache.generated_at,cached,expires_at:new Date(+expires).toISOString()};
}
exports.main=async function(event) {
  event=event || {};
  try {
    const method=(event.httpMethod || event.requestContext?.httpMethod || 'GET').toUpperCase();
    const requestedPath=event.path || event.rawPath || '/';
    if(method==='OPTIONS')return response(event,204,'');
    if(method==='GET'&&(requestedPath==='/'||requestedPath.endsWith('/health')))return response(event,200,{ok:true,version:'1.1.0',data_version:revision.data_version});
    const app=cloudbase.init({env:process.env.SCF_NAMESPACE || process.env.TCB_ENV});
    const db=app.database();const query=event.queryStringParameters || event.queryString || {};
    if(method==='GET'&&requestedPath.endsWith('/api/quotes')) {
      const symbols=String(query.symbols || Object.keys(SYMBOLS).join(',')).split(',');
      if(symbols.length>3 || symbols.some(s=>!SYMBOLS[s]))throw httpError(400,'目前仅支持三只测试证券。');
      return response(event,200,{quotes:await quotesFor(db,[...new Set(symbols)]),refresh_interval_seconds:3600});
    }
    if(method==='POST'&&requestedPath.endsWith('/api/reports')) {
      const body=typeof event.body==='string'?JSON.parse(event.isBase64Encoded?Buffer.from(event.body,'base64').toString('utf8'):event.body):event.body;
      return response(event,200,await createReport(app,db,body));
    }
    if(method==='GET'&&requestedPath.endsWith('/api/reports/file')) {
      if(!verify(query.key,query.expires,query.signature))throw httpError(403,'下载链接已过期或无效，请重新生成。');
      const cache=await getDoc(db,'report_cache',query.key);
      if(cache?.state!=='ready'||cache.expires_at<Date.now())throw httpError(404,'报告缓存已过期，请重新生成。');
      const parts=[];for(let i=0;i<cache.chunks;i++){
        const item=await getDoc(db,'report_files',query.key+'-'+i);if(!item)throw httpError(404,'报告缓存缺失，请重新生成。');parts.push(item.data);
      }
      return {...response(event,200,parts.join(''),{'Content-Type':'application/pdf','Content-Disposition':"attachment; filename=report.pdf; filename*=UTF-8''"+encodeURIComponent(cache.filename),'Cache-Control':'private, no-store'}),isBase64Encoded:true};
    }
    return response(event,404,{message:'请求的服务不存在。'});
  }catch(error){
    const code=error instanceof SyntaxError?400:error.statusCode || 503;
    return response(event,code,{message:error.statusCode?error.message:code===400?'请求格式不正确。':'服务暂时不可用，请稍后再试。'});
  }
};
exports._test={sign,verify,validatedRequest};
