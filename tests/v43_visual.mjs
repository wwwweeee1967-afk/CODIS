/* CODIS-V43 — visual/layout checks on real WebKit (iPhone engine) + Chromium: time badge inside its tile, bottom dock size/position (safe-area simulated), glass fallback.
   Needs: npm i playwright-core@1.49.1 (scratch folder) + installed webkit. Run: node tests/v43_visual.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html [outDir] */
import { webkit, chromium, devices } from 'playwright-core';
const url = process.argv[2], outDir = process.argv[3] || '.';
let bad = 0; const ok = (n, c, i)=>{ console.log((c ? 'PASS ' : 'FAIL ') + n + (c || i === undefined ? '' : '  -> ' + i)); if(!c) bad++; };
for(const eng of ['webkit', 'chromium']){
  const b = eng === 'webkit' ? await webkit.launch() : await chromium.launch({ executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  for(const [W, H, safe] of [[390, 844, 34], [320, 568, 0], [430, 932, 34], [844, 390, 0]]){
    const ctx = await b.newContext({ ...devices['iPhone 12'], viewport:{ width:W, height:H } }); const p = await ctx.newPage(); const errs = []; p.on('pageerror', e=>errs.push(e.message));
    await p.goto(url); await p.waitForTimeout(3000); await p.evaluate(()=>{ const g = document.getElementById('gate-guest'); if(g && g.offsetParent) g.click(); }); await p.waitForTimeout(1200);
    await p.addStyleTag({ content:':root{ --safe-b:' + safe + 'px !important; }' });
    const tag = eng + ' ' + W + 'x' + H + ' safe' + safe;
    const nav = await p.evaluate(()=>{ const s = document.querySelector('.sidebar').getBoundingClientRect(), cs = getComputedStyle(document.querySelector('.sidebar')); return { h:s.height, gap:innerHeight - s.bottom, bf:cs.backdropFilter || cs.webkitBackdropFilter, labels:[...document.querySelectorAll('.navlabel')].map(l=>({ clip:l.scrollWidth > l.clientWidth + 1 })), navH:getComputedStyle(document.documentElement).getPropertyValue('--nav-h') }; });
    const land = W > H;
    ok(tag + ' dock height ≤ 66 (' + Math.round(nav.h) + ')', nav.h <= (W <= 374 ? 70 : land ? 52 : 66));
    ok(tag + ' dock gap from bottom ' + Math.round(nav.gap) + 'px', safe ? Math.abs(nav.gap - 22) <= 1 : Math.abs(nav.gap - 10) <= 1, nav.gap);
    ok(tag + ' backdrop-filter active', !!nav.bf && nav.bf !== 'none', nav.bf);
    ok(tag + ' no clipped nav label', nav.labels.every(l=>!l.clip));
    if(!land){
      await p.evaluate(()=>{ const f = codisFin(); f.setup.done = true; f.fx = { rate:40, setAt:new Date().toISOString() };
        codisFinCreateReward({ name:'مشاهدة مباراة', kind:'time', minutes:70, stickerId:'pizza', cardId:'daily_C' }); codisFinCreateReward({ name:'ساعة قيمنق', kind:'time', minutes:60, cardId:'daily_C' });
        document.querySelector('.navbtn[data-page="settings"]').click(); rpOpenHub('reward'); setSettingsPeriod('daily'); });
      await p.waitForTimeout(1500);
      const m = await p.evaluate(()=>[...document.querySelectorAll('#settings-page-rewards .rpt')].filter(t=>t.querySelector('.dur-badge') && t.getBoundingClientRect().width).map(t=>{ const R = e=>e.getBoundingClientRect(), T = R(t), d = t.querySelector('.dur-badge'), D = R(d), s = R(d.querySelector('svg')), sk = t.querySelector('.rpt-stk'), K = sk ? R(sk) : null, rg = document.createRange(); rg.selectNodeContents([...d.childNodes].find(n=>n.nodeType === 3)); const tx = rg.getBoundingClientRect();
        return { inside:D.left >= T.left - 0.5 && D.right <= T.right + 0.5, svgW:s.width, svgInBadge:s.left >= D.left && s.right <= D.right, dy:Math.abs((tx.top + tx.height / 2) - (s.top + s.height / 2)), overlap:K ? !(K.right <= D.left || K.left >= D.right || K.bottom <= D.top || K.top >= D.bottom) : false, stkW:K ? K.width : null }; }));
      ok(tag + ' time badges found', m.length >= 2, m.length);
      ok(tag + ' badge inside tile', m.every(x=>x.inside), JSON.stringify(m));
      ok(tag + ' icon full size 11px, inside badge', m.every(x=>Math.abs(x.svgW - 11) < .6 && x.svgInBadge));
      ok(tag + ' icon vertically centred on text (≤1.6px)', m.every(x=>x.dy <= 1.6), m.map(x=>x.dy).join());
      ok(tag + ' badge does not overlap sticker', m.every(x=>!x.overlap));
      ok(tag + ' sticker keeps its 16px box (22px thumb, -3px margins)', m.every(x=>x.stkW === null || x.stkW >= 15.5), m.map(x=>x.stkW).join());
      await p.screenshot({ path:outDir + '/v43_' + eng + '_' + W + '.png' });
    }
    ok(tag + ' no JS errors', !errs.length, errs.join(' | '));
    await ctx.close();
  }
  await b.close();
}
process.exit(bad ? 1 : 0);
