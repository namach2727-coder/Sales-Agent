const assert=require('node:assert/strict');const fs=require('node:fs');const {JSDOM}=require('jsdom');
const root=__dirname+'/web/';const html=fs.readFileSync(root+'showcase.html','utf8');const source=fs.readFileSync(root+'showcase.js','utf8');
const flush=()=>new Promise(r=>setImmediate(r));
(async()=>{
 const dom=new JSDOM(html,{url:'https://example.invalid/showcase',runScripts:'outside-only'});const w=dom.window,d=w.document;let calls=0;
 w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};w.HTMLDialogElement.prototype.close=function(){this.open=false;};
 const items=[{id:'shop',icon:'🛍',title:'فروشگاه آنلاین',description:'فروش و پیگیری',features:['دریافت سفارش'],choices:['محصولات','پیگیری']},{id:'other',icon:'✨',title:'ایدهٔ دیگر',description:'شرح ایده',features:['بررسی'],choices:['معرفی','امکانات']}];
 w.fetch=async()=>{calls++;return {ok:true,json:async()=>({industries:items,bot_url:'https://t.me/sample_showcase_bot',examples_are_simulated:true})};};
 w.eval(source);await flush();assert.equal(calls,1);assert.equal(d.querySelectorAll('.industry-card').length,2);
 const search=d.getElementById('search');search.focus();search.value='فروشگاه';search.dispatchEvent(new w.Event('input'));assert.equal(d.activeElement,search);assert.equal(d.querySelectorAll('.industry-card:not([hidden])').length,1);
 d.querySelector('.industry-card button').click();assert.equal(d.getElementById('preview').open,true);assert.equal(d.getElementById('request-category').href,'https://t.me/sample_showcase_bot?start=idea_shop');
 d.querySelector('#demo-options button').click();assert.match(d.getElementById('demo-text').textContent,/هیچ درخواست/);assert.equal(calls,1,'demo never submits or calls Telegram');
 d.getElementById('close-preview').click();assert.equal(d.getElementById('preview').open,false);
 search.value='<script>';search.dispatchEvent(new w.Event('input'));assert.equal(d.getElementById('empty').hidden,false);d.getElementById('show-other').click();assert.match(d.getElementById('preview-title').textContent,/ایده/);
 assert.equal(d.querySelectorAll('form').length,0);assert(!html.includes('user-scalable=no'));assert(!html.includes('maximum-scale=1'));
 dom.window.close();console.log('Own showcase catalog/search/focus/demo/no-send/deep-link: PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
