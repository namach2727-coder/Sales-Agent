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
  const w=dom.window; const requests=[]; let releasePreview, releaseActivity, activityMode="success", replyStateMode="success", releaseReplyState, releaseServiceDemo;
  let saved, config={published:{id:'published-two',version:2,greeting:'Hello',fallback_reply:'Fallback'},api_actions_ready:true,external_api_enabled:false,rules:[
    {id:'text-old',keyword:'قیمت',response_text:'Price',match_mode:'exact',action_type:'text',enabled:true},
    {id:'api-old',keyword:'موجودی',response_text:'Unavailable',match_mode:'contains',action_type:'api',enabled:true,
      api:{url:'https://api.example.com/stock',method:'GET',params:{},json_body:{},response_path:'data.text',auth_mode:'bearer',auth_header:'X-API-Key',credential_present:true}},
  ]};
  w.Telegram={WebApp:{initData:'synthetic-init',ready(){},expand(){}}};
  w.fetch=async (url,options={}) => {
    requests.push({url,options}); let body;
    if (url.endsWith('/me/tenants')) body=[{id:'tenant',display_name:'Synthetic workspace',role:'owner'}];
    else if (url.endsWith('/bots')) body=[{id:'bot',username:'ExampleBot',status:'active',is_managed:true,credential_ready:true}];
    else if (url.endsWith('/service-flow-preview')) {
      const input=JSON.parse(options.body);
      if(input.scenario==='timeout')await new Promise(resolve=>{releaseServiceDemo=resolve;});
      body={simulation:true,live_actions:false,phase:input.scenario==='paid'?'delivered':input.scenario==='pending'?'awaiting_payment':'review_required',
        checkout_url:'https://checkout.example.com/demo-only',steps:['سفارش نمونه','بررسی پرداخت نمونه'],
        demo_delivery:input.scenario==='paid'?{username:'<b>DEMO</b>',password:'DEMO-NOT-VALID',config_text:'DEMO-CONFIG'}:null};
    }
    else if (url.endsWith('/reply-state')) {
      if(replyStateMode==='delayed')await new Promise(resolve=>{releaseReplyState=resolve;});
      if(replyStateMode==='error')throw new Error('synthetic-state-failure');
      const input=JSON.parse(options.body);body={status:input.paused?'paused':'active',runtime_enabled:true};
    }
    else if (url.endsWith('/activity')) {
      if(activityMode==='error')throw new Error('synthetic-unavailable');
      if(activityMode==='delayed')await new Promise(resolve=>{releaseActivity=resolve;});
      body={window_hours:24,summary:{received:4,sent:1,failed:1,pending:1,checked_at:'2026-10-29T16:00:00Z'},events:[
        {received_at:'2026-10-29T16:00:00Z',delivery_status:'sent',telegram_acknowledged:true},
        {received_at:'2026-10-29T16:00:00Z',delivery_status:'failed',telegram_acknowledged:false},
        {received_at:'2026-10-29T16:00:00Z',delivery_status:'queued',telegram_acknowledged:false},
        {received_at:'2026-10-29T16:00:00Z',delivery_status:null,telegram_acknowledged:false}]};
    }
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
      config={...config,published:{id:'draft',version:3,greeting:saved.greeting,fallback_reply:saved.fallback_reply},rules:saved.rules.map((r,i)=>{
        const result={...r,id:'new-'+i}; if(result.api){result.api={...result.api,credential_present:true};delete result.api.credential;} return result;
      })};body={id:'draft',version:3,state:'published'};
    } else throw new Error('Unexpected fetch '+url);
    return {ok:true,status:200,headers:{get:()=>null},json:async()=>JSON.parse(JSON.stringify(body))};
  };
  w.eval(script);
  await until(()=>w.document.querySelector('.bot-actions button'));
  button(w.document,'تنظیم پیام‌های ربات').click();
  await until(()=>w.document.querySelectorAll('.rule-card').length===2);
  const firstPanel=w.document.querySelector('.reply-editor'), filter=field(firstPanel,'جست‌وجو در پاسخ‌ها');
  const beforeFilter=requests.length;filter.focus();
  for(const query of ['P','PR','PRICE','موجودي','not-found']) {
    filter.value=query;filter.dispatchEvent(new w.Event('input',{bubbles:true}));
    assert.equal(w.document.activeElement,filter,'Filtering preserves search focus');
    assert.equal(firstPanel.querySelectorAll('.rule-card:not([hidden])').length,query==='not-found'?0:1);
  }
  assert.match(firstPanel.querySelector('.search-result').textContent,/پیدا نشد/);
  const enter=new w.KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true});filter.dispatchEvent(enter);assert.equal(enter.defaultPrevented,true);
  assert.equal(requests.length,beforeFilter,'Search is local and never sends the query');
  button(firstPanel,'بستن تنظیمات').click();assert.equal(w.document.querySelector('.reply-editor'),null,'Search alone must not dirty the form');
  button(w.document,'تنظیم پیام‌های ربات').click();await until(()=>w.document.querySelectorAll('.rule-card').length===2);
  const panel=w.document.querySelector('.reply-editor');
  assert.equal(button(panel,'ذخیره پاسخ‌ها').type,'button','Save must use its direct click handler');
  assert.equal(button(panel,'ذخیره پاسخ‌ها').hasAttribute('form'),false);
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
  const toggle=button(w.document,'توقف پاسخ خودکار');replyStateMode='delayed';
  const row=toggle.closest('.bot-row');
  toggle.click();toggle.click();
  assert.match(row.querySelector('.reply-state-status').textContent,/در حال توقف/);
  await until(()=>releaseReplyState);releaseReplyState();
  await until(()=>toggle.textContent==='ادامهٔ پاسخ خودکار');
  assert.match(row.querySelector('.bot-card-header').textContent,/پاسخ‌گویی متوقف/);
  assert.equal(w.document.querySelector('.reply-editor'),panel,'Pause must retain the existing editor');
  assert.equal(w.document.activeElement,typing,'Pause must not rebuild/blur the editor');
  assert.equal(requests.filter(r=>r.url.endsWith('/reply-state')).length,1,'Duplicate taps while busy do not toggle twice');
  replyStateMode='error';toggle.click();
  await until(()=>row.querySelector('.reply-state-status').textContent.includes('تأیید نشد'));
  assert.equal(toggle.textContent,'ادامهٔ پاسخ خودکار','Failure must retain the known state');
  assert.equal(toggle.disabled,false);
  replyStateMode='success';toggle.click();await until(()=>toggle.textContent==='توقف پاسخ خودکار');
  const toggles=requests.filter(r=>r.url.endsWith('/reply-state')).map(r=>JSON.parse(r.options.body));
  assert.deepEqual(toggles,[{paused:true,expected_status:'active'},{paused:false,expected_status:'paused'},{paused:false,expected_status:'paused'}]);
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
  const menuToggle=field(newCard,'نمایش این عبارت به‌صورت دکمه در ربات');
  menuToggle.checked=true;menuToggle.dispatchEvent(new w.Event('change',{bubbles:true}));
  assert.equal(panel.querySelector('.menu-preview').hidden,false);
  assert.equal(panel.querySelector('.menu-preview-grid span').textContent,'آدرس');
  typing.focus();typing.dispatchEvent(new w.Event('input',{bubbles:true}));
  assert.equal(w.document.activeElement,typing,'Menu preview must not disturb typing');
  const search=field(panel,'جست‌وجو در پاسخ‌ها');
  search.value='آدرس';search.dispatchEvent(new w.Event('input',{bubbles:true}));typing.focus();
  typing.value='نام تازه';typing.dispatchEvent(new w.Event('input',{bubbles:true}));
  assert.equal(newCard.hidden,false,'Editing a matched card must not hide its own ancestor');assert.equal(w.document.activeElement,typing);
  typing.value='آدرس';typing.dispatchEvent(new w.Event('input',{bubbles:true}));
  button(panel,'نمایش همه').click();
  button(newCard,'کپی پاسخ').click();
  let copied=[...panel.querySelectorAll('.rule-card')].at(-1);
  assert.equal(field(copied,'کاربر چه می‌نویسد؟').value,'');assert.equal(field(copied,'ربات چه پاسخی بدهد؟').value,'Address');
  assert.equal(field(copied,'نمایش این عبارت به‌صورت دکمه در ربات').checked,false);
  search.value='قیمت';search.dispatchEvent(new w.Event('input',{bubbles:true}));assert.equal(copied.hidden,true);
  button(panel,'ذخیره پاسخ‌ها').click();
  assert.equal(copied.hidden,false);assert.equal(search.value,'');assert.equal(w.document.activeElement,field(copied,'کاربر چه می‌نویسد؟'));
  assert.equal(saved,undefined,'A copy needs a new trigger before Save');
  button(copied,'حذف پاسخ').click();
  field(existingApi,'کلید دسترسی').value='synthetic-copy-key';
  button(existingApi,'کپی پاسخ').click();copied=[...panel.querySelectorAll('.rule-card')].at(-1);
  assert.equal(field(copied,'نشانی سرویس (HTTPS)').value,field(existingApi,'نشانی سرویس (HTTPS)').value);
  assert.equal(field(copied,'کلید دسترسی').value,'synthetic-copy-key');
  search.value='synthetic-copy-key';search.dispatchEvent(new w.Event('input',{bubbles:true}));
  assert.equal(panel.querySelectorAll('.rule-card:not([hidden])').length,0,'Secrets never enter the search index');
  button(panel,'نمایش همه').click();button(copied,'حذف پاسخ').click();field(existingApi,'کلید دسترسی').value='';
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
  const cardsBeforeInvalidCopy=panel.querySelectorAll('.rule-card').length;button(existingApi,'کپی پاسخ').click();
  assert.equal(panel.querySelectorAll('.rule-card').length,cardsBeforeInvalidCopy,'Invalid API JSON must not create a copy');
  assert.equal(w.document.activeElement,params);
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
  const persistedText=panel.querySelector('.rule-card');
  const originalKeyword=field(persistedText,'کاربر چه می‌نویسد؟').value, originalAnswer=field(persistedText,'ربات چه پاسخی بدهد؟').value;
  field(persistedText,'کاربر چه می‌نویسد؟').value='';field(persistedText,'ربات چه پاسخی بدهد؟').value='';
  button(panel,'ذخیره پاسخ‌ها').click();
  assert.equal(saved,undefined,'Clearing a persisted reply must not silently omit/delete it');
  assert.equal(w.document.activeElement,field(persistedText,'کاربر چه می‌نویسد؟'));
  field(persistedText,'کاربر چه می‌نویسد؟').value=originalKeyword;field(persistedText,'ربات چه پاسخی بدهد؟').value=originalAnswer;
  const converted=field(persistedText,'نوع پاسخ');converted.value='api';converted.dispatchEvent(new w.Event('change',{bubbles:true}));
  field(persistedText,'نشانی سرویس (HTTPS)').value='https://api.example.com/new';
  previewText.value='/start';previewText.dispatchEvent(new w.Event('input',{bubbles:true}));previewButton.click();
  await until(()=>!previewButton.disabled && output.textContent.includes('پیام شروع'));
  const convertedBody=JSON.parse(requests.filter(r=>r.url.endsWith('/preview')).at(-1).options.body);
  assert.equal(convertedBody.rules[0].source_rule_id,null,'Text-to-API must not reference a text row as a saved API credential');
  assert.equal(convertedBody.rules[2].source_rule_id,'api-old','Existing API reuse remains scoped to its source');
  converted.value='text';converted.dispatchEvent(new w.Event('change',{bubbles:true}));
  const beforeBlank=panel.querySelectorAll('.rule-card').length;
  button(panel,'+ افزودن پاسخ').click();
  assert.equal(panel.querySelectorAll('.rule-card').length,beforeBlank+1);
  const blank=panel.querySelectorAll('.rule-card')[beforeBlank];
  button(panel,'+ افزودن پاسخ').click();
  assert.equal(panel.querySelectorAll('.rule-card').length,beforeBlank+1,'Repeated Add reuses the empty placeholder');
  assert.equal(w.document.activeElement,field(blank,'کاربر چه می‌نویسد؟'));
  assert.equal(button(panel,'+ افزودن پاسخ').parentElement,button(panel,'ذخیره پاسخ‌ها').parentElement);
  field(blank,'کاربر چه می‌نویسد؟').value='  ';
  field(blank,'ربات چه پاسخی بدهد؟').value='  ';
  search.value='آدرس';search.dispatchEvent(new w.Event('input',{bubbles:true}));
  const form=panel.querySelector('form'); button(panel,'ذخیره پاسخ‌ها').click();
  assert.match(panel.querySelector('.save-feedback').textContent,/در حال ذخیره/);
  await until(()=>saved && field(panel,'پیام خوش‌آمدگویی').disabled===false && panel.textContent.includes('همهٔ پاسخ‌ها ذخیره شدند'));
  assert.equal(saved.rules.length,3);assert.equal(saved.base_version,2);
  assert.equal(saved.rules[1].show_button,true);
  assert.equal(panel.querySelector('.save-feedback').classList.contains('success'),true);
  assert.equal(saved.rules[2].source_rule_id,'api-old');assert.equal(saved.rules[2].api.credential,null);
  assert.equal(saved.rules[2].api.include_message,false);
  assert.equal(panel.querySelectorAll('.rule-card').length,3);
  assert.equal(panel.querySelectorAll('.rule-card:not([hidden])').length,1,'Filtered Save still persists all completed replies');
  button(panel,'نمایش همه').click();
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
  const postsBeforeReport=requests.filter(r=>r.options.method==='POST').length;
  button(w.document,'گزارش عملکرد').click();
  assert.match(w.document.querySelector('.activity-status').textContent,/در حال دریافت/);
  await until(()=>w.document.querySelectorAll('.activity-events li').length===4);
  const report=w.document.querySelector('.activity-panel');
  assert.equal(report.querySelectorAll('.activity-stats > div').length,4);
  assert.match(report.textContent,/پاسخ ارسال شد/);assert.match(report.textContent,/ارسال پاسخ ناموفق/);
  assert.match(report.textContent,/نتیجهٔ ارسال هنوز مشخص نیست/);assert.match(report.textContent,/پاسخی ثبت نشده/);
  const priorResult=report.querySelector('.activity-result').innerHTML;
  activityMode='error';button(report,'به‌روزرسانی گزارش').click();
  await until(()=>report.querySelector('.activity-status').textContent.includes('انجام نشد'));
  assert.equal(report.querySelector('.activity-result').innerHTML,priorResult,'Failed refresh retains previous timestamped result');
  activityMode='delayed';button(report,'به‌روزرسانی گزارش').click();button(report,'به‌روزرسانی گزارش').click();
  await until(()=>releaseActivity);
  button(report,'بستن گزارش').click();releaseActivity();await new Promise(setImmediate);
  assert.equal(w.document.querySelector('.activity-panel'),null,'Closing before response must not recreate the panel');
  assert.equal(button(w.document,'گزارش عملکرد').disabled,false);
  assert.equal(requests.filter(r=>r.url.endsWith('/activity')).length,3);
  assert.equal(requests.filter(r=>r.options.method==='POST').length,postsBeforeReport,'Report never writes or sends');
  const demoBefore=requests.length;
  button(w.document,'نمونهٔ فروش و تحویل سرویس').click();
  const demo=w.document.querySelector('.service-preview');assert(demo);
  assert.match(demo.textContent,/حساب یا کانفیگ قابل استفاده ساخته نمی‌شود/);
  assert.equal(requests.length,demoBefore,'Opening the sample never executes actions');
  const run=button(demo,'اجرای سناریوی نمونه');run.click();run.click();
  assert.match(demo.querySelector('[role="status"]').textContent,/در حال اجرای/);
  await until(()=>demo.querySelector('.demo-account'));
  assert.match(demo.querySelector('.demo-account').textContent,/<b>DEMO<\/b>/);
  assert.equal(demo.querySelector('b'),null);assert.equal(demo.querySelector('a'),null,'Sample checkout URL is inert');
  const scenario=field(demo,'چه وضعیتی را آزمایش کنیم؟');scenario.value='pending';scenario.dispatchEvent(new w.Event('change',{bubbles:true}));
  assert.equal(demo.querySelector('.demo-account'),null,'Changing scenario clears stale delivery');
  run.click();await until(()=>!run.disabled && demo.querySelector('[role="status"]').textContent.includes('انتظار تأیید'));
  assert.equal(demo.querySelector('.demo-account'),null);
  scenario.value='mismatch';scenario.dispatchEvent(new w.Event('change',{bubbles:true}));run.click();
  await until(()=>!run.disabled && demo.querySelector('[role="status"]').textContent.includes('برای بررسی'));
  scenario.value='timeout';scenario.dispatchEvent(new w.Event('change',{bubbles:true}));run.click();await until(()=>releaseServiceDemo);
  button(demo,'بستن نمونه').click();releaseServiceDemo();await new Promise(setImmediate);
  assert.equal(w.document.querySelector('.service-preview'),null,'A late sample result must not reopen the panel');
  assert.equal(button(w.document,'نمونهٔ فروش و تحویل سرویس').disabled,false);
  assert.equal(requests.filter(r=>r.url.endsWith('/service-flow-preview')).length,4,'No duplicate run while busy');
  const botFetches=requests.filter(r=>r.url.endsWith('/bots')).length;
  w.document.dispatchEvent(new w.Event('visibilitychange'));
  await until(()=>requests.filter(r=>r.url.endsWith('/bots')).length===botFetches+1);
  dom.window.close();console.log('TelBot DOM editor behavior: PASS');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
