/* DOM behavior only: synthetic identity/fetch, no Telegram or provider network. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const root = __dirname;
const html = fs.readFileSync(path.join(root, 'web/index.html'), 'utf8');
const script = fs.readFileSync(path.join(root, 'web/app.js'), 'utf8');
async function until(fn) { for (let i=0;i<100;i++) { if (fn()) return; await new Promise(setImmediate); } throw new Error('UI did not reach expected state'); }
function field(scope, text) { const label = [...scope.querySelectorAll('label')].find(l => l.firstChild?.textContent === text); assert(label, text); return label.querySelector('input,select,textarea'); }
function button(scope, text) { const b=[...scope.querySelectorAll('button')].find(b => b.textContent===text); assert(b,text); return b; }
async function main() {
  const dom = new JSDOM(html, {runScripts:'outside-only', url:'https://telbot.invalid', pretendToBeVisual:true});
  const w=dom.window; const requests=[];
  let saved, config={published:{version:2,greeting:'Hello',fallback_reply:'Fallback'},api_actions_ready:true,external_api_enabled:false,rules:[
    {id:'text-old',keyword:'قیمت',response_text:'Price',match_mode:'exact',action_type:'text',enabled:true},
    {id:'api-old',keyword:'موجودی',response_text:'Unavailable',match_mode:'contains',action_type:'api',enabled:true,
      api:{url:'https://api.example.com/stock',method:'GET',params:{},json_body:{},response_path:'data.text',auth_mode:'bearer',auth_header:'X-API-Key',credential_present:true}},
  ]};
  w.Telegram={WebApp:{initData:'synthetic-init',ready(){},expand(){}}};
  w.fetch=async (url,options={}) => {
    requests.push({url,options}); let body;
    if (url.endsWith('/me/tenants')) body=[{id:'tenant',display_name:'Synthetic workspace',role:'owner'}];
    else if (url.endsWith('/bots')) body=[{id:'bot',username:'ExampleBot',status:'active',is_managed:true,credential_ready:true}];
    else if (url.endsWith('/config')) body=config;
    else if (url.endsWith('/configs')) { saved=JSON.parse(options.body); body={id:'draft',version:3}; }
    else if (url.includes('/publish?expected_version=2')) {
      config={...config,published:{version:3,greeting:saved.greeting,fallback_reply:saved.fallback_reply},rules:saved.rules.map((r,i)=>{
        const result={...r,id:'new-'+i}; if(result.api){result.api={...result.api,credential_present:true};delete result.api.credential;} return result;
      })};body={id:'draft',version:3,state:'published'};
    } else throw new Error('Unexpected fetch '+url);
    return {ok:true,status:200,headers:{get:()=>null},json:async()=>JSON.parse(JSON.stringify(body))};
  };
  w.eval(script);
  await until(()=>w.document.querySelector('.bot-actions button'));
  button(w.document,'تنظیم پیام‌های ربات').click();
  await until(()=>w.document.querySelectorAll('.rule-card').length===2);
  const panel=w.document.querySelector('.reply-editor');
  const existingApi=panel.querySelectorAll('.rule-card')[1];
  assert.equal(field(existingApi,'کلید اتصال — در پاسخ سرور نمایش داده نمی‌شود').value,'');
  assert.match(field(existingApi,'کلید اتصال — در پاسخ سرور نمایش داده نمی‌شود').placeholder,/ذخیره شده/);
  button(panel,'+ افزودن پاسخ').click();
  assert.equal(panel.querySelectorAll('.rule-card').length,3);
  const newCard=panel.querySelectorAll('.rule-card')[2];
  field(newCard,'کلمه یا عبارت محرک').value='آدرس';
  field(newCard,'متن پاسخ / پیام جایگزین در خطای API').value='Address';
  field(newCard,'کلمه یا عبارت محرک').dispatchEvent(new w.Event('input',{bubbles:true}));
  button(newCard,'بالاتر').click();
  assert.deepEqual([...panel.querySelectorAll('.rule-card')].map(c=>field(c,'کلمه یا عبارت محرک').value),['قیمت','آدرس','موجودی']);
  const form=panel.querySelector('form'); form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
  await until(()=>saved && field(panel,'پیام شروع /start').disabled===false && panel.textContent.includes('همهٔ پاسخ‌ها منتشر شدند'));
  assert.equal(saved.rules.length,3);assert.equal(saved.base_version,2);
  assert.equal(saved.rules[2].source_rule_id,'api-old');assert.equal(saved.rules[2].api.credential,null);
  assert.equal(saved.rules[2].api.include_message,false);
  assert.equal(panel.querySelectorAll('.rule-card').length,3);
  const refreshed=panel.querySelectorAll('.rule-card')[2];
  assert.equal(field(refreshed,'کلید اتصال — در پاسخ سرور نمایش داده نمی‌شود').value,'');
  button(refreshed,'حذف از نسخهٔ جدید').click(); assert.equal(panel.querySelectorAll('.rule-card').length,2);
  button(panel,'بستن تنظیمات').click();assert.equal(w.document.querySelector('.reply-editor'),null);
  assert.equal(button(w.document,'تنظیم پیام‌های ربات').disabled,false);
  assert.equal(requests.filter(r=>r.url.endsWith('/configs')).length,1);
  assert.equal(requests.filter(r=>r.url.includes('/publish?')).length,1);
  dom.window.close();console.log('TelBot DOM editor behavior: PASS');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
