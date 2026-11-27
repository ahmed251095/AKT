/* Shared behaviour for all design versions. No inline scripts (strict CSP). */
(()=>{'use strict';
const root=document.documentElement,reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
/* glass cards: soft light that follows the pointer */
document.querySelectorAll('.glass').forEach(el=>el.addEventListener('pointermove',e=>{const r=el.getBoundingClientRect();el.style.setProperty('--mx',(e.clientX-r.left)+'px');el.style.setProperty('--my',(e.clientY-r.top)+'px')},{passive:true}));
/* button shine on press */
document.addEventListener('click',e=>{const b=e.target.closest('.t-btn,.akt-btn');if(!b)return;b.classList.remove('go');void b.offsetWidth;b.classList.add('go')});
/* header state on scroll */
const header=document.querySelector('.site-header');
if(header){const on=()=>header.classList.toggle('scrolled',scrollY>24);on();addEventListener('scroll',on,{passive:true})}
/* mark the current section in the main menu */
const path=location.pathname;let best=null,len=0;
document.querySelectorAll('#primary-nav a[href]').forEach(a=>{const h=a.getAttribute('href');if(h&&h.length>4&&path.startsWith(h)&&h.length>len){best=a;len=h.length}});
if(best)best.setAttribute('aria-current','page');
/* reveal on scroll */
const items=document.querySelectorAll('.t-reveal');
if(reduced||!('IntersectionObserver' in window))items.forEach(el=>el.classList.add('in'));
else{const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}}),{threshold:.12,rootMargin:'0px 0px -6% 0px'});items.forEach((el,i)=>{el.style.setProperty('--i',i%4);io.observe(el)})}
/* count-up numbers */
const fmt=new Intl.NumberFormat(root.lang||'ar');
document.querySelectorAll('[data-t-count]').forEach(el=>{const end=Number(el.dataset.tCount);if(!Number.isFinite(end))return;el.textContent=fmt.format(end);if(reduced||!('IntersectionObserver' in window))return;el.textContent=fmt.format(0);const io=new IntersectionObserver(es=>{if(!es[0].isIntersecting)return;io.disconnect();const s=performance.now();(function f(n){const p=Math.min((n-s)/1500,1);el.textContent=fmt.format(Math.round(end*(1-Math.pow(1-p,3))));if(p<1)requestAnimationFrame(f)})(s)},{threshold:.6});io.observe(el)});
/* back-to-top button (original site behaviour, kept for every theme) */
const top=document.querySelector('.back-to-top');
if(top&&!top.dataset.bound){top.dataset.bound='1';const v=()=>top.classList.toggle('visible',scrollY>600);v();addEventListener('scroll',v,{passive:true});top.addEventListener('click',()=>scrollTo({top:0,behavior:reduced?'auto':'smooth'}))}
})();
