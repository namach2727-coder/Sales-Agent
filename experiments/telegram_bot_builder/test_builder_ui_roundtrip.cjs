/* Real HTTP/DB roundtrip, launched only by the disposable PostgreSQL test. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {JSDOM}=require('jsdom');
const origin=new URL(process.env.TELBOT_UI_TEST_ORIGIN || 'http://invalid');
if(origin.protocol!=='http:' || origin.hostname!=='127.0.0.1' || !origin.port || origin.username || origin.password) throw new Error('Loopback test server required');
function button(scope,text){const node=[...scope.querySelectorAll('button')].find(n=>n.textContent===text);assert(node,text);return node;}
function field(scope,text){const label=[...scope.querySelectorAll('label')].find(n=>n.firstChild?.textContent===text);assert(label,text);return label.querySelector('input,textarea,select');}
async function until(check){const end=Date.now()+10000;while(Date.now()<end){if(check())return;await new Promise(resolve=>setTimeout(resolve,10));}throw new Error('UI roundtrip timed out');}
async function main(){
  const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'web/index.html'),'utf8'),{runScripts:'outside-only',url:origin.href,pretendToBeVisual:true});
  const w=dom.window,requests=[];
  w.Telegram={WebApp:{initData:process.env.TELBOT_UI_TEST_INIT_DATA,ready(){},expand(){}}};
  w.fetch=(url,options={})=>{
    assert.equal(typeof url,'string');assert(url.startsWith('/api/'),'Only local application routes are allowed');
    requests.push({url,method:options.method||'GET'});
    return fetch(new URL(url,origin),options);
  };
  try {
    w.eval(fs.readFileSync(path.join(__dirname,'web/app.js'),'utf8'));
    await until(()=>w.document.querySelector('.bot-actions button'));
    async function open(){
      button(w.document,'تنظیم پیام‌های ربات').click();
      await until(()=>{const p=w.document.querySelector('.reply-editor');return p&&!button(p,'ذخیره پاسخ‌ها').disabled;});
      return w.document.querySelector('.reply-editor');
    }
    async function addAndSave(panel,keyword,response){
      button(panel,'پاسخ‌ها').click();button(panel,'+ افزودن پاسخ').click();
      const card=[...panel.querySelectorAll('.rule-card')].at(-1);
      field(card,'کاربر چه می‌نویسد؟').value=keyword;
      field(card,'ربات چه پاسخی بدهد؟').value=response;
      field(card,'کاربر چه می‌نویسد؟').dispatchEvent(new w.Event('input',{bubbles:true}));
      assert.equal(panel.querySelectorAll('.rule-card').length,keyword==='جدید اول'?1:2,'Typing does not create the next card');
      const toggle=field(card,'نمایش این عبارت به‌صورت دکمه در ربات');toggle.checked=true;toggle.dispatchEvent(new w.Event('change',{bubbles:true}));
      // An optional untouched next row must not prevent saving completed answers.
      button(panel,'+ افزودن پاسخ').click();
      button(panel,'+ افزودن پاسخ').click();
      assert.equal(panel.querySelectorAll('.rule-card').length,keyword==='جدید اول'?2:3,'Do not stack blank rows');
      const save=button(panel,'ذخیره پاسخ‌ها');assert.equal(save.type,'button');save.click();
      assert.match(panel.querySelector('.save-feedback').textContent,/در حال ذخیره/);
      // A second submit while the first request is pending must not duplicate versions.
      panel.querySelector('form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
      await until(()=>{const s=panel.querySelector('.save-feedback');return s.classList.contains('success')||s.classList.contains('error');});
      assert.equal(panel.querySelector('.save-feedback').classList.contains('success'),true,panel.querySelector('.save-feedback').textContent);
      button(panel,'بستن تنظیمات').click();assert.equal(w.document.querySelector('.reply-editor'),null);
    }
    let panel=await open();await addAndSave(panel,'جدید اول','پاسخ اول');
    panel=await open();assert.equal(panel.querySelectorAll('.rule-card').length,1);
    assert.equal(field(panel.querySelector('.rule-card'),'کاربر چه می‌نویسد؟').value,'جدید اول');
    await addAndSave(panel,'جدید دوم','پاسخ دوم');
    panel=await open();
    assert.deepEqual([...panel.querySelectorAll('.rule-card')].map(n=>field(n,'کاربر چه می‌نویسد؟').value),['جدید اول','جدید دوم']);
    assert.deepEqual([...panel.querySelectorAll('.rule-card')].map(n=>field(n,'ربات چه پاسخی بدهد؟').value),['پاسخ اول','پاسخ دوم']);
    assert([...panel.querySelectorAll('.rule-card')].every(card=>field(card,'نمایش این عبارت به‌صورت دکمه در ربات').checked),'Button choices survive real persistence');
    assert.equal(panel.querySelectorAll('.menu-preview-grid span').length,2);
    assert.equal(field(panel,'پیام خوش‌آمدگویی').value,'Hello');
    assert.equal(field(panel,'پاسخ به پیام‌های دیگر').value,'Fallback');
    assert.equal(requests.filter(n=>n.method==='POST').length,4);
    console.log('TelBot real UI -> FastAPI -> PostgreSQL save/reopen: PASS');
  } finally {dom.window.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
