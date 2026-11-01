(()=>{
'use strict';
const $=id=>document.getElementById(id);let catalog=[],botUrl=null,active=null;
const norm=s=>s.normalize('NFKC').replace(/ي/g,'ی').replace(/ك/g,'ک').toLowerCase();
function safeBot(value){return typeof value==='string'&&/^https:\/\/t\.me\/[A-Za-z0-9_]{5,32}$/.test(value)?value:null;}
function linkFor(id){return botUrl+'?start=idea_'+id;}
function setupLinks(){
 document.querySelectorAll('.bot-link').forEach(a=>{a.hidden=!botUrl;if(botUrl)a.href=linkFor('other');});
 $('connection-status').hidden=!!botUrl;
 if(!botUrl)$('connection-status').textContent='لینک گفتگو هنوز آماده نیست. می‌توانی ایده‌ها و نمونه‌ها را ببینی؛ ثبت درخواست فعلاً در دسترس نیست.';
}
function render(){
 const query=norm($('search').value.trim());let count=0;
 document.querySelectorAll('.industry-card').forEach(card=>{const x=catalog.find(x=>x.id===card.dataset.id);const show=norm(x.title+' '+x.description+' '+x.features.join(' ')).includes(query);card.hidden=!show;if(show)count++;});
 $('catalog-status').textContent=count.toLocaleString('fa-IR')+' حوزه برای شروع';$('empty').hidden=count!==0;
}
function openPreview(x){
 active=x;$('preview-title').textContent=x.icon+' '+x.title;$('preview-description').textContent=x.description;$('preview-features').replaceChildren();
 x.features.forEach(f=>{const li=document.createElement('li');li.textContent=f;$('preview-features').append(li);});
 resetDemo();const request=$('request-category');request.hidden=!botUrl;if(botUrl)request.href=linkFor(x.id);
 $('preview').showModal();
}
function resetDemo(){
 $('demo-text').textContent='فرض کن مشتری این کسب‌وکار هستی. از کدام مسیر شروع می‌کنی؟';$('demo-options').replaceChildren();
 active.choices.forEach(choice=>{const b=document.createElement('button');b.type='button';b.textContent=choice;b.addEventListener('click',()=>{
 $('demo-text').textContent='انتخاب شما: '+choice+' — در نسخهٔ اختصاصی، این مرحله می‌تواند اطلاعات لازم را دریافت کند و به مسیر مربوط برود. این نمونه هیچ درخواست یا عملیات واقعی ثبت نمی‌کند.';
 const again=document.createElement('button');again.type='button';again.textContent='شروع دوبارهٔ نمونه';again.addEventListener('click',resetDemo);$('demo-options').replaceChildren(again);again.focus();});$('demo-options').append(b);});
}
$('search').addEventListener('input',render);$('close-preview').addEventListener('click',()=>$('preview').close());
$('show-other').addEventListener('click',()=>{const x=catalog.find(x=>x.id==='other');if(x)openPreview(x);});
async function load(){
 try{
  const r=await fetch('/api/v1/showcase/catalog',{credentials:'omit'});if(!r.ok)throw Error('catalog');const d=await r.json();
  if(!Array.isArray(d.industries)||!d.industries.length||d.examples_are_simulated!==true)throw Error('catalog');
  catalog=d.industries;botUrl=safeBot(d.bot_url);$('cards').replaceChildren();
  catalog.forEach(x=>{const card=document.createElement('article');card.className='industry-card';card.dataset.id=x.id;
   const icon=document.createElement('span');icon.className='card-icon';icon.setAttribute('aria-hidden','true');icon.textContent=x.icon;
   const h=document.createElement('h3');h.textContent=x.title;const p=document.createElement('p');p.textContent=x.description;
   const b=document.createElement('button');b.type='button';b.textContent='ایده‌ها و نمونهٔ تعاملی ↗';b.setAttribute('aria-label','دیدن نمونهٔ '+x.title);b.addEventListener('click',()=>openPreview(x));card.append(icon,h,p,b);$('cards').append(card);
  });render();setupLinks();
 }catch(e){$('catalog-status').textContent='دریافت فهرست انجام نشد. دوباره تلاش کن.';$('connection-status').textContent='ارتباط با سرویس برقرار نشد؛ هیچ درخواستی ارسال نشده است.';
  const retry=document.createElement('button');retry.type='button';retry.textContent='تلاش دوباره';retry.addEventListener('click',()=>{retry.remove();load();});$('catalog-status').append(retry);
 }
}
load();
})();
