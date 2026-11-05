// Theme switch end-to-end through the real Settings UI. SHOT=prefix
export default async function(c){
  const P = process.env.SHOT || 'th';
  await c.load(); await c.evaluate(`localStorage.removeItem('codis_theme_v1'); 1`); await c.load(); await c.sleep(1800);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  const st = ()=>c.evaluate(`({ t:CodisTheme.get(), attr:document.documentElement.getAttribute('data-theme'), ls:localStorage.getItem('codis_theme_v1'), bar:document.querySelector('meta[name=theme-color]').content, bg:getComputedStyle(document.body).backgroundColor, font:getComputedStyle(document.querySelector('.page-title')||document.body).fontFamily.slice(0,40), badge:(document.getElementById('home-theme-state')||{}).textContent, checked:[...document.querySelectorAll('#theme-opts .thm-opt')].map(o=>o.getAttribute('aria-checked')).join() })`);
  console.log('boot', JSON.stringify(await st()));
  await c.evaluate(`navigateToPage('settings')`); await c.sleep(800); await c.screenshot(P + '_home_paper.png');
  await c.evaluate(`openSettingsCategory('appearance')`); await c.sleep(900); await c.screenshot(P + '_page_paper.png');
  await c.tap('#theme-opts [data-theme-opt="dark"]'); await c.sleep(900);
  console.log('after dark tap', JSON.stringify(await st())); await c.screenshot(P + '_page_dark.png');
  await c.evaluate(`showSettingsHome()`); await c.sleep(700); await c.screenshot(P + '_home_dark.png');
  await c.load(); await c.sleep(2200);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2200); }
  console.log('reload (persisted?)', JSON.stringify(await st()));
  await c.evaluate(`navigateToPage('settings')`); await c.sleep(700); await c.evaluate(`openSettingsCategory('appearance')`); await c.sleep(800);
  await c.tap('#theme-opts [data-theme-opt="paper"]'); await c.sleep(900);
  console.log('back to paper', JSON.stringify(await st())); await c.screenshot(P + '_page_paper2.png');
}
