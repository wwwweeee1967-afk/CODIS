"""CODIS-V44 (3.31.0) — الصندوق المجاني: كرت مالي مستقل (1–10) + قسم «مكافآت الصندوق المجاني» + صندوق بالمتجر كل 24 ساعة.
  py -3 tools/patch_v44.py app/CODIS_FINAL.html app/CODIS_FINAL.html     (بعد patch_v43؛ ثم set_version.py 3.31.0) — أو: sh tools/rebuild_v44.sh"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-V44' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:140])
    s = s.replace(old, new)

# ---------- 1) الكرت المالي: بحث/تموضع/ترحيل (المصفوفة الـ25 وcodisFinClassify لم تُمس) ----------
once("function codisFinCardById(id){ if(id === 'learn') id = 'learn_bronze'; return codisFinCards().find(c=>c.id === id) || null; }",
     "function codisFinCardById(id){ if(id === 'free_box') return codisFreeCard();   /* CODIS-V44: كرت الصندوق المجاني خارج المصفوفة */\n  if(id === 'learn') id = 'learn_bronze'; return codisFinCards().find(c=>c.id === id) || null; }")
once("function codisFinPlacement(card){\n", "function codisFinPlacement(card){\n  if(card.free) return { room:'tasks', rarity:econCfg().rarities[0].id, variantOf:null, weight:0 };   /* CODIS-V44: علامة freebox تُخرجه من كل سحوبات الغرف */\n")
once("  if(item.fin) item.fin.card = card.id;\n}", "  if(card.free) item.freebox = true; else delete item.freebox;   /* CODIS-V44 */\n  if(item.fin) item.fin.card = card.id;\n}")
once("      if(!it || typeof it !== 'object') return;\n      it.fin = codisFinItemOk(it.fin)", "      if(!it || typeof it !== 'object') return;\n      if(it.freebox !== true) delete it.freebox;   /* CODIS-V44 */\n      it.fin = codisFinItemOk(it.fin)")
once("      if(!it.fin){ delete it.variantOf; return; }", "      if(!it.fin){ delete it.variantOf; delete it.freebox; return; }   /* CODIS-V44 */\n      if(it.fin.card === 'free_box'){ it.freebox = true; it.room = 'tasks'; it.weight = 0; delete it.variantOf; return; }   /* CODIS-V44: آمن وقت التحميل (لا يقرأ data) */\n      delete it.freebox;")
once("    const coin = codisFinCoinOfIqd(it.fin.iqd, rate); it.fin.coin = coin; res.items++;\n    const cur = cardOf(it.fin);",
     "    const coin = codisFinCoinOfIqd(it.fin.iqd, rate); it.fin.coin = coin; res.items++;\n    if(it.fin.card === 'free_box'){ if(codisFinInRange(codisFreeCard(), coin)) delete it.fin.oor; else { it.fin.oor = true; res.oor++; } return; }   /* CODIS-V44: لا تنتقل لبطاقة أخرى؛ خارج 1–10 تُستبعد من السحب فقط */\n    const cur = cardOf(it.fin);")
once("const cls = codisFinClassify(name, coin); if(!cls.ok) return { ok:false, reason:cls.reason", "const cls = codisFinClassifyAuto(name, coin); if(!cls.ok) return { ok:false, reason:cls.reason")
once("  if(kind === 'financial') item.fin.iqd = iqd; else item.fin.minutes = minutes;", "  if(card.free) item.freebox = true;   /* CODIS-V44 */\n  if(kind === 'financial') item.fin.iqd = iqd; else item.fin.minutes = minutes;")
# التطبيع: الحقل يبقى، حالة المطالبة، مصدر المخزون
once("stickerId:codisStickerIdOk(x.stickerId), fin:x.fin,", "stickerId:codisStickerIdOk(x.stickerId), fin:x.fin, freebox:x.freebox === true ? true : undefined,")
once("    periodLists:st.periodLists === true\n  };", "    periodLists:st.periodLists === true,\n    freeBox:codisFreeBoxNorm(st.freeBox)   /* CODIS-V44 */\n  };")
once("(x.source === 'store' || x.source === 'box') ? x.source : 'outcome'", "(x.source === 'store' || x.source === 'box' || x.source === 'free') ? x.source : 'outcome'")
once("(o.source === 'store' || o.source === 'box') ? o.source : 'outcome'", "(o.source === 'store' || o.source === 'box' || o.source === 'free') ? o.source : 'outcome'")
once("  if(it.source === 'box') return 'من بكج';", "  if(it.source === 'box') return 'من بكج';\n  if(it.source === 'free') return 'من الصندوق المجاني';   /* CODIS-V44 */")

# ---------- 2) الفصل عن النتائج اليومية والبكجات المدفوعة وقوائم الغرف ----------
once("x.enabled && x.room === room && !x.fixed); }", "x.enabled && x.room === room && !x.fixed && !x.freebox); }   /* CODIS-V44: مكافآت الصندوق المجاني خارج السحوبات */")
once("filter(x=>x.enabled && !x.fixed && !x.variantOf && econRarityById(x.rarity) && CodisEconomy.storePrice(x) > 0); }", "filter(x=>x.enabled && !x.fixed && !x.variantOf && !x.freebox && econRarityById(x.rarity) && CodisEconomy.storePrice(x) > 0); }   /* CODIS-V44: خارج البكجات المدفوعة */")
once("const all = kind === 'punish' ? data.settings.punishItems : data.settings.rewardItems, n = { daily:0", "const all = (kind === 'punish' ? data.settings.punishItems : data.settings.rewardItems).filter(x=>!(x && x.freebox)), n = { daily:0")
once("const isP = rpKind === 'punish', all = isP ? data.settings.punishItems : data.settings.rewardItems, row", "const isP = rpKind === 'punish', all = (isP ? data.settings.punishItems : data.settings.rewardItems).filter(x=>!(x && x.freebox)), row")
once("data.settings.rewardItems.filter(x=>x.room === settingsDailyRoom).length", "data.settings.rewardItems.filter(x=>x.room === settingsDailyRoom && !x.freebox).length")
once("set('home-reward-count', data.settings.rewardItems.length)", "set('home-reward-count', data.settings.rewardItems.filter(x=>!(x && x.freebox)).length)")
once("  try{ rpuAfterFill(kind, n); }catch(e){}", "  try{ if(kind !== 'punish') codisFreeMgmtRender(); }catch(e){}   /* CODIS-V44 */\n  try{ rpuAfterFill(kind, n); }catch(e){}")
once("  if(it.variantOf){ const _d = codisFixedById(it.variantOf);", "  if(it.freebox) return '<span class=\"rpt-tag cat-chip\">صندوق مجاني</span>';   /* CODIS-V44 */\n  if(it.variantOf){ const _d = codisFixedById(it.variantOf);")

# ---------- 3) الإضافة التلقائية: الكرت خيار صريح + وضع «إضافة للصندوق» ----------
once("function finAutoOpen(){", "function finAutoOpen(o){")
once("  finAuto = finAutoBlank();\n", "  finAuto = finAutoBlank(); if(o && o.free) finAuto.free = true;   /* CODIS-V44 */\n")
once("title:'إضافة مكافأة تلقائية',", "title:(o && o.free) ? 'إضافة مكافأة للصندوق المجاني' : 'إضافة مكافأة تلقائية',")
once("cls = codisFinClassify(name || '—', coin);", "cls = codisFinClassifyAuto(name || '—', coin);\n    if(a.free){ const _fc = cls.ok ? cls.candidates.filter(c=>c.card.free) : []; cls = _fc.length ? Object.assign({}, cls, { candidates:_fc, best:_fc[0], ambiguous:false, suggestions:_fc }) : { ok:false, reason:'freeRange', coin:coin }; }   /* CODIS-V44 */\n   ")
once("warn = cls.reason === 'low' ? 'القيمة أقل من الحد الأدنى (10 كوين' + (a.kind === 'financial' ? ' = ' + finFmt(10 * f.fx.rate) + ' د.ع بالسعر الحالي' : ' = 20 دقيقة') + ')' :",
     "warn = cls.reason === 'freeRange' ? 'قيمة مكافآت الصندوق المجاني من 1 إلى 10 كوينز' + (a.kind === 'financial' ? ' (' + finFmt(f.fx.rate) + '–' + finFmt(10 * f.fx.rate) + ' د.ع بالسعر الحالي)' : ' (من دقيقتين إلى 20 دقيقة)') : cls.reason === 'low' ? 'القيمة أقل من الحد الأدنى (كوين واحد' + (a.kind === 'financial' ? ' = ' + finFmt(f.fx.rate) + ' د.ع بالسعر الحالي' : ' = دقيقتان') + ')' :")
once("econRoomLabel(c.card.room) + ' · نطاق '", "(c.card.free ? 'الصندوق المجاني' : econRoomLabel(c.card.room)) + ' · نطاق '")
once("low:'القيمة أقل من 10 كوين'", "low:'القيمة أقل من كوين واحد'")

# ---------- 4) المنطق الجديد (بعد CodisInventory) ----------
once("  return { get, owned, closed, sellValue, grant, all };\n})();", "  return { get, owned, closed, sellValue, grant, all };\n})();\n\n" + rd('v44_core.js').rstrip() + "\n")

# ---------- 5) المتجر ----------
once("econStoreNavHtml() + (econClosedOpen ? econClosedPanelHtml() : '') + econBoxesHtml()", "econStoreNavHtml() + (econClosedOpen ? econClosedPanelHtml() : '') + codisFreeBoxStoreHtml() + econBoxesHtml()")
once("econOwnOpen, econBusyId, econStoreBusy,", "econOwnOpen, codisFreeBoxSig(), econBusyId, econStoreBusy,")
once("  codisFitLazy(box); codisWatchRewardCards(box);\n  econVaultSync(); econStoreNavBind(); econStoreNavSync();", "  codisFitLazy(box); codisWatchRewardCards(box); codisFreeBoxSchedule();   /* CODIS-V44 */\n  econVaultSync(); econStoreNavBind(); econStoreNavSync();")

# ---------- 6) قسم الإدارة (نهاية صفحة المكافآت اليومية) ----------
once('<div class="eco-list rpu-list" id="reward-list-monthly"></div>\n        </section>\n      </div>',
     '<div class="eco-list rpu-list" id="reward-list-monthly"></div>\n        </section>\n'
     '        <section class="rpu-sec rpu-free" id="rpu-r-free" data-period="daily" aria-labelledby="rpu-r-free-h">\n'
     '          <header class="rpu-head">\n'
     '            <span class="rpu-ico" aria-hidden="true"><svg data-icon="star" data-size="md"></svg></span>\n'
     '            <div class="rpu-ht"><h3 class="rpu-h" id="rpu-r-free-h">مكافآت الصندوق المجاني</h3><span class="rpu-sub" data-count></span></div>\n'
     '            <button type="button" class="rpu-fadd" onclick="codisFreeAdd()"><svg class="rpu-plus" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3v10M3 8h10" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg><span>إضافة مكافأة</span></button>\n'
     '          </header>\n'
     '          <div class="eco-list rpu-list" id="free-list"></div>\n'
     '        </section>\n      </div>')

# ---------- 8) بطاقة خاصة بالصندوق المجاني (بدل بطاقة اليومي) ----------
once("function econStoreFaceHtml(it, rar, o){\n  o = o || {};\n", "function econStoreFaceHtml(it, rar, o){\n  o = o || {};\n  if(codisIsFreeReward(it)){ let _c = 0; try{ _c = it.fin ? codisFinItemCoin(it) : (it.rewardId ? econEffCoin(data.settings.rewardItems.find(x=>x && x.id === it.rewardId) || {}, rar) : 0); }catch(e){} return codisFreeGiftCardHtml(it.name, (o.price !== undefined && o.price !== 0) ? o.price : _c, { plain:true, label:o.label, stickerId:it.stickerId }); }   /* CODIS-V44 */\n")
once("function codisRewardCardHtml(e, o){\n  o = o || {};\n", "function codisRewardCardHtml(e, o){\n  o = o || {};\n  if(codisIsFreeReward(e)) return codisFreeGiftCardHtml(e.item || e.name, (o.price !== undefined ? o.price : e.coinValue), { plain:o.plain, label:o.label, stickerId:e.stickerId });   /* CODIS-V44 */\n")
once("{ id:it.uid, room:it.room, name:it.name, stickerId:it.stickerId, rewardId:it.rewardId }", "{ id:it.uid, room:it.room, name:it.name, stickerId:it.stickerId, rewardId:it.rewardId, fin:it.fin, source:it.source }")
once("[['الفئة', econCardName(it, rar)], ['القسم', econRoomLabel(it.room)], ['السعر', econCoin(price), '', true]], { tone:rar.tone, kind:wk ? 'weekly' : mo ? 'monthly' : 'reward', sticker:it.stickerId });", "[['الفئة', it.freebox ? 'كرت الصندوق المجاني' : econCardName(it, rar)], ['القسم', it.freebox ? 'الصندوق المجاني' : econRoomLabel(it.room)], ['السعر', econCoin(price), '', true]], { tone:rar.tone, kind:wk ? 'weekly' : mo ? 'monthly' : 'reward', sticker:it.stickerId });")

# ---------- 7) CSS ----------
css = rd('v44.css'); assert '</style' not in css and '<!--' not in css
i = s.index('<style id="codis-v43-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v44-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('v44 applied')
