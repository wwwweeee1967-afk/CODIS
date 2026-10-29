#!/usr/bin/env python3
"""CODIS-BOXES-V4 (بعد patch_v5.py): نموذج احتمالات الصناديق الجديد (بديل 82.7%).
 النموذج (مصدر واحد: effectiveBase → effective → roll والواجهة):
  1) الجوائز تُصنَّف بقيمتها الفعلية بالكوين إلى 7 نطاقات ثابتة (≤30 · ≤120 · ≤300 · ≤700 · ≤1500 · ≤3500 · أعلى) — ثابتة لا تتحرك بتغيّر محتوى المخزون؛ النطاق الفارغ يُتجاوز.
  2) أهلية الصندوق: الجائزة ≤ 12× السعر الأساسي (الأغلى يضم الجميع، فلا جائزة مستبعدة من كل الصناديق). لا حدّ أدنى للقيمة (أُلغي؛ المطوّر قادر على فرضه).
  3) الاحتمال لكل نطاق ∝ المتوسط^(−β) ويُحَلّ β لكل صندوق ليكون عائد البيع المتوقع = ρ × السعر المدفوع (ρ = .78 .82 .86 .90 .93) ⇒ لا ربح مضمون أبداً والصناديق الأغلى أعلى قيمة.
  4) سقف «النفايات»: نطاقات متوسطها < 0.4× السعر لا تتجاوز حصتها (100% · 55% · 45% · 35% · 25%) ثم يُعاد حلّ β على بقية النطاقات — الصندوق الغالي لا يعطي غالباً جائزة رخيصة.
  5) حدّ أدنى لكل نطاق 0.4%، تقريب بالألف بأكبر باقٍ (المجموع 1000 تماماً)، لا سالب. داخل النطاق كل جائزة متساوية. لا Pity (الاحتمال المعروض = الفعلي دائماً).
 كل عتبات المطوّر (RTP/pWin/المرجع/السعر/المجموعات) تبقى عبر CodisLimits."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-BOXES-V4' in s: sys.exit('already patched (CODIS-BOXES-V4)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

def cut_between(start, end, new, label):
    global s
    if s.count(start) != 1: sys.exit('start "%s" matched %d' % (label, s.count(start)))
    i = s.index(start); j = s.index(end, i + len(start))
    s = s[:i] + new + s[j:]

# حدّ القيمة الأدنى: يُلغى افتراضياً (الأهلية بالسقف الأعلى والنموذج الاحتمالي)
rep("const MIN_VALUE = Object.freeze({ bx1:0, bx2:50, bx3:90, bx4:165, bx5:245 });", "const MIN_VALUE = Object.freeze({ bx1:0, bx2:0, bx3:0, bx4:0, bx5:0 });   /* CODIS-BOXES-V4: لا استبعاد بالقيمة الدنيا؛ النموذج الاحتمالي يخفّض الرخيص تدريجياً (المطوّر قادر على فرض حدّ) */", 'MIN_VALUE')

classes_new = r"""  /* CODIS-BOXES-V4 — نطاقات قيمة ثابتة (كوين). الفئة = نطاق فيه جوائز مؤهّلة؛ المتوسط للحساب والاحتمال لكل نطاق */
  const BAND_EDGES = [30, 120, 300, 700, 1500, 3500], BAND_NAMES = ['أساسية', 'متوسطة', 'جيدة', 'قيّمة', 'نادرة', 'أسطورية', 'خرافية'];
  const RHO = { bx1:.78, bx2:.82, bx3:.86, bx4:.90, bx5:.93 }, DUD_CAP = { bx1:1, bx2:.55, bx3:.45, bx4:.35, bx5:.25 }, DUD_RATIO = .4, FLOOR_PM = 4, REF_CAP = 900;
  function bandOf(v){ let k = 0; while(k < BAND_EDGES.length && v > BAND_EDGES[k]) k++; return k; }
  function classes(minV, capV){
    const lim = capV === undefined || capV === null ? Infinity : capV;
    const items = prizePool().map(x=>({ x:x, v:valueOf(x) })).filter(o=>o.v > 0 && o.v >= (minV || 0) && o.v <= lim).sort((a,b)=>a.v - b.v || a.x.id.localeCompare(b.x.id)), by = [];
    items.forEach(o=>{ const b = bandOf(o.v); (by[b] = by[b] || []).push(o); });
    const out = []; by.forEach((g, b)=>{ if(!g || !g.length) return; out.push({ items:g.map(o=>o.x), vals:g.map(o=>o.v), min:g[0].v, max:g[g.length - 1].v, mean:g.reduce((s,o)=>s + o.v, 0) / g.length, band:b }); });
    const tones = econTones();
    return out.map((c,k)=>Object.assign(c, { id:'vc' + (k + 1), name:BAND_NAMES[c.band] || ('فئة ' + (k + 1)), order:k + 1, tone:tones[Math.min(tones.length - 1, Math.floor(k * tones.length / out.length))], n:c.items.length }));
  }
