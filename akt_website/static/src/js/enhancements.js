/* Progressive enhancements. Text lists and source images remain available. */
(() => {
  'use strict';
  const ar = document.documentElement.lang === 'ar';
  const say = (a, e) => ar ? a : e;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches || document.documentElement.classList.contains('low-motion');
  document.querySelectorAll('[data-project-map]').forEach(wrapper => {
    const button=wrapper.querySelector('[data-map-load]'), canvas=wrapper.querySelector('.map-canvas'), status=wrapper.querySelector('.map-status');
    button.addEventListener('click', () => {
      if (!window.L) {status.textContent=say('تعذر تحميل عارض الخريطة. قائمة المواقع متاحة أدناه.', 'Map viewer unavailable. Use the location list below.');return;}
      try {
        const points=JSON.parse(document.getElementById(wrapper.dataset.pointsId).textContent);
        canvas.hidden=false;
        const map=L.map(canvas,{scrollWheelZoom:false,zoomControl:false,zoomAnimation:!reduced,fadeAnimation:!reduced});
        L.control.zoom({position:ar?'topright':'topleft',zoomInTitle:say('تكبير','Zoom in'),zoomOutTitle:say('تصغير','Zoom out')}).addTo(map);
        const layer=L.tileLayer(wrapper.dataset.tileUrl,{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'});
        const ready=say('استخدم أزرار التكبير أو لوحة المفاتيح. الخريطة لا تستخدم موقع جهازك.', 'Use the zoom controls or keyboard. This map does not use your device location.');
        const failed=say('خلفية الخريطة غير متاحة حالياً. استخدم قائمة المواقع أو حاول لاحقاً.', 'Map background unavailable. Use the location list or try later.');
        let hadError=false;
        const timeout=setTimeout(()=>{status.textContent=failed;},15000);
        layer.on('tileerror',()=>{hadError=true;clearTimeout(timeout);status.textContent=failed;});
        layer.on('load',()=>{clearTimeout(timeout);status.textContent=hadError?failed:ready;});
        layer.addTo(map);
        const bounds=[];
        points.forEach(point=>{
          const lat=Number(point.lat),lng=Number(point.lng),target=new URL(point.url,location.origin);
          if(!Number.isFinite(lat)||!Number.isFinite(lng)||Math.abs(lat)>90||Math.abs(lng)>180||target.origin!==location.origin)return;
          const anchor=document.createElement('a');anchor.href=target.href;anchor.textContent=point.title;
          L.marker([lat,lng],{title:point.title,alt:point.title}).addTo(map).bindPopup(anchor);bounds.push([lat,lng]);
        });
        map.on('popupopen',()=>{const close=canvas.querySelector('.leaflet-popup-close-button');if(close)close.setAttribute('aria-label',say('إغلاق النافذة','Close popup'));});
        if(bounds.length===1)map.setView(bounds[0],12);else if(bounds.length)map.fitBounds(bounds,{padding:[25,25],maxZoom:12});
        button.hidden=true;status.textContent=ready;canvas.setAttribute('role','region');canvas.focus({preventScroll:true});
      } catch (_) {status.textContent=say('تعذر فتح الخريطة. قائمة المواقع متاحة أدناه.', 'Could not open the map. Use the location list below.');}
    },{once:true});
  });
  document.querySelectorAll('[data-panorama]').forEach(wrapper=>{
    const button=wrapper.querySelector('[data-panorama-load]'),close=wrapper.querySelector('[data-panorama-close]'),canvas=wrapper.querySelector('.panorama-canvas'),poster=wrapper.querySelector('.panorama-poster'),status=wrapper.querySelector('.panorama-status');
    let viewer=null,timer=null;
    const stop=()=>{clearTimeout(timer);if(viewer){viewer.off();viewer.destroy();viewer=null;}canvas.hidden=true;poster.hidden=false;button.disabled=false;button.textContent=say('فتح الجولة ↗','Open tour ↗');if(close)close.hidden=true;};
    const fail=()=>{stop();status.textContent=say('تعذر عرض البانوراما على هذا الجهاز أو الاتصال. افتح الصورة الأصلية أو حاول مرة أخرى.', 'Panorama unavailable on this device or connection. Open the original image or retry.');};
    if(close)close.addEventListener('click',()=>{stop();status.textContent=say('أُغلقت الجولة.','Tour closed.');button.focus({preventScroll:true});});
    button.addEventListener('click',()=>{
      if(!window.pannellum){status.textContent=say('العارض غير متاح. افتح الصورة الأصلية.', 'Viewer unavailable. Open the original image.');return;}
      button.disabled=true;canvas.hidden=false;status.textContent=say('جارٍ فتح الجولة…','Opening the tour…');
      try {
        const strings=ar?{loadButtonLabel:'فتح الجولة',loadingLabel:'جارٍ التحميل…',bylineLabel:'بواسطة %s',noPanoramaError:'لم تُحدد صورة بانورامية.',fileAccessError:'تعذر تحميل الصورة %s.',malformedURLError:'رابط الصورة غير صالح.',iOS8WebGLError:'هذا الجهاز لا يدعم الصورة الحالية.',genericWebGLError:'المتصفح لا يدعم العرض التفاعلي. افتح الصورة الأصلية.',textureSizeError:'الصورة أكبر مما يدعمه هذا الجهاز. افتح الصورة الأصلية.',unknownError:'تعذر بدء العرض. افتح الصورة الأصلية.'}:undefined;
        viewer=pannellum.viewer(canvas,{type:'equirectangular',panorama:wrapper.dataset.url,yaw:Number(wrapper.dataset.yaw)||0,autoLoad:true,autoRotate:0,mouseZoom:false,hotSpotDebug:false,escapeHTML:true,strings});
        timer=setTimeout(fail,15000);
        viewer.on('load',()=>{
          clearTimeout(timer);poster.hidden=true;if(close)close.hidden=false;
          status.textContent=say('اسحب للاستكشاف أو استخدم الأسهم بعد تحديد العارض. أزرار التكبير داخل العرض.', 'Drag to explore, or focus the viewer and use arrow keys. Zoom controls are inside the view.');
          canvas.focus({preventScroll:true});
        });
        viewer.on('error',fail);
        const controls=[['.pnlm-zoom-in',say('تكبير','Zoom in')],['.pnlm-zoom-out',say('تصغير','Zoom out')],['.pnlm-fullscreen-toggle-button',say('تبديل ملء الشاشة','Toggle fullscreen')]];
        controls.forEach(([selector,label])=>{
          const control=canvas.querySelector(selector);if(!control)return;
          control.textContent=selector.includes('zoom-in')?'+':selector.includes('zoom-out')?'−':'⛶';control.setAttribute('role','button');control.setAttribute('aria-label',label);control.setAttribute('title',label);control.tabIndex=0;
          control.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();control.click();}});
        });
        const orientation=canvas.querySelector('.pnlm-orientation-button');if(orientation)orientation.hidden=true;
      } catch (_) {fail();}
    });
  });
})();
