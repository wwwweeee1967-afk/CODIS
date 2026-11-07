"""CODIS-V35 (3.22.0) — كتالوج كروت غرفة الأستاذ (محطة · حدثية) + توحيد أسعار عقوباتها.

  py -3 tools/patch_v35.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (بعد patch_v34؛ ثم set_version.py)

  1  الكروت الخاصة (7 مكافآت + 6 عقوبات) عناصر حقيقية بالكتالوج بمعرّفاتها التاريخية؛ المخطط `codisFixedDefs` للقيم فقط
  2  `codisV34Seed` صار ترحيلاً غير هدّام لمرة واحدة (settings.catalogV35)؛ الاسم/الستيكر/التفعيل/الحذف تبقى
  3  الإعدادات: غرفتان فقط (العمليات · الأستاذ)؛ المحطة والحدثية أقسام داخل الأستاذ؛ إضافة بمكان/أهمية، تعديل، تعطيل، حذف، معاينة
  4  `codisPenaltyPrice` مصدر وحيد لتكلفة التجاوز (الإعدادات · النتيجة · الخصم · بطاقات التجاوز)
  5  المتجر/المخزون/النتيجة: بلا ندرة للكروت الخاصة + الستيكر يظهر
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-V35' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:110])
    s = s.replace(old, new)
def cut(start, end):
    global s
    i = s.index(start); assert s.count(start) == 1, ('cut anchor', start[:60]); j = s.index(end, i + 1)
    s = s[:i] + s[j:]

# ---- 1) remove the old definitions (schema/seed/outcome + v34 rows + event section filler)
cut('function codisFixedDefs(){', 'function codisHabitFixedCtx(')
cut('function econRewardRowHtml(it){', '/* CODIS-CLARITY: كل قائمة تُرسم بقسمها')
cut('function econPunishRowHtml(it){', 'function econRenderPunish(){')
cut('function codisFillEventPenalties(){', '/* دوال الغرف القديمة بقيت بنفس الاسم')
cut('function setSettingsPeriod(p){', 'let rpKind = ')   # V35: صفحات مستقلة بدل التمرير (البديل بـv35.js)
once('function codisHabitFixedCtx(', '/* ===== CODIS-V35 ===== */\n' + rd('v35.js') + '\nfunction codisHabitFixedCtx(')

# ---- 2) normalization keeps catalog cards (no duplicates; migration once)
once("const rids = settings.economy.rarities.map(r=>r.id), fallbackRarity = rids[0];",
     "const rids = settings.economy.rarities.map(r=>r.id), fallbackRarity = rids[0];\n  settings.rewardItems = codisV35Dedupe(settings.rewardItems); settings.punishItems = codisV35Dedupe(settings.punishItems);   /* CODIS-V35: لا نسختان من الكرت نفسه */")

# ---- 3) settings: two rooms; lists exclude catalog cards (they render in their own sections)
once("const items = all.filter(x=>x.room === room && x.fixedGroup !== 'event').sort(sortFn);   /* V34: عقوبات الحدثية ثابتة بقسمها المستقل */",
     "const items = all.filter(x=>x.room === room).sort(room === 'habits' ? codisV35Sort : sortFn);   /* V35: غرفة التأديب قائمة مستقلة كبقية الغرف */")
once("'<p class=\"eco-note\" id=\"' + prefix + '-hint\">' + econRewardHintText(d.rarity, d.room) + '</p>' +",
     "codisV35PlaceHtml(prefix, 'reward', it) + '<p class=\"eco-note\" id=\"' + prefix + '-hint\">' + econRewardHintText(d.rarity, d.room) + '</p>' +")
once("  h.textContent = econRewardHintText(r.value, l ? l.value : 'tasks');\n}", "  h.textContent = econRewardHintText(r.value, l ? l.value : 'tasks');\n  codisV35PlaceSync(prefix, 'reward');\n}")
once("  h.textContent = econPunishHintText(v.value, l ? l.value : 'tasks');\n}", "  h.textContent = econPunishHintText(v.value, l ? l.value : 'tasks');\n  codisV35PlaceSync(prefix, 'punish');\n}")
once("  let bad = false;\n  const num = (id, def)=>{ const raw = g(id).value.trim();", "  { const spv = codisV35ReadPlace(prefix, 'reward', name, codisStickerIdOk((g('sticker') || {}).value)); if(spv) return spv; }\n  let bad = false;\n  const num = (id, def)=>{ const raw = g(id).value.trim();")
once("  return { name:name, severity:g('sev').value, room:g('room').value, coinBypassCost:null, enabled:g('on').checked };", "  { const spv = codisV35ReadPlace(prefix, 'punish', name); if(spv) return spv; }\n  return { name:name, severity:g('sev').value, room:g('room').value, coinBypassCost:null, enabled:g('on').checked };")
once("  const v = econReadReward('eco-new-r'); if(!v) return;\n", "  const v = econReadReward('eco-new-r'); if(!v) return;\n  if(v.slot) return codisV35AddSlot('reward', v);\n")
once("  const v = econReadPunish('eco-new-p'); if(!v) return;\n", "  const v = econReadPunish('eco-new-p'); if(!v) return;\n  if(v.slot) return codisV35AddSlot('punish', v);\n")
once("  const it = data.settings.rewardItems.find(x=>x.id === id); if(!it || it.fixed) return;\n  const ok = await codisConfirm(CodisCopy.deleteReward(it.name)); if(!ok) return;",
     "  const it = data.settings.rewardItems.find(x=>x.id === id); if(!it) return;\n  const ok = await codisConfirm(it.fixed ? codisV35DelCopy(it) : CodisCopy.deleteReward(it.name)); if(!ok) return;")
once("  const ok = await codisConfirm(CodisCopy.deletePunish(it.name)); if(!ok) return;", "  const ok = await codisConfirm(it.fixed ? codisV35DelCopy(it) : CodisCopy.deletePunish(it.name)); if(!ok) return;")
once("function econRenderRewards(){\n  const list = document.getElementById('reward-list'); if(!list) return;", "function econRenderRewards(){\n  const list = document.getElementById('reward-list'); if(!list) return;\n  codisV35Cat('reward');")
once("    '<div class=\"eco-grid2\">' +\n    econField('الشدة',", "    codisV35PlaceHtml(prefix, 'punish', it) + '<div class=\"eco-grid2\">' +\n    econField('الشدة',")
once("  const v = econReadReward('eco-edit-r'); if(!v) return;\n", "  const v = econReadReward('eco-edit-r'); if(!v) return;\n  if(v.slot) return codisV35SaveSlot('reward', it, v);\n")
once("  const v = econReadPunish('eco-edit-p'); if(!v) return;\n", "  const v = econReadPunish('eco-edit-p'); if(!v) return;\n  if(v.slot) return codisV35SaveSlot('punish', it, v);\n")
# sticker picker preview: the real discipline card (not an operations card with a rarity)
once("  try{ return econStoreFaceHtml({ room:room, name:nm, stickerId:id }, rar, { label:nm }); }catch(x){ return ''; }", "  { const sd = codisV35FormDef(prefix, 'reward'); if(sd){ try{ return econStoreFaceHtml({ fixed:true, id:sd.id, room:'habits', name:nm, stickerId:id }, cfg[0], { label:nm }); }catch(x){ return ''; } } }\n  try{ return econStoreFaceHtml({ room:room, name:nm, stickerId:id }, rar, { label:nm }); }catch(x){ return ''; }")
# html: remove the third room button (twice), containers, old event section
btn = '<button type="button" class="arch-filter-btn" data-room="habits" aria-pressed="false" onclick="setSettingsRoom(\'habits\')">الحدثية<span class="arch-filter-n"></span></button>'
assert s.count(btn) == 2; s = s.replace(btn, btn.replace('الحدثية<span', 'غرفة التأديب<span'))   # غرفة التأديب غرفة مستقلة
once('<div class="eco-list rpu-list" id="reward-list"></div>', '<div class="eco-list rpu-list" id="reward-list"></div>\n          <div class="cat-box" id="reward-cat" hidden></div>')
once('<div class="eco-list rpu-list" id="punish-list"></div>', '<div class="eco-list rpu-list" id="punish-list"></div>\n          <div class="cat-box" id="punish-cat" hidden></div>')
i = s.index('<section class="rpu-sec" id="rpu-p-event"'); j = s.index('</section>', i) + len('</section>')
s = s[:i].rstrip(' \n') + '\n' + s[j:]
once("habits:'الحدثية'", "habits:'التأديب'")
once("'عقوبات بسيطة لليوم.' : 'مكافآت بسيطة وشائعة، أرخص من البقية وبلا درجات ندرة.');", "'عقوبات بسيطة لليوم.' : 'مكافآت بسيطة وشائعة، أرخص من البقية وبلا درجات ندرة.') + '';")

once("d.room === 'learn' ? ' style=\"display:none;\"' : ''", "(d.room === 'learn' || d.room === 'habits') ? ' style=\"display:none;\"' : ''")
once("(l && l.value === 'learn') ? 'none' : ''", "(l && (l.value === 'learn' || l.value === 'habits')) ? 'none' : ''")
once("الحدثية: مواقف ما تصير كل يوم، ممكن أسبوع أو أكثر. إذا صار الموقف ونجحت تاخذ مكافأة، وإذا فشلت تاخذ عقوبة.", "غرفة التأديب: مكافآت وعقوبات العادات (المحطة · الحدثية) — تُصنَّف بأهمية العادة: عادية · مهمة · حرجة، لا بالندرة.")
# ---- 4) single price source
once("if(p && p.scope === 'habit') return ({ LOW:31.25, MEDIUM:62.5, HIGH:125 })[econNormSeverity(p.severity, 'MEDIUM')] || 62.5;",
     "if(p && p.scope === 'habit') return codisPenaltyPrice('station', econNormSeverity(p.severity, 'MEDIUM')) || 62.5;   /* V35: المصدر الوحيد */")
once("'\">' + econSevLabel(e.severity || 'MEDIUM') + '</span>' + (cost > 0 ? ' ' + 'تجاوزها بـ '", "'\">' + escapeHtml(e.fixedLabel || econSevLabel(e.severity || 'MEDIUM')) + '</span>' + (cost > 0 ? ' ' + 'تجاوزها بـ '")

# ---- 5) store / inventory / result: no rarity for catalog cards, sticker shows
once("function econCardName(it, rar){ ", "function econCardName(it, rar){ { const sp = codisSlotOf(it); if(sp) return sp.label; } ")
once("'<div class=\"store-detail-tags\">' + econRarityBadge(rar.tone, rar.id, econCardName(it, rar), rar.order) + '</div>'",
     "'<div class=\"store-detail-tags\">' + (codisSlotOf(it) ? '<span class=\"cat-chip\">' + escapeHtml(codisSlotOf(it).label) + '</span>' : econRarityBadge(rar.tone, rar.id, econCardName(it, rar), rar.order)) + '</div>'")
once("  if(it && it.fixed) return codisHabitSpecialCardHtml({ kind:'reward', scope:'habit', fixedId:it.id, item:it.name, coinValue:it.fixedCoin }, { plain:true, price:o.price, label:o.label });",
     "  { const sp = codisSlotOf(it); if(sp) return codisHabitSpecialCardHtml({ kind:'reward', scope:'habit', fixedId:sp.id, item:it.name, coinValue:sp.coin, stickerId:it.stickerId }, { plain:true, price:o.price, label:o.label }); }")
once("return codisSpecialCardHtml(k, { name:name, coin:coin, plain:o.plain, tone:", "return codisSpecialCardHtml(k, { name:name, coin:coin, plain:o.plain, stickerId:e.stickerId, tone:")
once("  const plain = !econStoreArtAr(it, rar);\n  const art = plain ?", "  if(codisSlotOf(it)) return '<div class=\"pk-tile\" role=\"listitem\" data-id=\"' + escapeHtml(it.id) + '\">' + econStoreFaceHtml(it, rar, { label:it.name }) + '</div>';\n  const plain = !econStoreArtAr(it, rar);\n  const art = plain ?")
once("econPackTileHtml({ id:it.uid, room:it.room, name:it.name, stickerId:it.stickerId }, {", "econPackTileHtml({ id:it.uid, room:it.room, name:it.name, stickerId:it.stickerId, rewardId:it.rewardId }, {")
once("[['الفئة', it.rarityName], ['المصدر', econSourceLabel(it)]", "[['الفئة', (codisSlotOf(it) || { label:it.rarityName }).label], ['المصدر', econSourceLabel(it)]")

# ---- tiles page: search + re-apply the filter after every list render
once('      </nav>\n      <div class="rpu-block is-reward" id="rp-reward-block">', '      </nav>\n      <button type="button" class="rpu-all-btn" id="rpu-all-btn" aria-pressed="false" onclick="setSettingsPeriod(\'all\')"><svg class="rpu-all-ico" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="6.5" height="6.5" rx="1.6"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.6"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.6"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.6"/></svg><span id="rpu-all-t">كل المكافآت</span><b id="rpu-all-n"></b><svg class="rpu-all-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg></button>\n      <div class="rpu-block is-reward" id="rp-reward-block">')
once('      <div hidden id="rpu-stash">', '      <section class="rpu-all" id="rpu-all" hidden aria-label="الكل">\n        <label class="rpu-find"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M16 16l4.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input type="search" id="rpu-q" placeholder="ابحث بالاسم…" aria-label="ابحث بالاسم" autocomplete="off" enterkeyhint="search" oninput="rpuFind()"><button type="button" class="rpu-find-x" aria-label="مسح البحث" onclick="rpuFindClear()"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"/></svg></button></label>\n        <div class="rpu-all-list" id="rpu-all-list"></div>\n      </section>\n      <div hidden id="rpu-stash">')
once("    list.innerHTML = items.length ? items.map(rowHtml).join('') : '<div class=\"eco-empty\">' + emptyFor(room) + '</div>';", "    list.innerHTML = rpuView === 'all' ? '' : (items.length ? items.map(rowHtml).join('') : '<div class=\"eco-empty\">' + emptyFor(room) + '</div>');   /* V35: «الكل» يعرضها مرة واحدة فقط */")
once("  settingsRoom = settingsDailyRoom; econRenderRewards(); econRenderPunish(); codisSfx('open', { ctx:'settings' });", "  settingsRoom = settingsDailyRoom; rpuView = 'daily'; econRenderRewards(); econRenderPunish(); codisSfx('open', { ctx:'settings' });")
once("  return n;\n}\nfunction econRenderRewards(){", "  try{ rpuAfterFill(kind, n); }catch(e){}\n  return n;\n}\nfunction econRenderRewards(){")
# ---- CODIS-ATMOS-V2: إعادة تضمين محرّك الزخارف من مصدره tools/atmos_engine.js (المضمَّن = نسخة حرفية منه)
eng = open(os.path.join(HERE, 'atmos_engine.js'), encoding='utf-8').read().rstrip()
i = s.index('/* ===== CODIS-STICKER-ATMOS — «جو الستيكر»'); assert s.count('/* ===== CODIS-STICKER-ATMOS — «جو الستيكر»') == 1
j = s.index('})();', s.index('return { html:html, get:get, extras:extras', i)) + len('})();')
s = s[:i] + eng + s[j:]
# ---- css
css = rd('v35.css'); assert '</style' not in css
i = s.index('<style id="codis-v34-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v35-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v35 ok', len(s))
