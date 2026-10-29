/* Save failure/readback behavior. Synthetic identity and application fetch only. */
const assert=require('node:assert/strict');
const fs=require('node:fs'), path=require('node:path');
const {JSDOM}=require('jsdom');
function button(root,text){const b=[...root.querySelectorAll('button')].find(n=>n.textContent===text);assert(b,text);return b;}
function field(root,text){const l=[...root.querySelectorAll('label')].find(n=>n.firstChild?.textContent===text);assert(l,text);return l.querySelector('input,textarea,select');}
async function until(fn){for(let i=0;i<150;i++){if(fn())return;await new Promise(setImmediate);}throw new Error('Save UI did not settle');}
async function scenario(mode){
  const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'web/index.html'),'utf8'),{runScripts:'outside-only',url:'https://telbot.invalid',pretendToBeVisual:true});
  const w=dom.window,requests=[];let committed=false;
  let original={published:{id:'old',version:4,greeting:'Hello',fallback_reply:'Fallback'},api_actions_ready:true,external_api_enabled:false,rules:[]};
  w.Telegram={WebApp:{initData:'synthetic-init',ready(){},expand(){}}};
  w.fetch=async(url,options={})=>{
    requests.push({url,options});let status=200,body;
    if(url.endsWith('/me/tenants'))body=[{id:'tenant',display_name:'Synthetic',role:'owner'}];
    else if(url.endsWith('/bots'))body=[{id:'bot',status:'active',credential_ready:true,is_managed:true}];
    else if(url.endsWith('/config')){
      if(committed && mode==='readback_error'){status=503;body={detail:'unavailable'};}
      else body=original;
    }else if(url.endsWith('/configs')){
      if(mode==='expired'){status=401;body={detail:'expired_auth_date'};}
      else body={id:'draft',version:5,state:'draft'};
    }else if(url.includes('/publish?')){
      if(mode==='conflict'){status=409;body={detail:'Published configuration changed; reload before publishing'};}
      else{committed=true;body={id:'draft',version:5,state:'published'};
        if(['empty','complete_extra'].includes(mode)) {
          const snapshot=JSON.parse(requests.find(r=>r.url.endsWith('/configs')).options.body);
          original={...original,published:{...body,greeting:snapshot.greeting,fallback_reply:snapshot.fallback_reply},rules:snapshot.rules.map((r,i)=>({...r,id:'saved-'+i}))};
        }
      }
    }else throw new Error('Unexpected request');
    return {ok:status<400,status,headers:{get:()=>null},json:async()=>JSON.parse(JSON.stringify(body))};
  };
  try {
    w.eval(fs.readFileSync(path.join(__dirname,'web/app.js'),'utf8'));
    await until(()=>w.document.querySelector('.bot-actions button'));
    button(w.document,'تنظیم پیام‌های ربات').click();
    await until(()=>{const p=w.document.querySelector('.reply-editor');return p&&!button(p,'ذخیره پاسخ‌ها').disabled;});
    const panel=w.document.querySelector('.reply-editor');
    assert.equal(panel.querySelectorAll('.rule-card').length,0,'Opening the editor must not add a reply');
    button(panel,'+ افزودن پاسخ').click();
    const card=panel.querySelector('.rule-card');field(card,'کاربر چه می‌نویسد؟').value='قیمت';
    field(card,'ربات چه پاسخی بدهد؟').value=mode==='invalid'?'':'Unsaved new answer';
    field(card,'کاربر چه می‌نویسد؟').dispatchEvent(new w.Event('input',{bubbles:true}));
    if(mode==='empty') {
      field(card,'کاربر چه می‌نویسد؟').value='  ';field(card,'ربات چه پاسخی بدهد؟').value='';
    }
    if(mode==='complete_extra')button(panel,'+ افزودن پاسخ').click();
    const countBeforeSave=panel.querySelectorAll('.rule-card').length;
    assert.equal(countBeforeSave,mode==='complete_extra'?2:1,'Typing never adds the next reply');
    const save=button(panel,'ذخیره پاسخ‌ها');save.click();
    const notice=panel.querySelector('.save-feedback');assert.equal(notice.hidden,false,'Feedback must be beside Save immediately');
    if(['empty','complete_extra'].includes(mode)) {
      await until(()=>notice.classList.contains('success'));
      const posted=JSON.parse(requests.find(r=>r.url.endsWith('/configs')).options.body);
      assert.equal(posted.rules.length,mode==='empty'?0:1,'Only completed optional replies are posted');
      assert.equal(panel.querySelectorAll('.rule-card').length,posted.rules.length);
      button(panel,'بستن تنظیمات').click();assert.equal(w.document.querySelector('.reply-editor'),null);
      return;
    }
    if(mode!=='invalid')save.click(); // repeat tap while busy
    await until(()=>notice.classList.contains('error'));
    assert.equal(field(card,'ربات چه پاسخی بدهد؟').value,mode==='invalid'?'':'Unsaved new answer');
    assert.equal(panel.querySelector('.rule-card'),card,'Failure must not rebuild/erase the typed form');
    assert.equal(notice.classList.contains('success'),false);
    assert.equal(save.disabled,false,'Save must react again rather than stay inert');
    if(mode==='expired')assert.match(notice.textContent,/نشست تلگرام/);
    if(mode==='invalid'){
      assert.equal(w.document.activeElement,field(card,'ربات چه پاسخی بدهد؟'));
      assert.equal(requests.filter(r=>r.options.method==='POST').length,0);
    }else{
      assert.equal(requests.filter(r=>r.url.endsWith('/configs')).length,1);
      assert.equal(requests.filter(r=>r.url.includes('/publish?')).length,mode==='expired'?0:1);
    }
    if(['readback_error','readback_mismatch'].includes(mode)){
      assert.match(notice.textContent,/تأیید نهایی/);
      const before=requests.length;save.click();assert.equal(requests.length,before,'Verification failure must not silently republish');
    }
  } finally {dom.window.close();}
}
(async()=>{for(const mode of ['empty','complete_extra','invalid','expired','conflict','readback_error','readback_mismatch'])await scenario(mode);console.log('TelBot save click/error/readback behavior: PASS');})().catch(error=>{console.error(error);process.exitCode=1;});
