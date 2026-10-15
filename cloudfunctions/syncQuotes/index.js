'use strict';
const cloudbase=require('@cloudbase/node-sdk');
const {SYMBOLS}=require('./market/providers');
const {synchronize,databaseStore}=require('./market/service');
exports.main=async function () {
  const app=cloudbase.init({env:process.env.SCF_NAMESPACE || process.env.TCB_ENV});
  const db=app.database();const quotes=await synchronize(Object.keys(SYMBOLS),databaseStore(db));
  for(const collection of ['report_cache','report_files']) {
    await db.collection(collection).where({expires_at:db.command.lt(Date.now())}).remove();
  }
  return {ok:quotes.every(q=>q.price>0),synced_at:new Date().toISOString(),quotes};
};
