"""CODIS-TEACHER-TIERS (3.29.0) — ندرة غرفة الأستاذ المستقلة (برونزية/فضية/ذهبية).
  py -3 tools/patch_v42.py app/CODIS_FINAL.html app/CODIS_FINAL.html     (بعد patch_v41؛ ثم set_version.py 3.29.0) — أو: sh tools/rebuild_v42.sh
  المحرك: tools/identity/v42_core.js · الألوان: v42.css · صور البطاقات الثلاث: tools/make_teacher_tiers_art.py (تُولَّد من صورة الأستاذ الأصلية في backups/before_v42)."""
import sys, os, base64, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-TEACHER-TIERS' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:140])
    s = s.replace(old, new)
def line_of(prefix, new):
    global s
    assert s.count(prefix) == 1, ('prefix count', s.count(prefix), prefix[:100])
    i = s.index(prefix); j = s.index('\n', i); s = s[:i] + new + s[j:]

core = rd('v42_core.js').rstrip() + '\n'
css = rd('v42.css'); assert '</style' not in css and '<!--' not in css
once("/* البيانات الافتراضية لأول تشغيل فقط */\nfunction seedData(){", core + "\n/* البيانات الافتراضية لأول تشغيل فقط */\nfunction seedData(){")

# ---------- الندرة والقيمة ----------
once("function econRarityById(id){ return econCfg().rarities.find(r=>r.id === id) || null; }",
     "function econRarityById(id){ return econCfg().rarities.find(r=>r.id === id) || codisTeacherTierById(id); }   /* CODIS-TEACHER-TIERS: درجات الأستاذ بشكل الندرة (id/name/tone/order) لكنها خارج econCfg().rarities */")
once("if(item && item.room === 'learn') return ECON_LEARN_COIN;", "if(item && item.room === 'learn') return codisTeacherCoin(codisTeacherTierOf(item));   /* CODIS-TEACHER-TIERS: 10 / 12.5 / 20 حسب الدرجة (البرونزية = ECON_LEARN_COIN القديمة) */")
once("const rarity = (room !== 'learn' && rids.indexOf(x.rarity) !== -1) ? x.rarity : fallbackRarity;",
     "const rarity = room === 'learn' ? (codisTeacherTierOk(x.rarity) || 'bronze') : (rids.indexOf(x.rarity) !== -1 ? x.rarity : fallbackRarity);   /* CODIS-TEACHER-TIERS: الأستاذ = برونزية/فضية/ذهبية؛ القديم بلا معرّف درجة ← برونزية (تطبيع قابل للتكرار بلا أثر) */")
once("rarityTone:econTones().indexOf(x.rarityTone) !== -1 ? x.rarityTone : 'c',", "rarityTone:codisToneOk(x.rarityTone),")
once("rarityTone:econTones().indexOf(o.rarityTone) !== -1 ? o.rarityTone : 'c',", "rarityTone:codisToneOk(o.rarityTone),")

