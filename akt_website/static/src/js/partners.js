/* Client/partner logo rail. Approval filtering happens server-side. */
(() => {
 'use strict';
 document.querySelectorAll('[data-partner-slider]').forEach(section => { if(section.querySelector('.partner-rail').swiper) return;
  if (!window.Swiper) return; // Native horizontal scrolling is the no-JS/library fallback.
  const rail=section.querySelector('.partner-rail');
  const controls=section.querySelector('.partner-controls');
  const motion=section.querySelector('.partner-motion');
  const count=rail.querySelectorAll('.swiper-slide').length;
  const isTextRail=rail.classList.contains('why-rail')||rail.classList.contains('text-rail');
  const reduce=matchMedia('(prefers-reduced-motion: reduce)');
  const lowPower=navigator.connection?.saveData || (navigator.hardwareConcurrency && navigator.hardwareConcurrency<=2);
  let userPaused=reduce.matches||Boolean(lowPower),hovered=false,focused=false,dragging=false,inView=false,explicitResume=false;
  const continuous=!isTextRail&&count>=8;
  rail.classList.toggle('partner-continuous',continuous);
  const slider=new Swiper(rail,{
   slidesPerView:isTextRail?1.15:1.5,spaceBetween:16,speed:(reduce.matches||lowPower)?0:(continuous?9000:900),
   breakpoints:isTextRail?{390:{slidesPerView:1.2,spaceBetween:18},640:{slidesPerView:2.2,spaceBetween:20},900:{slidesPerView:3,spaceBetween:22},1200:{slidesPerView:4,spaceBetween:24}}:{390:{slidesPerView:1.7,spaceBetween:18},640:{slidesPerView:2.5,spaceBetween:20},900:{slidesPerView:3.5,spaceBetween:22},1200:{slidesPerView:4,spaceBetween:24}},
   loop:continuous,rewind:!continuous,watchOverflow:true,grabCursor:true,
   autoplay:false,
   navigation:{prevEl:section.querySelector('.partner-prev'),nextEl:section.querySelector('.partner-next')},
   keyboard:{enabled:true,onlyInViewport:true},
   a11y:{enabled:true,prevSlideMessage:document.documentElement.lang==='ar'?'الشعارات السابقة':'Previous logos',nextSlideMessage:document.documentElement.lang==='ar'?'الشعارات التالية':'Next logos'},
  });
  // Enable autoplay only after initialization so reduced-motion starts stationary.
  slider.params.autoplay={...slider.params.autoplay,enabled:true,delay:(reduce.matches||lowPower)?2800:(continuous?0:2800),disableOnInteraction:false,waitForTransition:true,stopOnLastSlide:false};
  function freeze(){
   slider.autoplay.stop();
   if(slider.animating){const x=slider.getTranslate();slider.setTransition(0);slider.setTranslate(x);slider.updateActiveIndex();slider.updateSlidesClasses();slider.animating=false;}
  }
  function sync(){
   const paused=userPaused||((hovered||focused)&&!explicitResume)||dragging||document.hidden||!inView||slider.isLocked;
   if(paused)freeze();else if(!slider.autoplay.running)slider.autoplay.start();
   motion.dataset.state=paused?'paused':'playing';
   motion.setAttribute('aria-label',paused?motion.dataset.play:motion.dataset.pause);
   section.dataset.motion=paused?'paused':'playing';
   rail.querySelector('.swiper-wrapper').setAttribute('aria-live',paused?'polite':'off');
   controls.hidden=slider.isLocked;
  }
  motion.addEventListener('click',()=>{if(section.dataset.motion==='paused'){userPaused=false;explicitResume=true}else{userPaused=true;explicitResume=false}sync()});
  section.addEventListener('pointerenter',e=>{if(e.pointerType!=='touch'){hovered=true;sync()}});
  section.addEventListener('pointerleave',()=>{hovered=false;explicitResume=false;if(focused&&!document.activeElement.matches(':focus-visible'))focused=false;sync()});
  section.addEventListener('focusin',()=>{focused=true;sync()});
  section.addEventListener('focusout',e=>{focused=section.contains(e.relatedTarget);explicitResume=false;sync()});
  slider.on('touchStart',()=>{dragging=true;sync()});
  slider.on('touchEnd',()=>{dragging=false;sync()});
  slider.on('resize',sync);slider.on('lock',sync);slider.on('unlock',sync);
  document.addEventListener('visibilitychange',sync);
  reduce.addEventListener('change',e=>{slider.params.speed=(e.matches||lowPower)?0:(continuous?9000:900);slider.params.autoplay.delay=(e.matches||lowPower)?2800:(continuous?0:2800);if(e.matches)userPaused=true;sync()});
  new IntersectionObserver(entries=>{inView=entries[0].isIntersecting;sync()},{threshold:.15}).observe(section);
  controls.hidden=false;sync();
 });
})();
