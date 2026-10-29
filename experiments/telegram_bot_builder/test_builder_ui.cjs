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
  const w=dom.window; const requests=[]; let releasePreview;
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
    else if (url.endsWith('/preview')) {
      const snapshot=JSON.parse(options.body);
      if (snapshot.text==='منتظر') await new Promise(resolve=>{releasePreview=resolve;});
      body=snapshot.text==='موجودی' ? {action:'api',rule_index:3,fallback_text:'Unavailable',executed:false} :
        snapshot.text==='/start' ? {action:'greeting',response_text:snapshot.greeting,executed:false} :
        {action:'text',rule_index:2,response_text:'<b>Unsaved address</b>',executed:false};
    }
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
  const tabs=[...panel.querySelectorAll('[role="tab"]')];
  assert.deepEqual(tabs.map(tab=>tab.textContent),['پیام شروع','پاسخ‌ها','آزمایش']);
  assert.equal(tabs.filter(tab=>tab.getAttribute('aria-selected')==='true').length,1);
  assert.equal(tabs[1].getAttribute('aria-selected'),'true');
  assert.equal(panel.querySelectorAll('.editor-pane:not([hidden])').length,1);
  assert.equal(w.document.getElementById('onboarding-intro').hidden,true);
  assert.equal(w.document.getElementById('onboarding-steps').hidden,true);
  assert.notEqual(w.document.activeElement.tagName,'INPUT');
  assert.notEqual(w.document.activeElement.tagName,'TEXTAREA');
  const existingApi=panel.querySelectorAll('.rule-card')[1];
  assert.equal(field(existingApi,'کلید دسترسی').value,'');
  assert.match(field(existingApi,'کلید دسترسی').placeholder,/ذخیره شده/);
  button(panel,'+ افزودن پاسخ').click();
  assert.equal(panel.querySelectorAll('.rule-card').length,3);
  const newCard=panel.querySelectorAll('.rule-card')[2];
  const typing=field(newCard,'کاربر چه می‌نویسد؟');
  const moves=new w.MutationObserver(()=>{}); moves.observe(panel.querySelector('.rules-list'),{childList:true});
  typing.focus();
  for (const letter of 'آدرس') {
    typing.value+=letter;
    typing.setSelectionRange(typing.value.length,typing.value.length);
    typing.dispatchEvent(new w.InputEvent('input',{bubbles:true,data:letter,inputType:'insertText'}));
    assert.equal(w.document.activeElement,typing,'Typing must not detach or blur the focused rule input');
    assert.equal(typing.selectionStart,typing.value.length,'Caret must stay in the typed input');
  }
  typing.dispatchEvent(new w.CompositionEvent('compositionstart',{bubbles:true}));
  typing.dispatchEvent(new w.InputEvent('input',{bubbles:true,data:'س',isComposing:true}));
  typing.dispatchEvent(new w.CompositionEvent('compositionend',{bubbles:true,data:'س'}));
  assert.equal(w.document.activeElement,typing);
  assert.equal(moves.takeRecords().length,0,'Typing/composition must not move cards in the rule list'); moves.disconnect();
  const requestsBeforeReturn=requests.length;
  w.document.dispatchEvent(new w.Event('visibilitychange'));
  await new Promise(setImmediate);
  assert.equal(requests.length,requestsBeforeReturn,'Returning to app must preserve the open editor without a list refresh');
  assert.equal(w.document.activeElement,typing);
  button(w.document,'بررسی وضعیت ربات‌ها').click();
  await new Promise(setImmediate);
  assert.equal(requests.length,requestsBeforeReturn);
  assert.equal(w.document.querySelector('.reply-editor'),panel);
  field(newCard,'کاربر چه می‌نویسد؟').value='آدرس';
  field(newCard,'ربات چه پاسخی بدهد؟').value='Address';
  field(newCard,'کاربر چه می‌نویسد؟').dispatchEvent(new w.Event('input',{bubbles:true}));
  button(newCard,'بالاتر').click();
  assert.deepEqual([...panel.querySelectorAll('.rule-card')].map(c=>field(c,'کاربر چه می‌نویسد؟').value),['قیمت','آدرس','موجودی']);
  button(panel,'پیام شروع').click();
  assert.equal(field(panel,'پیام خوش‌آمدگویی').closest('.editor-pane').hidden,false);
  const welcome=field(panel,'پیام خوش‌آمدگویی'); welcome.focus();
  welcome.value+='ی'; welcome.dispatchEvent(new w.InputEvent('input',{bubbles:true,data:'ی'}));
  assert.equal(w.document.activeElement,welcome);
  button(panel,'پاسخ‌ها').click();
  assert.equal(typing.value,'آدرس','Tab navigation must retain unsaved field state');
  existingApi.open=true;
  existingApi.querySelectorAll('details').forEach(details=>{details.open=true;});
  for (const control of existingApi.querySelectorAll('input:not([type="checkbox"]),textarea')) {
    const original=control.value; control.focus(); control.value+='ی'; control.dispatchEvent(new w.InputEvent('input',{bubbles:true,data:'ی'}));
    assert.equal(w.document.activeElement,control,'API typing must preserve focus too');
    control.value=original; control.dispatchEvent(new w.Event('input',{bubbles:true}));
  }
  const fallback=field(panel,'پاسخ به پیام‌های دیگر'); fallback.value='';
  button(panel,'آزمایش').click(); button(panel,'ذخیره پاسخ‌ها').click();
  assert.equal(w.document.activeElement,fallback,'Validation must open the correct pane and collapsed field');
  assert.equal(fallback.closest('details').open,true);
  assert.equal(fallback.closest('.editor-pane').hidden,false);
  assert.equal(saved,undefined);
  fallback.value='Fallback'; fallback.dispatchEvent(new w.Event('input',{bubbles:true}));
  const params=field(existingApi,'پارامترهای Query (JSON)'); params.value='{'; params.closest('details').open=false;
  button(panel,'آزمایش').click(); button(panel,'ذخیره پاسخ‌ها').click();
  assert.equal(w.document.activeElement,params); assert.equal(params.closest('details').open,true);
  assert.equal(saved,undefined); params.value='{}'; params.dispatchEvent(new w.Event('input',{bubbles:true}));
  button(panel,'آزمایش').click();
  const preview=panel.querySelector('.response-preview'); assert.equal(preview.hidden,false);
  const previewText=field(preview,'پیام آزمایشی'), previewButton=button(preview,'نمایش پیش‌نمایش'), output=preview.querySelector('.preview-output');
  assert.equal(previewText.closest('form'),null);
  field(panel,'پیام خوش‌آمدگویی').value='Unsaved greeting';
  field(existingApi,'کلید دسترسی').value='synthetic-new-key';
  previewText.value='/start'; previewButton.click();
  await until(()=>!previewButton.disabled && output.textContent.includes('Unsaved greeting'));
  let previewBody=JSON.parse(requests.filter(r=>r.url.endsWith('/preview')).at(-1).options.body);
  assert.equal(previewBody.greeting,'Unsaved greeting');
  assert.equal(previewBody.rules[2].source_rule_id,'api-old');
  assert.equal(Object.hasOwn(previewBody.rules[2].api,'credential'),false);
  assert.equal(field(existingApi,'کلید دسترسی').value,'synthetic-new-key');
  assert.equal(saved,undefined); // preview neither creates a draft nor publishes
  previewText.value='آدرس'; previewText.dispatchEvent(new w.Event('input',{bubbles:true})); previewButton.click();
  await until(()=>!previewButton.disabled && output.textContent.includes('Unsaved address'));
  assert.equal(output.querySelector('b'),null); // response content remains plain text
  previewText.value='موجودی'; previewText.dispatchEvent(new w.Event('input',{bubbles:true})); previewButton.click();
  await until(()=>!previewButton.disabled && output.textContent.includes('فراخوانی نشد'));
  assert.match(output.textContent,/Unavailable/); assert.match(output.textContent,/پاسخ 3/);
  previewText.value='منتظر'; previewText.dispatchEvent(new w.Event('input',{bubbles:true})); previewButton.click();
  await until(()=>releasePreview);
  field(newCard,'ربات چه پاسخی بدهد؟').dispatchEvent(new w.Event('input',{bubbles:true}));
  releasePreview();
  await until(()=>!previewButton.disabled && output.textContent.includes('تغییر کرد'));
  previewText.value=''; previewText.dispatchEvent(new w.Event('input',{bubbles:true})); previewButton.click();
  assert.match(output.textContent,/پیام آزمایشی بنویس/);
  assert.equal(requests.filter(r=>r.url.endsWith('/preview')).length,4);
  field(existingApi,'کلید دسترسی').value='';
  const form=panel.querySelector('form'); button(panel,'ذخیره پاسخ‌ها').click();
  await until(()=>saved && field(panel,'پیام خوش‌آمدگویی').disabled===false && panel.textContent.includes('همهٔ پاسخ‌ها ذخیره شدند'));
  assert.equal(saved.rules.length,3);assert.equal(saved.base_version,2);
  assert.equal(saved.rules[2].source_rule_id,'api-old');assert.equal(saved.rules[2].api.credential,null);
  assert.equal(saved.rules[2].api.include_message,false);
  assert.equal(panel.querySelectorAll('.rule-card').length,3);
  const refreshed=panel.querySelectorAll('.rule-card')[2];
  assert.equal(field(refreshed,'کلید دسترسی').value,'');
  button(refreshed,'حذف پاسخ').click(); assert.equal(panel.querySelectorAll('.rule-card').length,2);
  button(panel,'بازگردانی').click(); assert.equal(panel.querySelectorAll('.rule-card').length,3);
  assert.equal(panel.querySelectorAll('.rule-card')[2],refreshed);
  assert.equal(field(refreshed,'کلید دسترسی').value,'');
  button(panel,'بستن تنظیمات').click();
  assert.equal(w.document.querySelector('.reply-editor'),panel);
  button(panel,'ادامهٔ ویرایش').click(); assert.equal(panel.querySelector('.discard-confirm').hidden,true);
  button(panel,'بستن تنظیمات').click();
  button(panel,'بستن بدون ذخیره').click();assert.equal(w.document.querySelector('.reply-editor'),null);
  assert.equal(button(w.document,'تنظیم پیام‌های ربات').disabled,false);
  assert.equal(requests.filter(r=>r.url.endsWith('/configs')).length,1);
  assert.equal(requests.filter(r=>r.url.includes('/publish?')).length,1);
  const botFetches=requests.filter(r=>r.url.endsWith('/bots')).length;
  w.document.dispatchEvent(new w.Event('visibilitychange'));
  await until(()=>requests.filter(r=>r.url.endsWith('/bots')).length===botFetches+1);
  dom.window.close();console.log('TelBot DOM editor behavior: PASS');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