# ---------- المحرك ----------
once("  function recentIds(room){", """  /* ===== CODIS-TEACHER-TIERS: سحب الأستاذ بمرحلتين، حالة مستقلة كلياً (لا Pity ولا ندرات عامة؛ سجل التكرار recent لغرفة learn فقط) ===== */
  function teacherTable(ctxKey, o){
    const tiers = codisTeacherTiers(), pool = poolOf('learn');
    if(!pool.length) return [];
    const a = o && o.adaptive, ad = (a && a.period === ctxKey) ? codisTeacherAdaptive(a.period, a.count) : null;
    const rows = tiers.map(t=>({ r:t, w:wnum(ad && ad.weights[t.id] !== undefined ? ad.weights[t.id] : t.weight), n:pool.filter(x=>x.rarity === t.id && wnum(x.weight) > 0).length, boosted:false }));
    let total = rows.reduce((s, x)=>s + x.w, 0);
    if(total <= 0){ rows.forEach(x=>{ x.w = 1; }); total = rows.length; }
    rows.forEach(x=>{ x.p = x.w / total; });
    if(CodisLimits.bypass('reward.protectedOdds')){   /* المطوّر: إعادة موازنة نسبية على الدرجات المتاحة فقط */
      const av = rows.filter(x=>x.n > 0), tot = av.reduce((s, x)=>s + x.w, 0);
      if(!av.length) return [];
      rows.forEach(x=>{ x.p = x.n > 0 ? x.w / tot : 0; });
    } else {   /* المستخدم: احتمال درجة بلا مكافآت ينزل إلى أقرب درجة أدنى متاحة فقط (لا تركيز نحو الأعلى بحذف الأدنى)؛ البرونزية الفارغة = مكافأة عامة برونزية */
      for(let i = rows.length - 1; i > 0; i--){
        if(rows[i].n > 0 || !(rows[i].p > 0)) continue;
        let j = i - 1; while(j >= 0 && rows[j].n === 0) j--;
        if(j >= 0){ rows[j].p += rows[i].p; rows[i].p = 0; }
      }
    }
    return rows;
  }
  function genericTeacher(){ const r = codisTeacherTiers()[0], coin = codisTeacherCoin(r.id); return { generic:true, reward:null, genericName:'مكافأة ' + r.name, rarity:r, odds:100, pity:false, emptyPool:true, coinValue:coin, storePrice:econAutoStore(coin) }; }
  function rollTeacher(ctxKey, o){
    const table = teacherTable(ctxKey, o), row = table.length ? weightedPick(table, x=>x.p) : null;
    if(!row) return genericTeacher();
    const rows = row.n > 0 ? rewardTable('learn', row.r.id) : [];
    const pick = rows.length ? (weightedPick(rows, x=>x.w) || rows[0]) : null;
    const a = o && o.adaptive, ad = (a && a.period === ctxKey) ? codisTeacherAdaptive(a.period, a.count) : null, coin = pick ? econEffCoin(pick.item, row.r) : codisTeacherCoin(row.r.id);
    return { generic:false, ctxKey:ctxKey, eligible:false, reward:pick ? pick.item : null, genericName:pick ? '' : 'مكافأة ' + row.r.name, rarity:row.r, odds:Math.round(row.p * 1000) / 10, pity:false,
      adaptive:ad ? { period:ad.period, count:ad.count, over:ad.over, dec:Math.round(ad.dec * 1e6) / 1e6, cOdds:Math.round(ad.cOdds * 1e6) / 1e6 } : null,
      coinValue:coin, storePrice:econAutoStore(coin) };
  }
  function recentIds(room){""")
once("  function roll(room, ctxKey, o){\n    const table = rarityTable(room, ctxKey, o);", "  function roll(room, ctxKey, o){\n    if(room === 'learn') return rollTeacher(ctxKey, o);   /* CODIS-TEACHER-TIERS */\n    const table = rarityTable(room, ctxKey, o);")
once("function explain(room, ctxKey, o){ return rarityTable(room, ctxKey, o).map(", "function explain(room, ctxKey, o){ if(room === 'learn') return teacherTable(ctxKey, o).map(x=>({ id:x.r.id, p:x.p, boosted:false })); return rarityTable(room, ctxKey, o).map(")
once("return { roll, commit, rollPenalty, commitPenalty, explain, setRng, pityState, pick:weightedPick };", "return { roll, commit, rollPenalty, commitPenalty, explain, setRng, pityState, pick:weightedPick, teacherTable };")

