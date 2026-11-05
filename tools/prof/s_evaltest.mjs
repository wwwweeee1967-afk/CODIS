// Loads the app (guest), evaluates an in-page test file (IIFE returning a promise), prints its result as JSON.
// TEST=tests/<name>_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
// (nav_browser.js cannot run here: it navigates the page, which ends the CDP evaluation)
import { readFileSync } from 'node:fs';
export default async function(c){
  const src = readFileSync(process.env.TEST, 'utf8');
  if(process.env.THEME){ await c.load(); await c.evaluate(`localStorage.setItem('codis_theme_v1', '${process.env.THEME}'); 1`); }
  await c.load(); await c.sleep(2500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2000); }
  const r = await c.evaluate(src);
  const v = typeof r === 'string' ? r : JSON.stringify(r);
  let o = null; try{ o = typeof r === 'string' ? JSON.parse(r) : r; }catch(e){}
  if(o && Array.isArray(o.results)){
    const bad = o.results.filter(x=>!x.ok);
    console.log('RESULT ' + process.env.TEST + ': passed=' + (o.passed !== undefined ? o.passed : o.results.length - bad.length) + ' failed=' + (o.failed !== undefined ? o.failed : bad.length));
    bad.forEach(x=>console.log('  FAIL ' + x.name + ' — ' + x.info));
  } else console.log('RESULT ' + process.env.TEST + ': ' + String(v).slice(0, 3000));
}