"""
cut_between("  /* فئات القيمة من المكافآت المؤهّلة الآن:", "  /* احتمالات الفئات الفعلية للمستوى (بالألف", classes_new, 'classes')

eff_new = r"""  /* أعداد حقيقية (مجموعها 1000) ← أعداد صحيحة مجموعها 1000 بأكبر باقٍ، بحدّ أدنى FLOOR_PM لكل فئة، بلا سالب */
  function toPm(raw, total){
    total = total || 1000;
    const n = raw.length, floor = Math.min(FLOOR_PM, Math.floor(total / n)), out = raw.map(x=>Math.max(floor, Math.floor(x)));
    let left = total - out.reduce((a,b)=>a + b, 0);
    const ord = raw.map((x,i)=>({ f:x - Math.floor(x), i:i })).sort((a,b)=>b.f - a.f || a.i - b.i);
    for(let j = 0; left > 0; j = (j + 1) % n){ out[ord[j].i]++; left--; }
    while(left < 0){ let k = 0; for(let i = 1; i < n; i++) if(out[i] > out[k]) k = i; if(out[k] <= floor) break; out[k]--; left++; }
    return out;
  }
  /* توزيع النموذج لمستوى: cs = فئات مؤهّلة بترتيب القيمة، price = السعر المدفوع، target = العائد المتوقع بالكوين. يُعيد pm (بالألف) */
  function solve(cs, price, target, dudCap){
    const n = cs.length; if(n === 1) return [1000];
    const mean = cs.map(c=>c.mean), dud = cs.map(c=>c.mean < DUD_RATIO * price), nd = dud.filter(x=>!x).length;
    const groupPm = (beta, idx, mass)=>{ const w = idx.map(i=>Math.pow(mean[i], -beta)), s = w.reduce((a,b)=>a + b, 0) || 1; return w.map(x=>x / s * mass); };
    const ev = p=>p.reduce((s,x,i)=>s + x / 1000 * mean[i], 0);
    const solveBeta = f=>{ let lo = -4, hi = 14; for(let i = 0; i < 70; i++){ const m = (lo + hi) / 2; if(ev(f(m)) > target) lo = m; else hi = m; } return f(hi); };
    const all = idx=>cs.map((_, i)=>i);
    let p = solveBeta(b=>groupPm(b, all(), 1000));
    const dudMass = p.reduce((s,x,i)=>s + (dud[i] ? x : 0), 0);
    if(nd > 0 && nd < n && dudMass > dudCap * 1000){
      const D = dudCap * 1000, di = [], ni = []; cs.forEach((_, i)=>(dud[i] ? di : ni).push(i));
      p = solveBeta(b=>{ const out = new Array(n); groupPm(b, ni, 1000 - D).forEach((x, k)=>{ out[ni[k]] = x; }); groupPm(b, di, D).forEach((x, k)=>{ out[di[k]] = x; }); return out; });
    }
    let pm = toPm(p);
    const cap = Math.max(1, Math.round(CodisLimits.num('box.refTop', REF_CAP)));   /* حدّ أعلى لنسبة الفئة الأدنى (المطوّر يعدّله) */
    if(n > 1 && pm[0] > cap){ const ex = pm[0] - cap; pm[0] = cap; const rest = pm.slice(1), tot = rest.reduce((a,b)=>a + b, 0) || 1; pm = [pm[0]].concat(toPm(rest.map(x=>x / tot * (1000 - cap)), 1000 - cap)); }
    return pm;
  }
  function effectiveBase(t){
    const top = Math.max.apply(null, tiers().map(x=>x.basePrice)), cap = t.basePrice >= top ? Infinity : MAX_PRIZE_X_V() * t.basePrice;
    let cs = classes(minValue(t.id), cap);
    if(!cs.length){ if(!CodisLimits.bypass('box.empty')) return []; cs = classes(minValue(t.id)); if(!cs.length) return []; }   /* أغلى بكج يضم كل الجوائز؛ إن لم توجد جوائز مؤهّلة: غير متاح (المطوّر معفى) */
    const price = t.price > 0 ? t.price : t.basePrice * 0.7, sellK = Math.max(0.01, (Number(econCfg().sellPercent) || 80) / 100);
    const rho = Number(CodisLimits.num('box.rho.' + t.id, RHO[t.id] || .85)), target = Math.max(0, rho) * price / sellK;   /* عائد الاستبدال المطلوب ⇒ عائد البيع = ρ × السعر (< السعر دائماً) */
    const pm = solve(cs, price, target, Number(DUD_CAP[t.id]) || 1);
    const ev = pm.reduce((s,x,i)=>s + x / 1000 * cs[i].mean, 0), win = pm.reduce((s,x,i)=>s + x / 1000 * cs[i].vals.filter(v=>v > t.basePrice).length / cs[i].vals.length, 0);
    if((ev > MAX_RTP_V() * t.basePrice || win > MAX_PWIN_V()) && !CodisLimits.bypass('box.rtpGate')) return [];
    return cs.map((c,i)=>Object.assign({}, c, { pm:pm[i] }));
  }
"""
cut_between("  function effectiveBase(t){", "  /* أثر القيم الفعلية على المستوى", eff_new, 'effectiveBase')

# تسجيل ρ للمطوّر + تصدير الدوال للاختبار
rep("return { tiers, tier, pool, classes, effective, effectiveBase, stats, valueOf, minValue, owned, get, roll, buy, open, buyOpenMany, BULK };",
    "try{ Object.keys(RHO).forEach(k=>CodisLimits.reg('box.rho.' + k, 'عائد البيع المتوقع ÷ السعر — ' + k, RHO[k])); }catch(e){}\n  return { tiers, tier, pool, classes, effective, effectiveBase, stats, valueOf, minValue, owned, get, roll, buy, open, buyOpenMany, BULK, model:{ BAND_EDGES, RHO, DUD_CAP, DUD_RATIO, FLOOR_PM, solve, toPm } };", 'exports')
s = s.replace('<!-- CODIS-V5-NAV -->', '<!-- CODIS-V5-NAV -->\n<!-- CODIS-BOXES-V4 -->', 1)
if 'CODIS-BOXES-V4 -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v6 OK')
