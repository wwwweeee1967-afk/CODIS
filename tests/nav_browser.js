/* CODIS-V5 navigation test — evaluate in the page (http, fresh origin, continue as guest first). Mutates local test data only.
   Real history.back() is used for native-back cases; synthetic TouchEvents for the swipe (simulated, not a real finger). */
(async function(){
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const gateOpen = ()=>{ const g = document.getElementById('codis-gate'); return !!g && g.classList.contains('is-open'); };
  const settingsSec = ()=>[...document.querySelectorAll('#page-settings .settings-page-section')].find(c=>getComputedStyle(c).display !== 'none');
  const inSub = ()=>{ const s = settingsSec(); return !!s && s.id !== 'settings-home' && !!s.querySelector('.settings-back-btn'); };
  const room = ()=>{ const a = document.querySelector('.navbtn.active'); return a && a.dataset.page; };
  const nav = p=>{ document.querySelector('.navbtn[data-page="' + p + '"]').click(); return sleep(700); };

  T('history guard installed (state=top)', history.state && history.state.codis === 'top');
  const len0 = history.length;
  for(const p of ['tasks', 'habits', 'learn', 'planning', 'settings', 'tasks']) await nav(p);
  T('room switching adds no history entries', history.length === len0, len0 + ' → ' + history.length);

  /* native back at a root room: stays, no gate, no change */
  await nav('tasks'); const before = room();
  history.back(); await sleep(500);
  T('native back at a root room: stays in app, same room', room() === before && !gateOpen() && location.pathname.length > 0);
  T('guard re-armed after back', history.state && history.state.codis === 'top');
  T('no gate after back', !gateOpen());

  /* nested settings page: exactly one level per back */
  await nav('settings'); openSettingsCategory('sound'); await sleep(700);
  T('nested page open', inSub());
  history.back(); await sleep(700);
  T('back from nested page returns to settings home (one level)', !inSub() && room() === 'settings');
  history.back(); await sleep(600);
  T('second back at settings home does nothing (no skip, no gate)', room() === 'settings' && !gateOpen());

  /* two quick backs while 2 levels deep: only one level closes */
  openSettingsCategory('rp'); await sleep(600); rpOpenHub('reward'); await sleep(700);
  const deep = settingsSec().id;
  history.back(); history.back(); await sleep(900);
  T('two rapid backs = one operation (lock)', settingsSec().id !== deep && inSub(), deep + ' → ' + settingsSec().id);
  history.back(); await sleep(700);
  T('next back closes the next level only', !inSub());

  /* store layer + modal */
  document.getElementById('coin-chip') && document.getElementById('coin-chip').click(); await sleep(700);
  const layer = codisBackLayer();
  T('coin log/store layer is a back target', !!layer);
  history.back(); await sleep(700);
  T('back closes the store layer', !codisBackLayer() && !gateOpen());

  /* topmost-layer-only: confirm over a page */
  openSettingsCategory('sound'); await sleep(600);
  const pr = codisConfirm({ title:'t', message:'m' }); await sleep(300);
  history.back(); await sleep(500);
  const r = await Promise.race([pr, sleep(200).then(()=>'pending')]);
  T('back with a confirm open closes only the confirm', r === false && inSub(), String(r));
  history.back(); await sleep(600); T('then the page', !inSub());

  /* swipe gesture (synthetic) */
  const mk = (type, x, y, id = 1)=>{ const t = new Touch({ identifier:id, target:document.body, clientX:x, clientY:y }); return new TouchEvent(type, { touches:type === 'touchend' ? [] : [t], changedTouches:[t], bubbles:true, cancelable:true }); };
  const bodyR = document.body.getBoundingClientRect(), L = bodyR.left + 6;
  await nav('settings'); openSettingsCategory('sound'); await sleep(700); const sec = settingsSec();
  document.dispatchEvent(mk('touchstart', L, 300)); document.dispatchEvent(mk('touchmove', L + 30, 302)); document.dispatchEvent(mk('touchmove', L + 90, 304)); await sleep(30);
  T('swipe: page follows the finger', /translate3d\(9\d|translate3d\(8\d|translate3d\(\d+px/.test(sec.style.transform) && !/translate3d\(0px/.test(sec.style.transform), sec.style.transform);
  document.dispatchEvent(mk('touchmove', L + 20, 304)); document.dispatchEvent(mk('touchend', L + 20, 304)); await sleep(500);
  T('swipe below threshold: springs back, page stays', inSub() && sec.style.transform === '', sec.style.transform);
  document.dispatchEvent(mk('touchstart', L, 300)); document.dispatchEvent(mk('touchmove', L + 40, 360)); document.dispatchEvent(mk('touchmove', L + 60, 520)); document.dispatchEvent(mk('touchend', L + 60, 520)); await sleep(400);
  T('vertical drag from the edge is not a back', inSub());
  document.dispatchEvent(mk('touchstart', L, 300)); document.dispatchEvent(mk('touchmove', L + 60, 302)); document.dispatchEvent(mk('touchmove', L + 200, 304)); document.dispatchEvent(mk('touchend', L + 200, 304)); await sleep(700);
  T('completed swipe goes back exactly one level', !inSub() && room() === 'settings' && !gateOpen());
  T('transform cleaned after swipe', sec.style.transform === '' && sec.style.transition === '');
  document.dispatchEvent(mk('touchstart', L, 300)); document.dispatchEvent(mk('touchmove', L + 90, 302)); document.dispatchEvent(mk('touchmove', L + 200, 304)); document.dispatchEvent(mk('touchend', L + 200, 304)); await sleep(600);
  T('swipe at settings home (root) does nothing', room() === 'settings' && !gateOpen());
  /* second finger cancels */
  openSettingsCategory('sound'); await sleep(600);
  document.dispatchEvent(mk('touchstart', L, 300)); document.dispatchEvent(mk('touchmove', L + 80, 302));
  const t2 = [new Touch({ identifier:1, target:document.body, clientX:L + 80, clientY:302 }), new Touch({ identifier:2, target:document.body, clientX:200, clientY:400 })];
  document.dispatchEvent(new TouchEvent('touchmove', { touches:t2, changedTouches:t2, bubbles:true, cancelable:true })); await sleep(500);
  T('second finger cancels the gesture and restores', inSub() && settingsSec().style.transform === '');
  history.back(); await sleep(600);

  /* session / gate: a stale gate restored from cache must be hidden when a guest/session exists */
  localStorage.setItem('codis_guest_mode', '1');
  const g0 = document.getElementById('codis-gate'); if(g0) g0.classList.add('is-open');
  window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted:true })); await sleep(100);
  T('pageshow(persisted) with a stored session/guest hides a stale gate', !gateOpen());

  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, results:out, failures:failed };
})();