# ---------- المصفوفة المالية ----------
line_of("    { id:'learn', name:'مكافأة غرفة الأستاذ'", """    { id:'learn_bronze', name:'مكافأة غرفة الأستاذ — برونزية', room:'learn', rarity:'bronze', scope:'learn', roomKey:'learn', ref:10, min:10, max:12.5, maxOpen:true, fixed:false, fixedId:null, type:'pool' },
    { id:'learn_silver', name:'مكافأة غرفة الأستاذ — فضية', room:'learn', rarity:'silver', scope:'learn', roomKey:'learn', ref:12.5, min:12.5, max:20, maxOpen:true, fixed:false, fixedId:null, type:'pool' },
    { id:'learn_gold', name:'مكافأة غرفة الأستاذ — ذهبية', room:'learn', rarity:'gold', scope:'learn', roomKey:'learn', ref:20, min:20, max:30, maxOpen:false, fixed:false, fixedId:null, type:'pool' },""")
once("function codisFinCardById(id){ return codisFinCards().find(c=>c.id === id) || null; }", "function codisFinCardById(id){ if(id === 'learn') id = 'learn_bronze'; return codisFinCards().find(c=>c.id === id) || null; }   /* CODIS-TEACHER-TIERS: المعرّف القديم 'learn' = البرونزية */")
once("function codisFinInRange(c, coin){ const v = Math.round(Number(coin) * 100) / 100; return v >= c.min - 1e-9 && v <= c.max + 1e-9; }",
     "function codisFinInRange(c, coin){ const v = Math.round(Number(coin) * 100) / 100; return v >= c.min - 1e-9 && (c.maxOpen ? v < c.max - 1e-9 : v <= c.max + 1e-9); }   /* CODIS-TEACHER-TIERS: برونزية/فضية الأستاذ حدّها الأعلى مفتوح فلا غموض عند 12.5 و20 */")
once("if(cards.length !== 23) out.problems.push('count ' + cards.length);", "if(cards.length !== 25) out.problems.push('count ' + cards.length);")
once("else if(c.id === 'learn'){ if(c.ref !== ECON_LEARN_COIN) out.problems.push('learn ref'); }",
     "else if(c.room === 'learn'){ const t = codisTeacherTierById(c.rarity); if(!t || c.ref !== t.ref || c.min !== t.min || c.max !== t.max) out.problems.push('teacher tier ' + c.id); else if(t.id === 'bronze' && c.ref !== ECON_LEARN_COIN) out.problems.push('learn ref'); }")
once("if(card.room === 'learn') return { room:'learn', rarity:econCfg().rarities[0].id, variantOf:null, weight:10 };", "if(card.room === 'learn') return { room:'learn', rarity:card.rarity || 'bronze', variantOf:null, weight:10 };")
once("target = coin < codisFinMinCoin() ? codisFinCardById('learn') :", "target = coin < codisFinMinCoin() ? codisFinCardById('learn_bronze') :")
once("      const card = codisFinCardById(it.fin.card);\n      if(card){ if(card.fixed){",
     "      if(it.fin.card === 'learn'){ it.fin.card = 'learn_' + codisTeacherTierForCoin(it.fin.coin); }   /* CODIS-TEACHER-TIERS: ترحيل المعرّف القديم مرة واحدة (بعدها لا يطابق) */\n      const card = codisFinCardById(it.fin.card);\n      if(card && card.room === 'learn'){ it.room = 'learn'; it.rarity = card.rarity; delete it.variantOf; }\n      if(card){ if(card.fixed){")

# ---------- المحرر ----------
once("const coin = room === 'learn' ? ECON_LEARN_COIN : econCoinFor(rarityId, econScopeOfRoom(room)); return 'استبدال '",
     "const tt = room === 'learn' ? (codisTeacherTierById(rarityId) || codisTeacherTiers()[0]) : null, coin = tt ? tt.ref : econCoinFor(rarityId, econScopeOfRoom(room)); return (tt ? tt.ar + ' (' + econFmt(tt.min) + '–' + econFmt(tt.max) + ') · ' : '') + 'استبدال '")
