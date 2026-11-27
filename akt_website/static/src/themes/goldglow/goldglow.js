/* Version 5: gold glow. Ripple on press and the sectors slider. */
(()=>{'use strict';
const rm=matchMedia('(prefers-reduced-motion: reduce)').matches;
document.addEventListener('pointerdown',e=>{const t=e.target.closest('.akt-btn,.gg-chip');if(!t||rm)return;const r=t.getBoundingClientRect(),s=document.createElement('span');s.className='gg-rip';s.style.left=(e.clientX-r.left)+'px';s.style.top=(e.clientY-r.top)+'px';t.appendChild(s);setTimeout(()=>s.remove(),700)});
document.querySelectorAll('[data-gg-slider]').forEach(sl=>{
 const trk=sl.querySelector('.gg-trk'),dots=sl.querySelector('.gg-dots'),n=trk.children.length;if(!n)return;
 for(let i=0;i<n;i++)dots.appendChild(document.createElement('i'));
 const w=()=>trk.children[0].offsetWidth+16,rtl=getComputedStyle(trk).direction==='rtl'?-1:1;
 const step=d=>{const end=Math.abs(trk.scrollLeft)+trk.clientWidth>=trk.scrollWidth-6;if(d>0&&end)trk.scrollTo({left:0,behavior:rm?'auto':'smooth'});else trk.scrollBy({left:d*rtl*w(),behavior:rm?'auto':'smooth'})};
 sl.querySelectorAll('[data-dir]').forEach(b=>b.addEventListener('click',()=>step(b.dataset.dir==='next'?1:-1)));
 const upd=()=>{const i=Math.min(n-1,Math.round(Math.abs(trk.scrollLeft)/w()));[...dots.children].forEach((d,k)=>d.classList.toggle('on',k===i))};
 trk.addEventListener('scroll',upd,{passive:true});upd();
 let hold=false;['pointerenter','focusin'].forEach(ev=>sl.addEventListener(ev,()=>hold=true));['pointerleave','focusout'].forEach(ev=>sl.addEventListener(ev,()=>hold=false));
 if(!rm&&trk.scrollWidth>trk.clientWidth+10)setInterval(()=>{if(!hold&&!document.hidden)step(1)},4500);
});
})();
