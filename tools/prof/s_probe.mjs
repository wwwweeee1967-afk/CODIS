import { readFileSync } from 'node:fs';
// Evaluate PROBE (JS expression) after guest boot + optional PAGE navigation; prints JSON.
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  if(process.env.SEED){ await c.evaluate(readFileSync('tools/prof/seed_plan.js', 'utf8')); await c.sleep(600); }
  if(process.env.PAGE) { await c.evaluate(process.env.PAGE); await c.sleep(1500); }
  console.log(JSON.stringify(await c.evaluate(process.env.PROBE), null, 1));
}