once("econRewardHintText(d.rarity, d.room)", "econRewardHintText(d.room === 'learn' ? codisTeacherTierOf(d) : d.rarity, d.room)")
once("      econField(ic('clipboard-check') + 'القائمة', '<select class=\"eco-sel\" id=\"' + prefix + '-room\"",
     "      '<div id=\"' + prefix + '-trarity-wrap\"' + (d.room === 'learn' ? '' : ' style=\"display:none;\"') + '>' + econField(ic('star') + 'الندرة', '<select class=\"eco-sel\" id=\"' + prefix + '-trarity\" onchange=\"econRewardRarityChanged(\\'' + prefix + '\\')\">' + codisTeacherTiers().map(t=>'<option value=\"' + t.id + '\"' + (t.id === codisTeacherTierOf(d) ? ' selected' : '') + '>' + t.ar + ' · ' + t.en + '</option>').join('') + '</select>') + '</div>' +\n      econField(ic('clipboard-check') + 'القائمة', '<select class=\"eco-sel\" id=\"' + prefix + '-room\"")
once("  h.textContent = econRewardHintText(r.value, l ? l.value : 'tasks');",
     "  { const tw = document.getElementById(prefix + '-trarity-wrap'), tr = document.getElementById(prefix + '-trarity'), isL = !!l && l.value === 'learn'; if(tw) tw.style.display = isL ? '' : 'none';\n    h.textContent = econRewardHintText(isL && tr ? tr.value : r.value, l ? l.value : 'tasks'); }")
once("rarity:(g('room').value === 'learn' ? econCfg().rarities[0].id : g('rarity').value)", "rarity:(g('room').value === 'learn' ? (codisTeacherTierOk((g('trarity') || {}).value) || 'bronze') : g('rarity').value)")
once("const rar = (room === 'learn' ? cfg[0] : (econRarityById(g('rarity')", "const rar = (room === 'learn' ? (codisTeacherTierById(g('trarity') ? g('trarity').value : '') || codisTeacherTiers()[0]) : (econRarityById(g('rarity')")
once("  if(it.room === 'learn') return '';\n", "  if(it.room === 'learn'){ const _t = codisTeacherTierById(codisTeacherTierOf(it)); return '<span class=\"rpt-tag rar-badge rar-' + _t.tone + '\" title=\"' + _t.ar + '\"><b>' + _t.en + '</b><span>' + _t.ar + '</span></span>'; }   /* CODIS-TEACHER-TIERS */\n")

# ---------- البطاقات ----------
once("function codisCardKey(e){ const k = String(e && e.rarityTone || '').toUpperCase(); return CODIS_CARD_SLOTS[k] ? k : null; }",
     "function codisCardKey(e){ if(e && codisTeacherToneOk(e.rarityTone)) return 'C'; const k = String(e && e.rarityTone || '').toUpperCase(); return CODIS_CARD_SLOTS[k] ? k : null; }   /* CODIS-TEACHER-TIERS: بطاقة الأستاذ 4:5 كاليومية؛ مفتاح C هنا للمرور بنفس المسارات فقط (codisRewardCardHtml تحوّلها لبطاقة الأستاذ) */")
