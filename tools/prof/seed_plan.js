(async()=>{ const sleep = ms=>new Promise(r=>setTimeout(r, ms)); codisConfirm = async()=>true; try{ CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{}; }catch(e){}
  const btn = (root, txt)=>[...document.querySelectorAll(root + ' button')].find(b=>b.getClientRects().length && b.innerText.includes(txt));
  document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(500);
  const b = btn('#page-planning', 'إضافة خطة'); if(b){ b.click(); await sleep(400); }
  const ti = document.getElementById('plan-tasks-input'); ti.value = '1- 14 صفحة مراجعة\n2- !تقرير المبيعات\n3- اتصال بالعائلة'; ti.dispatchEvent(new Event('input', { bubbles:true }));
  const li = document.getElementById('plan-learn-input'); li.value = '1- درس الرياضيات'; li.dispatchEvent(new Event('input', { bubbles:true }));
  switchWriteTab('tasks'); distributePlan(); await sleep(800); return 1; })()