once("label:o.label, stickerId:e.stickerId });   /* غرفة الأستاذ", "label:o.label, stickerId:e.stickerId, tier:codisTeacherTierOf(e) });   /* غرفة الأستاذ")
a0 = s.index("function codisSpecialCardHtml(k, o){")
a1 = s.index("\n}\n", a0) + 3
new_fn = """function codisSpecialCardHtml(k, o){
  o = o || {};
  const tier = (k === 'teacher' && o.tier) ? codisTeacherTierOk(o.tier) : '', tt = tier ? codisTeacherTierById(tier) : null, ak = tier ? 'teacher_' + tier : k;   /* CODIS-TEACHER-TIERS: صورة ولوحة لكل درجة */
  const S = CODIS_SPECIAL_CARD_SLOTS[ak], coin = econC(Math.max(0, Number(o.coin) || 0)), name = String(o.name || '');
  return (o.plain ? '<div class="rwc-wrap is-on">' : '<div class="rv rwc-wrap" data-s="1">') + '<div class="rwc scx scx-' + k + (tt ? ' scx-t-' + tier : '') + ' rwc-c" role="img" aria-label="' + escapeHtml(o.label || ((tt ? tt.ar + ' — ' : '') + name + (coin > 0 ? ' — ' + econFmt(coin) : ''))) + '">' +
    '<div class="rwc-stage" style="--ar:' + S.ar + ';--ar-css:' + S.w + ' / ' + S.h + '">' +
    (CODIS_SPECIAL_CARD_ART[ak] ? '<img class="rwc-art scx-art" src="' + CodisArt.src(CODIS_SPECIAL_CARD_ART[ak]) + '" alt="" draggable="false">' : '<div class="rwc-art scx-ph scx-ph-' + escapeHtml(String(o.tone || 'normal')) + '" aria-hidden="true"></div>') + codisStickerLayerHtml(o, 's', k) +
    (tt ? '<span class="scx-tag" aria-hidden="true">' + tt.en + '</span>' : '') +
    '<div class="rwc-slot scx-plate" style="' + codisSpecialPlateStyle(ak) + '"><span class="scx-row"><span class="scx-name" dir="auto">' + escapeHtml(name) + '</span>' +
    (coin > 0 ? '<span class="scx-coin">' + codisIcon('coin') + '<b>' + econFmt(coin) + '</b></span>' : '') + '</span></div>' +
    '</div></div></div>';
}
"""
s = s[:a0] + new_fn + s[a1:]
once("  teacher:     { ar:0.8, w:800, h:1000, plate:[22, 80.9, 56, 8.6] },", "  teacher:     { ar:0.8, w:800, h:1000, plate:[22, 80.9, 56, 8.6] },\n  teacher_bronze:{ ar:0.8, w:800, h:1000, plate:[22, 80.9, 56, 8.6] },\n  teacher_silver:{ ar:0.8, w:800, h:1000, plate:[22, 80.9, 56, 8.6] },\n  teacher_gold:  { ar:0.8, w:800, h:1000, plate:[22, 80.9, 56, 8.6] },")
tmp = tempfile.mkdtemp()
subprocess.check_call(['py', '-3', os.path.join(HERE, 'make_teacher_tiers_art.py'), os.path.join(HERE, '..', 'backups', 'before_v42', 'CODIS_FINAL.html'), tmp], stdout=subprocess.DEVNULL)
art = ''.join('CODIS_SPECIAL_CARD_ART.teacher_%s = "data:image/webp;base64,%s";\n' % (n, base64.b64encode(open(os.path.join(tmp, n + '.webp'), 'rb').read()).decode()) for n in ('bronze', 'silver', 'gold'))
once("(function(){ try{ Object.keys(CODIS_SPECIAL_CARD_ART).forEach(k=>{ const i = new Image(); i.src = CODIS_SPECIAL_CARD_ART[k]; }); }catch(x){} })();",
     "(function(){ try{ Object.keys(CODIS_SPECIAL_CARD_ART).forEach(k=>{ const i = new Image(); i.src = CODIS_SPECIAL_CARD_ART[k]; }); }catch(x){} })();\n/* CODIS-TEACHER-TIERS: ثلاث صور لبطاقة الأستاذ (tools/make_teacher_tiers_art.py) — بلا تحميل مسبق (ذاكرة WebKit)؛ تُفكّ عند أول عرض */\n" + art)
once("function econCardName(it, rar){ { const sp = codisSlotOf(it); if(sp) return sp.label; }", "function econCardName(it, rar){ { const sp = codisSlotOf(it); if(sp) return sp.label; } if(it && it.room === 'learn') return codisTeacherTierById(codisTeacherTierOf(it)).ar;   /* CODIS-TEACHER-TIERS */")
once("(codisSlotOf(it) || { label:it.rarityName }).label", "(codisSlotOf(it) || { label:(it.room === 'learn' ? codisTeacherTierById(codisTeacherTierOf(it)).ar : it.rarityName) }).label")

i = s.index('<style id="codis-v41-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v42-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('v42 applied')
