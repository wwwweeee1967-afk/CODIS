#!/usr/bin/env python3
"""CODIS-CLARITY (بعد patch_v27.py) — 3.15.0 — إعادة تنظيم واجهات (عرض فقط؛ لا تغيير بالمنطق/الاحتمالات/البيانات):
 1. طبقات النوافذ: أوراق .cd-ov (المنجزة/التسوية/الستيكر) كانت 9000 (= شاشة القفل، وتعلوها بترتيب DOM) فوق التأكيد (700)
    ⇒ الأوراق 680 (تحت التأكيد، فوق كل نوافذ التطبيق، وتحت القفل/الإقلاع/البوابة). Esc والرجوع يخصّان التأكيد أولاً.
 2. المكافآت/العقوبات: صفحة موحّدة لكل نوع بأقسام يومي/أسبوعي/شهري (نفس دوال الرسم والبيانات).
 3. غرفة التأديب: ترتيب الترويسة/المحدّد/نموذج الإضافة/بطاقة العادة.
 4. تفاصيل البكج: ترويسة + ملخص + توزيع + مجموعات قابلة للطي (الأرقام من CodisBoxes.effective كما هي).
 5. ظهر البطاقة: بلا قص صامت (التفاف + تمرير داخلي مضبوط داخل إطار 4:5).
 6. سجل الكوينز: ملخص + تجميع بالتاريخ.
 7. المباعة/المستخدمة: تبويبان مستقلان + «الأكثر استخداماً» من السجل الفعلي (المنتهية لا تُحسب).
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-CLARITY' in s: sys.exit('already patched (CODIS-CLARITY)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# ---------------------------------------------------------------- 1. طبقات النوافذ
rep(""".cd-ov{ position:fixed; inset:0; z-index:9000; display:flex;""",
    """/* CODIS-CLARITY: طبقة الأوراق 680 — فوق نوافذ التطبيق (200–650) وتحت التأكيد (700) والقفل/الإقلاع (9000+) */
.cd-ov{ position:fixed; inset:0; z-index:680; display:flex;""", 'cd-ov z')

rep("""function resolveCodisConfirm(v){""",
    """/* CODIS-CLARITY: Esc والتأكيد مفتوح يخصّه وحده — يسبق مستمعي الأوراق (document capture) فلا تنسكر الورقة التي تحته */
window.addEventListener('keydown', e=>{
  if(e.key !== 'Escape') return;
  const m = document.getElementById('codis-confirm-modal');
  if(m && CodisMotion.isOpen(m)){ e.stopPropagation(); e.preventDefault(); resolveCodisConfirm(false); }
}, true);
function resolveCodisConfirm(v){""", 'confirm esc')

rep("""  if(stickerSheet) return { act:closeStickerPicker, el:stickerSheet.root };
  if(graceSheet) return { act:closeGraceSheet, el:graceSheet.root };
  if(open('codis-confirm-modal')) return L('codis-confirm-modal', ()=>resolveCodisConfirm(false));""",
    """  if(open('codis-confirm-modal')) return L('codis-confirm-modal', ()=>resolveCodisConfirm(false));   /* CODIS-CLARITY: التأكيد يعلو الأوراق */
  if(stickerSheet) return { act:closeStickerPicker, el:stickerSheet.root };
  if(graceSheet) return { act:closeGraceSheet, el:graceSheet.root };
  if(CodisTaskFlow.doneEl()) return { act:CodisTaskFlow.closeDone, el:CodisTaskFlow.doneEl() };""", 'back order')

rep("""      body.querySelectorAll('.cd-restore').forEach(b=>{ b.onclick = async ()=>{ b.disabled = true; await restore(k, b.dataset.id); if(sheet === s0) paint(); }; });""",
    """      body.querySelectorAll('.cd-restore').forEach(b=>{ b.onclick = async ()=>{
        if(b.disabled) return; b.disabled = true; const id = b.dataset.id;
        await restore(k, id); if(sheet !== s0) return; paint();
        /* CODIS-CLARITY: الزر الذي رجع له التركيز انحذف بإعادة الرسم ⇒ التركيز يبقى داخل الورقة */
        if(!root.contains(document.activeElement)){ const nb = Array.prototype.find.call(body.querySelectorAll('.cd-restore'), x=>x.dataset.id === id) || root.querySelector('.cd-close'); try{ nb.focus({ preventScroll:true }); }catch(e){} }
      }; });""", 'restore focus')

rep("""  return { visible, answer, reattach, doneBar, restore, openDone, closeDone, _anim:anim, _busy:busy };""",
    """  return { visible, answer, reattach, doneBar, restore, openDone, closeDone, doneEl:()=>sheet ? sheet.root : null, _anim:anim, _busy:busy };""", 'taskflow export')

def cut(start, end, new, label):
    """يستبدل المقطع من start (شاملاً) إلى end (غير شامل) — كلاهما يجب أن يكون فريداً."""
    global s
    for m in (start, end):
        if s.count(m) != 1: sys.exit('cut anchor "%s" matched %d times' % (label, s.count(m)))
    a = s.index(start); b = s.index(end)
    if b <= a: sys.exit('cut "%s": end before start' % label)
    s = s[:a] + new + s[b:]

# ---------------------------------------------------------------- 2. المكافآت/العقوبات: صفحة موحّدة
PLUS = '<svg class="rpu-plus" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3v10M3 8h10" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>'

def rpu_section(kind, period):
    pk = 'r' if kind == 'reward' else 'p'
    noun = {'reward': 'المكافآت', 'punish': 'العقوبات'}[kind]
    adj = {'daily': 'اليومية', 'weekly': 'الأسبوعية', 'monthly': 'الشهرية'}[period]
    ico = {'daily': 'calendar', 'weekly': 'report', 'monthly': 'star'}[period]
    lst = ('%s-list' % kind) + ('' if period == 'daily' else '-' + period)
    add = {'reward': 'إضافة مكافأة', 'punish': 'إضافة عقوبة'}[kind]
    rooms = ''
    if period == 'daily':
        rooms = ('\n          <div class="arch-filter room-sel" role="group" aria-label="القسم اليومي">'
                 '<button type="button" class="arch-filter-btn is-on" data-room="tasks" aria-pressed="true" onclick="setSettingsRoom(\'tasks\')">غرفة العمليات<span class="arch-filter-n"></span></button>'
                 '<button type="button" class="arch-filter-btn" data-room="learn" aria-pressed="false" onclick="setSettingsRoom(\'learn\')">غرفة الأستاذ<span class="arch-filter-n"></span></button>'
                 '<button type="button" class="arch-filter-btn" data-room="habits" aria-pressed="false" onclick="setSettingsRoom(\'habits\')">الحدثية<span class="arch-filter-n"></span></button></div>')
    month = '\n          <div class="rpu-month" data-month></div>' if period == 'monthly' else ''
    return ('''
        <section class="rpu-sec" id="rpu-%(pk)s-%(period)s" data-period="%(period)s" aria-labelledby="rpu-%(pk)s-%(period)s-h">
          <header class="rpu-head">
            <span class="rpu-ico" aria-hidden="true"><svg data-icon="%(ico)s" data-size="md"></svg></span>
            <div class="rpu-ht"><h3 class="rpu-h" id="rpu-%(pk)s-%(period)s-h">%(noun)s %(adj)s</h3><span class="rpu-sub" data-count></span></div>
            <button type="button" class="rpu-add" aria-expanded="false" onclick="rpuAdd('%(kind)s','%(period)s')">%(plus)s<span>%(add)s</span></button>
          </header>%(month)s%(rooms)s
          <p class="rpu-note" data-note="%(period)s"></p>
          <div class="rpu-add-slot"></div>
          <div class="eco-list rpu-list" id="%(lst)s"></div>
        </section>''' % dict(pk=pk, period=period, ico=ico, noun=noun, adj=adj, kind=kind, plus=PLUS, add=add, month=month, rooms=rooms, lst=lst))

RPU_PAGE = '''<!-- ============ CODIS-CLARITY: صفحة موحّدة (مكافآت أو عقوبات) بأقسام يومية/أسبوعية/شهرية ============ -->
    <div id="settings-page-rewards" class="settings-page-section rpu" style="display:none;">
      <button type="button" class="settings-back-btn" onclick="rpGo('rp')"><svg class="ios-chevron" data-icon="back"></svg>المكافآت والعقوبات</button>
      <div class="settings-section-head">
        <div class="settings-section-title" id="rp-leaf-title">المكافآت</div>
      </div>
      <p class="rpu-lead" id="rp-lead"></p>
      <nav class="rpu-jump" aria-label="انتقل إلى الفترة">
        <button type="button" class="rpu-jump-btn" data-period="daily" onclick="setSettingsPeriod('daily')"><span>يومية</span><b data-jn="daily"></b></button>
        <button type="button" class="rpu-jump-btn" data-period="weekly" onclick="setSettingsPeriod('weekly')"><span>أسبوعية</span><b data-jn="weekly"></b></button>
        <button type="button" class="rpu-jump-btn" data-period="monthly" onclick="setSettingsPeriod('monthly')"><span>شهرية</span><b data-jn="monthly"></b></button>
      </nav>
      <div class="rpu-block is-reward" id="rp-reward-block">''' + ''.join(rpu_section('reward', p) for p in ('daily', 'weekly', 'monthly')) + '''
      </div>
      <div class="rpu-block is-punish" id="rp-punish-block" style="display:none;">
        <details class="rpu-costs">
          <summary><span class="rpu-costs-t">تكلفة تجاوز العقوبة</span><span class="rpu-costs-s">حسب الشدة والفترة (كوين)</span></summary>
          <p class="rpu-note">ثابتة حسب الشدة والقائمة: الأسبوعية ×7 والشهرية ×30 من اليومية (عدد أيام الفترة).</p>
          <div id="punish-costs"></div>
        </details>''' + ''.join(rpu_section('punish', p) for p in ('daily', 'weekly', 'monthly')) + '''
      </div>
      <div hidden id="rpu-stash"><div id="reward-add-box"></div><div id="punish-add-box"></div></div>
    </div>

    '''

cut('<div id="settings-page-rp-reward" class="settings-page-section"', '<!-- ACCOUNT-PAGES -->', RPU_PAGE, 'rp pages')

rep("""      <button type="button" class="settings-back-btn" onclick="showSettingsHome()"><svg class="ios-chevron" data-icon="back"></svg>الإعدادات</button>
      <div class="settings-section-head"><div class="settings-section-title">المكافآت والعقوبات</div></div>
      <div class="settings-grid"><div class="ios-list">
            <button type="button" class="ios-row" onclick="rpOpenHub('reward')">
              <span class="ios-row-icon tone-gold"><svg data-icon="gift" data-size="md"></svg></span>
              <span class="ios-row-title">المكافآت</span>""",
    """      <button type="button" class="settings-back-btn" onclick="showSettingsHome()"><svg class="ios-chevron" data-icon="back"></svg>الإعدادات</button>
      <div class="settings-section-head"><div class="settings-section-title">المكافآت والعقوبات</div></div>
      <div class="settings-grid"><div class="ios-list">
            <button type="button" class="ios-row" onclick="rpOpenHub('reward')">
              <span class="ios-row-icon tone-gold"><svg data-icon="gift" data-size="md"></svg></span>
              <span class="ios-row-title">المكافآت<span class="ios-row-sub">يومية · أسبوعية · شهرية</span></span>""", 'hub reward row')
rep("""            <button type="button" class="ios-row" onclick="rpOpenHub('punish')">
              <span class="ios-row-icon tone-danger"><svg data-icon="warning" data-size="md"></svg></span>
              <span class="ios-row-title">العقوبات</span>""",
    """            <button type="button" class="ios-row" onclick="rpOpenHub('punish')">
              <span class="ios-row-icon tone-danger"><svg data-icon="warning" data-size="md"></svg></span>
              <span class="ios-row-title">العقوبات<span class="ios-row-sub">يومية · أسبوعية · شهرية</span></span>""", 'hub punish row')

rep("""  if(cat === 'punishments'){ rpKind = 'punish'; cat = 'rp-punish'; }
  if(cat === 'rewards'){ cat = 'rp-reward'; rpKind = 'reward'; }""",
    """  if(cat === 'punishments' || cat === 'rewards'){ rpOpenHub(cat === 'punishments' ? 'punish' : 'reward'); return; }   /* CODIS-CLARITY: صفحة موحّدة */""", 'category map')

# --- العرض: نفس البيانات (room) ونفس دوال الإضافة/التعديل/الحذف؛ فقط ثلاث قوائم بصفحة واحدة
cut("""function econRenderRewards(){""", """
/* ---- العقوبات + تكلفة التجاوز ---- */""", r"""/* CODIS-CLARITY: صف مكافأة (نفس الحقول والأزرار) */
function econRewardRowHtml(it){
  const rar = econRarityById(it.rarity) || econCfg().rarities[0], coin = econEffCoin(it, rar), price = econEffStore(it, rar), ed = econEditing === it.id;
  return '<div class="eco-item' + (it.enabled ? '' : ' is-off') + (ed ? ' is-editing' : '') + '"><div class="eco-item-main"><div class="eco-item-top">' + (it.room === 'learn' ? '' : econRarityBadge(rar.tone, rar.id, rar.name, rar.order)) + codisStickerThumbHtml(it.stickerId) + '<span class="eco-item-name">' + escapeHtml(it.name) + '</span>' + codisDurBadgeHtml(it.name) + '</div>' +
    '<div class="eco-item-meta"><span>استبدال <b>' + econFmt(coin) + '</b></span><span>متجر <b>' + econFmt(price) + '</b></span><span>بيع <b>' + econFmt(econSellValue(coin)) + '</b></span>' + (it.enabled ? '' : '<span class="eco-off-tag">معطّلة</span>') + '</div></div>' +
    '<div class="eco-item-acts"><button type="button" class="chip-act" onclick="econToggleReward(\'' + it.id + '\')" aria-pressed="' + (it.enabled ? 'true' : 'false') + '">' + (it.enabled ? 'تعطيل' : 'تفعيل') + '</button>' +
    '<button type="button" class="chip-act" onclick="econEdit(\'' + it.id + '\')" aria-expanded="' + (ed ? 'true' : 'false') + '">' + (ed ? 'إغلاق' : 'تعديل') + '</button>' +
    '<button type="button" class="chip-del" aria-label="حذف «' + escapeHtml(it.name) + '»" title="حذف" onclick="econDeleteReward(\'' + it.id + '\')">' + ICONS.trash + '</button></div>' +
    (ed ? '<div class="eco-item-edit">' + econRewardEditor('eco-edit-r', it) + '<button type="button" class="btn btn-primary eco-full" onclick="econSaveReward(\'' + it.id + '\')">حفظ التعديل</button></div>' : '') + '</div>';
}
/* CODIS-CLARITY: كل قائمة تُرسم بقسمها: اليومية لغرفة settingsDailyRoom، والأسبوعية والشهرية دائماً — نفس التصفية بـ room */
function rpuFill(kind, rowHtml, sortFn, emptyFor){
  const all = kind === 'punish' ? data.settings.punishItems : data.settings.rewardItems, n = { daily:0, weekly:0, monthly:0 }, perRoom = {};
  all.forEach(x=>{ const p = econScopeOfRoom(x.room); n[p] = (n[p] || 0) + 1; perRoom[x.room] = (perRoom[x.room] || 0) + 1; });
  [['daily', settingsDailyRoom, ''], ['weekly', 'weekly', '-weekly'], ['monthly', 'monthly', '-monthly']].forEach(([p, room, suf])=>{
    const list = document.getElementById(kind + '-list' + suf); if(!list) return;
    const items = all.filter(x=>x.room === room).sort(sortFn);
    list.innerHTML = items.length ? items.map(rowHtml).join('') : '<div class="eco-empty">' + emptyFor(room) + '</div>';
    const sec = list.closest('.rpu-sec'); if(!sec) return;
    const on = items.filter(x=>x.enabled).length, c = sec.querySelector('[data-count]');
    if(c) c.textContent = items.length ? ('العدد ' + items.length + (p === 'daily' ? ' · ' + econRoomLabel(room) : '') + (on < items.length ? ' · ' + (items.length - on) + ' معطّلة' : '')) : (p === 'daily' ? econRoomLabel(room) : 'فارغة');
    if(p === 'daily') sec.querySelectorAll('.room-sel .arch-filter-btn').forEach(b=>{ const k = b.querySelector('.arch-filter-n'); if(k) k.textContent = perRoom[b.dataset.room] || 0; });
  });
  const blk = document.getElementById('rp-' + kind + '-block');
  if(blk && blk.style.display !== 'none') document.querySelectorAll('#settings-page-rewards [data-jn]').forEach(b=>{ b.textContent = n[b.dataset.jn] || 0; });
  return n;
}
function econRenderRewards(){
  const list = document.getElementById('reward-list'); if(!list) return;
  if(econRoomIds().indexOf(settingsRoom) !== -1) settingsDailyRoom = settingsRoom;
  const cnt = document.getElementById('reward-count'); if(cnt) cnt.innerText = data.settings.rewardItems.filter(x=>x.room === settingsDailyRoom).length;
  econSyncPeriodUI();
  const addBox = document.getElementById('reward-add-box');
  if(addBox && !addBox.dataset.ready){ addBox.innerHTML = econRewardEditor('eco-new-r', null) + '<button type="button" class="btn btn-primary eco-full" onclick="econAddReward()">إضافة المكافأة</button>'; addBox.dataset.ready = '1'; }
  const rank = r=>{ const x = econRarityById(r); return x ? x.order : 99; };
  rpuFill('reward', econRewardRowHtml, (a,b)=>rank(a.rarity) - rank(b.rarity) || a.name.localeCompare(b.name, 'ar'),
    room=>room === 'weekly' ? 'ماكو مكافآت أسبوعية — أضف أول وحدة' : room === 'monthly' ? 'ماكو مكافآت شهرية — أضف أول وحدة' : 'ماكو مكافآت بـ«' + econRoomLabel(room) + '» — أضف أول مكافأة');
}
""", 'render rewards')

rep("""function econAddReward(){
  const v = econReadReward('eco-new-r'); if(!v) return;
  const now = econNowIso(); data.settings.rewardItems.push(Object.assign({ id:econUid('reward'), createdAt:now, updatedAt:now }, v));
  econNormalizeItems(data.settings); settingsRoom = v.room;""",
    """function econAddReward(){
  const v = econReadReward('eco-new-r'); if(!v) return;
  const now = econNowIso(); data.settings.rewardItems.push(Object.assign({ id:econUid('reward'), createdAt:now, updatedAt:now }, v));
  econNormalizeItems(data.settings); settingsRoom = v.room; rpuAddDone('reward');""", 'add reward done')
rep("""  econNormalizeItems(data.settings); settingsRoom = v.room; econSave('انضافت العقوبة'); econRenderAll();""",
    """  econNormalizeItems(data.settings); settingsRoom = v.room; rpuAddDone('punish'); econSave('انضافت العقوبة'); econRenderAll();""", 'add punish done')

cut("""function econRenderPunish(){""", """/* دوال الغرف القديمة بقيت بنفس الاسم: تبديل غرفة القوائم */""", r"""function econPunishRowHtml(it){
  const ed = econEditing === it.id;
  return '<div class="eco-item' + (it.enabled ? '' : ' is-off') + (ed ? ' is-editing' : '') + '"><div class="eco-item-main"><div class="eco-item-top"><span class="sev-badge sev-' + it.severity + '">' + econSevLabel(it.severity) + '</span><span class="eco-item-name">' + escapeHtml(it.name) + '</span></div>' +
    '<div class="eco-item-meta"><span>تجاوز <b>' + econFmt(econPenaltyCost(it)) + '</b> كوين' + (it.coinBypassCost === null ? ' (حسب الشدة)' : '') + '</span>' + (it.enabled ? '' : '<span class="eco-off-tag">معطّلة</span>') + '</div></div>' +
    '<div class="eco-item-acts"><button type="button" class="chip-act" onclick="econTogglePunish(\'' + it.id + '\')" aria-pressed="' + (it.enabled ? 'true' : 'false') + '">' + (it.enabled ? 'تعطيل' : 'تفعيل') + '</button>' +
    '<button type="button" class="chip-act" onclick="econEdit(\'' + it.id + '\')" aria-expanded="' + (ed ? 'true' : 'false') + '">' + (ed ? 'إغلاق' : 'تعديل') + '</button>' +
    '<button type="button" class="chip-del" aria-label="حذف «' + escapeHtml(it.name) + '»" title="حذف" onclick="econDeletePunish(\'' + it.id + '\')">' + ICONS.trash + '</button></div>' +
    (ed ? '<div class="eco-item-edit">' + econPunishEditor('eco-edit-p', it) + '<button type="button" class="btn btn-primary eco-full" onclick="econSavePunish(\'' + it.id + '\')">حفظ التعديل</button></div>' : '') + '</div>';
}
function econRenderPunish(){
  const list = document.getElementById('punish-list'); if(!list) return;
  if(econRoomIds().indexOf(settingsRoom) !== -1) settingsDailyRoom = settingsRoom;
  const cnt = document.getElementById('punish-count'); if(cnt) cnt.innerText = data.settings.punishItems.filter(x=>x.room === settingsDailyRoom).length;
  econSyncPeriodUI();
  const costs = document.getElementById('punish-costs');
  if(costs) costs.innerHTML = econPriceTable(econSeverities().map(v=>[v, econSevLabel(v)]), (v, k)=>econBypassFor(v, k));
  const addBox = document.getElementById('punish-add-box');
  if(addBox && !addBox.dataset.ready){ addBox.innerHTML = econPunishEditor('eco-new-p', null) + '<button type="button" class="btn btn-primary eco-full" onclick="econAddPunish()">إضافة العقوبة</button>'; addBox.dataset.ready = '1'; }
  rpuFill('punish', econPunishRowHtml, (a,b)=>econSeverities().indexOf(a.severity) - econSeverities().indexOf(b.severity) || a.name.localeCompare(b.name, 'ar'),
    room=>room === 'weekly' ? 'ماكو عقوبات أسبوعية' : room === 'monthly' ? 'ماكو عقوبات شهرية' : 'ماكو عقوبات بـ«' + econRoomLabel(room) + '»');
}
""", 'render punish')

cut("""function setSettingsRoom(room){""", """function econRpNote(){""", r"""function setSettingsRoom(room){ if(econRoomIds().indexOf(room) === -1) return; settingsRoom = room; settingsDailyRoom = room; econEditing = null; codisSfx('press', { ctx:'tab' }); rpuSyncAddRoom(); econRenderRewards(); econRenderPunish(); }
/* CODIS-CLARITY: الفترات كلها بنفس الصفحة ⇒ اختيار فترة = انتقال لقسمها (والقائمة الافتراضية للإضافة تتبعها) */
function setSettingsPeriod(p){
  if(['daily','weekly','monthly'].indexOf(p) === -1) return; settingsRoom = p === 'daily' ? settingsDailyRoom : p; econEditing = null; codisSfx('press', { ctx:'tab' }); econRenderRewards(); econRenderPunish();
  const sec = document.getElementById('rpu-' + (rpKind === 'punish' ? 'p' : 'r') + '-' + p);
  if(sec && sec.offsetParent){ const rm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches; try{ sec.scrollIntoView({ block:'start', behavior:rm ? 'auto' : 'smooth' }); }catch(e){ sec.scrollIntoView(); } }
}
let rpKind = 'reward';
const rpuAdding = { reward:null, punish:null };   /* حالة واجهة فقط: أي قسم فاتح نموذج الإضافة */
function rpGo(cat){ codisSfx('close', { ctx:'settings' }); CodisMotion.settingsGo(document.getElementById('settings-page-' + cat), -1); }
function rpuSlotOf(kind, period){ const sec = document.getElementById('rpu-' + (kind === 'punish' ? 'p' : 'r') + '-' + period); return sec ? sec.querySelector('.rpu-add-slot') : null; }
/* نموذج الإضافة نفسه (eco-new-r / eco-new-p) يُنقل لقسم الفترة — عنصر واحد فما يضيع المكتوب، والقائمة تُضبط على قسمه */
function rpuAdd(kind, period, force){
  kind = kind === 'punish' ? 'punish' : 'reward';
  const box = document.getElementById(kind + '-add-box'), stash = document.getElementById('rpu-stash'); if(!box || !stash) return;
  const wasOpen = rpuAdding[kind] === period;
  if(rpuAdding[kind]){ const old = rpuSlotOf(kind, rpuAdding[kind]); stash.appendChild(box); if(old) old.innerHTML = ''; rpuAdding[kind] = null; }
  if(wasOpen && !force){ codisSfx('close', { ctx:'editor' }); rpuSyncAddButtons(); return; }
  const slot = rpuSlotOf(kind, period); if(!slot) return;
  if(!box.dataset.ready){ if(kind === 'punish') econRenderPunish(); else econRenderRewards(); }
  slot.innerHTML = '<p class="rpu-add-t">' + (kind === 'punish' ? 'عقوبة جديدة' : 'مكافأة جديدة') + '</p>'; slot.appendChild(box);
  rpuAdding[kind] = period; rpuSyncAddRoom(); rpuSyncAddButtons(); codisSfx('open', { ctx:'editor' });
  const nm = document.getElementById(kind === 'punish' ? 'eco-new-p-name' : 'eco-new-r-name');
  if(nm && !force){ try{ nm.focus({ preventScroll:true }); slot.scrollIntoView({ block:'nearest' }); }catch(e){} }
}
function rpuSyncAddRoom(){
  ['reward', 'punish'].forEach(kind=>{
    const p = rpuAdding[kind]; if(!p) return;
    const pre = kind === 'punish' ? 'eco-new-p' : 'eco-new-r', sel = document.getElementById(pre + '-room'); if(!sel) return;
    sel.value = p === 'daily' ? settingsDailyRoom : p;
    if(kind === 'punish') econPunishChanged(pre); else econRewardRarityChanged(pre);
  });
}
function rpuSyncAddButtons(){
  document.querySelectorAll('#settings-page-rewards .rpu-sec').forEach(sec=>{
    const kind = sec.id.indexOf('rpu-p-') === 0 ? 'punish' : 'reward', on = rpuAdding[kind] === sec.dataset.period, b = sec.querySelector('.rpu-add'); if(!b) return;
    b.setAttribute('aria-expanded', on ? 'true' : 'false'); b.classList.toggle('is-open', on);
    const t = b.querySelector('span'); if(t) t.textContent = on ? 'إغلاق' : (kind === 'punish' ? 'إضافة عقوبة' : 'إضافة مكافأة');
  });
}
/* بعد الإضافة الناجحة: النموذج يُفرَّغ (يُبنى من جديد بأول رسم) ويرجع للمخزن */
function rpuAddDone(kind){
  const box = document.getElementById(kind + '-add-box'), stash = document.getElementById('rpu-stash');
  if(rpuAdding[kind]){ const slot = rpuSlotOf(kind, rpuAdding[kind]); if(box && stash) stash.appendChild(box); if(slot) slot.innerHTML = ''; rpuAdding[kind] = null; }
  if(box){ box.innerHTML = ''; delete box.dataset.ready; delete box.dataset.touchedRoom; }
  rpuSyncAddButtons();
}
function rpOpenHub(kind){
  rpKind = kind === 'punish' ? 'punish' : 'reward'; econEditing = null;
  ['reward', 'punish'].forEach(k=>{ if(rpuAdding[k]) rpuAdd(k, rpuAdding[k]); });
  settingsRoom = settingsDailyRoom; econRenderRewards(); econRenderPunish(); codisSfx('open', { ctx:'settings' });
  CodisMotion.settingsGo(document.getElementById('settings-page-rewards'), 1);
}
/* توافق: الفتح بفترة محددة = نفس الصفحة الموحّدة ثم الانتقال لقسمها */
function rpOpenLeaf(period){ rpOpenHub(rpKind); if(period && period !== 'daily') setTimeout(()=>setSettingsPeriod(period), 380); }
""", 'room/period/nav')

rep("""function econRpNote(){
  if(settingsRoom === 'weekly')""", """function econRpNote(room){ return econRpNoteFor(room || settingsRoom); }   /* CODIS-CLARITY: ملاحظة لقسم بعينه */
function econRpNoteFor(settingsRoom){
  if(settingsRoom === 'weekly')""", 'rp note param')

rep("""function econMonthCardHtml(){
  const cur = econThisMonthKey(), L = data.outcomeLedger, done = L['monthly|' + cur], s = CodisEconomy.monthStats(cur), wk = s ? s.weeks : 0;
  let h = '<div class="eco-sec-title">شهر ' + escapeHtml(cur) + '</div>';
  if(done){""", """function econMonthCardHtml(){
  const cur = econThisMonthKey(), L = data.outcomeLedger, done = L['monthly|' + cur], s = CodisEconomy.monthStats(cur), wk = s ? s.weeks : 0;
  let h = '<div class="rpu-mh"><span class="eco-sec-title">شهر ' + escapeHtml(cur) + '</span><span class="rpu-ms' + (done ? ' is-done' : '') + '">' + (done ? 'محسوم' : 'جارٍ') + '</span></div>';
  if(!done){ const w4 = Math.min(wk, 4); h += '<div class="rpu-mbar" role="progressbar" aria-label="الأسابيع المكتملة" aria-valuemin="0" aria-valuemax="4" aria-valuenow="' + w4 + '"><i style="width:' + (w4 * 25) + '%"></i></div>'; }
  if(done){""", 'month card')

rep("""function econSyncPeriodUI(){
  const mc = document.getElementById('rp-month-card');
  if(mc){ const on = settingsRoom === 'monthly'; mc.style.display = on ? '' : 'none'; if(on) mc.innerHTML = econMonthCardHtml(); }
  const rb = document.getElementById('rp-reward-block'), pb = document.getElementById('rp-punish-block'), nt = document.getElementById('rp-note');
  if(rb) rb.style.display = rpKind === 'reward' ? '' : 'none';
  if(pb) pb.style.display = rpKind === 'punish' ? '' : 'none';
  const lt = document.getElementById('rp-leaf-title');
  if(lt) lt.textContent = (rpKind === 'punish' ? 'العقوبات ' : 'المكافآت ') + (econRoomIds().indexOf(settingsRoom) !== -1 ? 'اليومية' : settingsRoom === 'weekly' ? 'الأسبوعية' : 'الشهرية');
  if(nt) nt.textContent = econRpNote();
  const daily = econRoomIds().indexOf(settingsRoom) !== -1; if(daily) settingsDailyRoom = settingsRoom;
  const cur = daily ? 'daily' : settingsRoom;
  document.querySelectorAll('.period-sel .arch-filter-btn').forEach(b=>{ const on = b.dataset.period === cur; b.classList.toggle('is-on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
  document.querySelectorAll('.room-sel').forEach(e=>{ e.style.display = daily ? '' : 'none'; });
}""", """function econSyncPeriodUI(){
  const pg = document.getElementById('settings-page-rewards'); if(!pg) return;
  const daily = econRoomIds().indexOf(settingsRoom) !== -1; if(daily) settingsDailyRoom = settingsRoom;
  const rb = document.getElementById('rp-reward-block'), pb = document.getElementById('rp-punish-block');
  if(rb) rb.style.display = rpKind === 'reward' ? '' : 'none';
  if(pb) pb.style.display = rpKind === 'punish' ? '' : 'none';
  const lt = document.getElementById('rp-leaf-title'); if(lt) lt.textContent = rpKind === 'punish' ? 'العقوبات' : 'المكافآت';
  const ld = document.getElementById('rp-lead');
  if(ld) ld.textContent = rpKind === 'punish' ? 'كل قوائم العقوبات بصفحة وحدة. كل قسم يعرض عقوباته وزر إضافة خاص بفترته.' : 'كل قوائم المكافآت بصفحة وحدة. كل قسم يعرض مكافآته وزر إضافة خاص بفترته.';
  const mh = econMonthCardHtml(); pg.querySelectorAll('[data-month]').forEach(mc=>{ mc.innerHTML = mh; });
  pg.querySelectorAll('[data-note]').forEach(n=>{ n.textContent = econRpNote(n.dataset.note === 'daily' ? settingsDailyRoom : n.dataset.note); });
  pg.querySelectorAll('.room-sel .arch-filter-btn').forEach(b=>{ const on = b.dataset.room === settingsDailyRoom; b.classList.toggle('is-on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
  rpuSyncAddButtons();
}""", 'sync period ui')

RPU_CSS = r"""
/* ===================== CODIS-CLARITY · صفحة المكافآت/العقوبات الموحّدة =====================
   ترتيب ثابت: عنوان + سطر تعريف ← قفزات الفترات ← قسم لكل فترة (ترويسة بأيقونة/عدد/زر إضافة · محدد الغرفة لليومية · حالة الشهر للشهرية · القائمة).
   القسم لوح واحد؛ الصفوف داخله تفصلها خطوط شعرية بدل بطاقات متداخلة. */
.ios-row-sub{ display:block; margin-top:2px; font-size:var(--fs-caption); font-weight:500; color:var(--text-3); }
.rpu-lead{ margin:-6px 0 var(--sp-lg); font-size:var(--fs-sub); line-height:1.75; color:var(--text-2); }
.rpu-jump{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:var(--sp-sm); margin-bottom:var(--sp-xl); }
.rpu-jump-btn{ min-height:44px; display:flex; align-items:center; justify-content:center; gap:6px; padding:0 8px; border-radius:var(--r-full); border:1px solid var(--glass-border); background:var(--glass); color:var(--text); font:inherit; font-size:var(--fs-sub); font-weight:600; cursor:pointer; transition:transform var(--dur-fast) var(--ease), background var(--dur-fast) var(--ease); }
.rpu-jump-btn b{ min-width:20px; padding:0 6px; border-radius:var(--r-full); background:rgb(var(--hi-rgb) / .07); color:var(--text-2); font-size:var(--fs-caption); font-weight:700; font-variant-numeric:tabular-nums; line-height:20px; }
.rpu-jump-btn:active{ transform:scale(var(--press)); background:var(--glass-strong); }
.rpu-jump-btn:focus-visible, .rpu-add:focus-visible, .rpu-costs > summary:focus-visible{ outline:2px solid var(--aqua); outline-offset:2px; }
.rpu-block{ display:flex; flex-direction:column; gap:var(--sp-xl); }
.rpu-sec{ scroll-margin-top:calc(var(--pad-top) + 4px); display:flex; flex-direction:column; gap:var(--sp-md); padding:var(--sp-lg); border-radius:var(--r-lg); background:var(--mat-panel-fill); border:1px solid var(--mat-panel-edge); box-shadow:var(--mat-panel-shadow); }
.rpu-head{ display:flex; align-items:center; gap:var(--sp-md); }
.rpu-ico{ flex:none; width:38px; height:38px; display:grid; place-items:center; border-radius:var(--r-sm); background:var(--gold-a12); color:var(--gold); }
.rpu-block.is-punish .rpu-ico{ background:var(--danger-a12); color:var(--danger-ink); }
.rpu-ico svg{ width:20px; height:20px; }
.rpu-ht{ flex:1; min-width:0; }
.rpu-h{ margin:0; font-size:17px; font-weight:700; line-height:1.4; }
.rpu-sub{ display:block; margin-top:1px; font-size:var(--fs-caption); color:var(--text-3); font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
.rpu-add{ flex:none; min-height:40px; display:inline-flex; align-items:center; gap:6px; padding:0 14px; border-radius:var(--r-full); border:1px solid var(--aqua-a40); background:var(--aqua-a08); color:var(--aqua); font:inherit; font-size:var(--fs-sub); font-weight:700; cursor:pointer; transition:transform var(--dur-fast) var(--ease); }
.rpu-add:active{ transform:scale(var(--press)); }
.rpu-add.is-open{ border-color:var(--glass-border-strong); background:transparent; color:var(--text-2); }
.rpu-add.is-open .rpu-plus{ transform:rotate(45deg); }
.rpu-plus{ width:14px; height:14px; transition:transform var(--dur-fast) var(--ease); }
.rpu-sec .room-sel{ margin:0; }
.rpu-sec .room-sel .arch-filter-btn{ min-height:44px; padding:0 6px; line-height:1.3; }
.rpu-sec .room-sel .arch-filter-n:empty{ display:none; }
.rpu-note{ margin:0; font-size:var(--fs-sub); line-height:1.75; color:var(--text-3); }
.rpu-add-slot:empty{ display:none; }
.rpu-add-slot{ padding:var(--sp-md); border-radius:var(--r-md); background:var(--mat-well); border:1px solid var(--aqua-a24); }
.rpu-add-t{ margin:0 0 var(--sp-sm); font-size:var(--fs-callout); font-weight:700; color:var(--aqua); }
.rpu-month{ padding:var(--sp-md); border-radius:var(--r-md); background:var(--mat-well); border:1px solid var(--glass-border); }
.rpu-month .eco-note{ margin-bottom:var(--sp-md); }
.rpu-mh{ display:flex; align-items:center; justify-content:space-between; gap:var(--sp-sm); margin-bottom:var(--sp-sm); }
.rpu-mh .eco-sec-title{ margin:0; font-size:var(--fs-callout); }
.rpu-ms{ flex:none; padding:2px 10px; border-radius:var(--r-full); background:var(--aqua-a08); color:var(--aqua); font-size:var(--fs-caption); font-weight:600; }
.rpu-ms.is-done{ background:var(--success-a12); color:var(--success-ink); }
.rpu-mbar{ height:6px; margin:2px 0 var(--sp-md); border-radius:var(--r-full); background:rgb(var(--hi-rgb) / .08); overflow:hidden; }
.rpu-mbar i{ display:block; height:100%; border-radius:inherit; background:var(--aqua); }
.rpu-list{ gap:0; }
.rpu-list .eco-item{ padding:var(--sp-md) 0; background:none; border:0; border-radius:0; border-top:1px solid var(--glass-border); }
.rpu-list .eco-item:first-child{ border-top:0; padding-top:4px; }
.rpu-list .eco-item.is-editing{ padding-inline:var(--sp-md); margin-inline:calc(-1 * var(--sp-md)); border-radius:var(--r-md); background:var(--mat-well); border-top-color:transparent; }
.rpu-list .eco-item-meta{ gap:4px 14px; margin-top:4px; }
.rpu-list .eco-item-meta b{ color:var(--text); font-weight:600; font-variant-numeric:tabular-nums; }
.rpu-list .eco-item-acts{ gap:2px; margin-inline-start:-10px; }
.eco-off-tag{ padding:0 8px; border-radius:var(--r-full); background:rgb(var(--hi-rgb) / .07); color:var(--text-2); }
.rpu-list .eco-empty{ padding:var(--sp-lg) var(--sp-sm); border-radius:var(--r-md); border:1px dashed var(--glass-border-strong); font-size:var(--fs-sub); color:var(--text-3); }
.rpu-costs{ padding:0 var(--sp-lg); border-radius:var(--r-lg); background:var(--mat-panel-fill); border:1px solid var(--mat-panel-edge); }
.rpu-costs > summary{ list-style:none; cursor:pointer; min-height:52px; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:2px 10px; padding:10px 0; }
.rpu-costs > summary::-webkit-details-marker{ display:none; }
.rpu-costs > summary::after{ content:''; width:8px; height:8px; margin-inline-start:auto; border-inline-end:2px solid var(--text-3); border-bottom:2px solid var(--text-3); transform:rotate(45deg); transition:transform var(--dur-fast) var(--ease); }
.rpu-costs[open] > summary::after{ transform:rotate(225deg); }
.rpu-costs-t{ font-weight:700; font-size:var(--fs-callout); }
.rpu-costs-s{ font-size:var(--fs-caption); color:var(--text-3); }
.rpu-costs[open]{ padding-bottom:var(--sp-lg); }
.rpu-costs .rpu-note{ margin-bottom:var(--sp-md); }
@media (prefers-reduced-motion:reduce){ .rpu-jump-btn, .rpu-add, .rpu-plus, .rpu-costs > summary::after{ transition:none; } }
"""

CSS = [RPU_CSS]

# ---------------------------------------------------------------- 3. غرفة التأديب (عرض فقط: نفس المعالجات والبيانات وقواعد الأنواع)
rep("""      <button type="button" class="disc-mode is-active" id="habit-tab-build" aria-pressed="true" onclick="switchHabitTab('build')"><span>أكتسبها</span><span class="disc-mode-n" id="habit-count-build" aria-hidden="true">0</span></button>
      <button type="button" class="disc-mode" id="habit-tab-quit" aria-pressed="false" onclick="switchHabitTab('quit')"><span>أتخلص منها</span><span class="disc-mode-n" id="habit-count-quit" aria-hidden="true">0</span></button>
    </div>""",
    """      <button type="button" class="disc-mode is-active" id="habit-tab-build" aria-pressed="true" onclick="switchHabitTab('build')"><span class="disc-mode-t"><span>أكتسبها</span><small>عادات تبنيها</small></span><span class="disc-mode-n" id="habit-count-build" aria-hidden="true">0</span></button>
      <button type="button" class="disc-mode" id="habit-tab-quit" aria-pressed="false" onclick="switchHabitTab('quit')"><span class="disc-mode-t"><span>أتخلص منها</span><small>عادات تتركها</small></span><span class="disc-mode-n" id="habit-count-quit" aria-hidden="true">0</span></button>
    </div>""", 'disc modes')
rep("""    <div class="disc-toolbar">
      <button type="button" class="disc-add-trigger\"""",
    """    <div class="disc-toolbar">
      <p class="disc-mode-desc" id="habit-mode-desc" aria-live="polite">يومية أو أسبوعية — تسجّلها كل ما تنجزها.</p>
      <button type="button" class="disc-add-trigger\"""", 'disc toolbar desc')
rep("""          <input type="text" id="new-habit-text" aria-label="اسم العادة" placeholder="اسم العادة" maxlength="120" onkeydown="if(event.key==='Enter') addHabit()">""",
    """          <div><label class="field-label" for="new-habit-text">اسم العادة</label>
          <input type="text" id="new-habit-text" aria-label="اسم العادة" placeholder="مثلاً: قراءة عشر صفحات" maxlength="120" onkeydown="if(event.key==='Enter') addHabit()"></div>""", 'add name label')
rep("""  if(page) page.dataset.mode = tab;
  if(prev !== tab){""", """  if(page) page.dataset.mode = tab;
  { const d = document.getElementById('habit-mode-desc'); if(d) d.textContent = tab === 'quit' ? 'امتناع يومي أو مواقف حدثية — تسجّل نجاحك أو وقوعك.' : 'يومية أو أسبوعية — تسجّلها كل ما تنجزها.'; }   /* CODIS-CLARITY */
  if(prev !== tab){""", 'mode desc sync')

rep("""  row.className = 'habit-card imp-'+imp+' '+cls+(h.id===codisJustChangedId ? ' just-changed' : '');""",
    """  row.className = 'habit-card hbx imp-'+imp+' '+cls+(h.id===codisJustChangedId ? ' just-changed' : '');""", 'hbx class')
rep("""      action = '<button type="button" class="stat-btn stat-done '+(done?'active':'')+'" aria-pressed="'+done+'" aria-label="سويتها اليوم" title="سويتها اليوم"><span class="stat-ico">'+ICONS.check+'</span></button>';""",
    """      action = '<button type="button" class="stat-btn stat-done '+(done?'active':'')+'" aria-pressed="'+done+'" aria-label="سويتها اليوم" title="سويتها اليوم"><span class="stat-ico">'+ICONS.check+'</span><span class="hbx-lab">'+(done ? 'منجزة اليوم' : 'سويتها اليوم')+'</span></button>';""", 'E action label')
rep("""' aria-label="'+(todayDone?'سُجّلت اليوم':'سجّلت إنجازاً')+'" title="'+(todayDone?'سُجّلت اليوم':'سجّلت إنجازاً')+'"><span class="stat-ico">'+ICONS.check+'</span></button>';""",
    """' aria-label="'+(todayDone?'سُجّلت اليوم':'سجّلت إنجازاً')+'" title="'+(todayDone?'سُجّلت اليوم':'سجّلت إنجازاً')+'"><span class="stat-ico">'+ICONS.check+'</span><span class="hbx-lab">'+(todayDone ? 'سُجّلت اليوم' : 'سجّل إنجاز اليوم')+'</span></button>';""", 'W action label')
rep("""    extra = '<div class="hb-big">'+days+' يوم بدون وقوع</div>';""",
    """    extra = '<div class="hb-big"><b>'+days+'</b> يوم بدون وقوع</div>';""", 'H big')

rep("""  let glance = '';
  if(h.type==='E'){ const sk = buildStreak(h); glance = '<span>سلسلة <b>'+sk+'</b></span><span>الأفضل <b>'+Math.max(bestStreak(h),sk)+'</b></span><span>أيام <b>'+habitDoneDays(h).length+'</b></span>'; }
  else if(h.type==='W'){ glance = '<span>هذا الأسبوع <b>'+weekCount(h,currentWeekId())+' / '+h.requiredPerWeek+'</b></span>'; }
  else { glance = '<span>أفضل <b>'+Math.max(h.bestDays||0, hDays(h))+'</b> يوم</span><span>وقوع <b>'+h.occurrences.length+'</b></span>'; }""",
    """  /* CODIS-CLARITY: الحلقة تحمل الرقم الرئيسي مع تسميته؛ الأرقام الظاهرة تكمّلها بلا تكرار (الكل باقٍ داخل «التفاصيل») */
  let glance = '', ringCap = '';
  if(h.type==='E'){ const sk = buildStreak(h); ringCap = 'سلسلة'; glance = '<span>الأفضل <b>'+Math.max(bestStreak(h),sk)+'</b></span><span>'+(abst ? 'أيام ناجحة' : 'أيام منجزة')+' <b>'+habitDoneDays(h).length+'</b></span><span>المحطة <b>'+((Math.floor(sk/HABIT_MILESTONE_STEP)+1)*HABIT_MILESTONE_STEP)+'</b></span>'; }
  else if(h.type==='W'){ const c = weekCount(h,currentWeekId()); ringCap = 'هذا الأسبوع'; glance = '<span>المتبقي <b>'+Math.max(0, h.requiredPerWeek - c)+'</b></span><span>أسابيع مكتملة <b>'+h.weekHistory.filter(e=>e.ok).length+'</b></span>'; }
  else { ringCap = 'يوم'; glance = '<span>الأفضل <b>'+Math.max(h.bestDays||0, hDays(h))+'</b></span><span>مرات الوقوع <b>'+h.occurrences.length+'</b></span><span>آخر وقوع <b>'+escapeHtml(h.lastOccurrence||'لم يحدث')+'</b></span>'; }""", 'glance')

rep("""  row.innerHTML = `
    <div class="streak-ring">${habitRingSvg(frac)}<span class="streak-num">${ringNum}</span></div>
    <div class="habit-body">
      <div class="habit-name ${nameDone?'done':''}">${escapeHtml(h.text)}</div>
      <div class="hb-tags">${pills}</div>
      ${extra}
      <div class="hb-glance">${glance}</div>
    </div>
    ${action}
    ${acts}
    <button type="button" class="hb-more-toggle\"""",
    """  row.innerHTML = `
    <div class="hbx-head">
      <div class="hbx-ring"><div class="streak-ring">${habitRingSvg(frac)}<span class="streak-num">${ringNum}</span></div><span class="hbx-cap">${ringCap}</span></div>
      <div class="habit-body">
        <div class="habit-name ${nameDone?'done':''}">${escapeHtml(h.text)}</div>
        <div class="hb-tags">${pills}</div>
      </div>
    </div>
    <div class="hb-glance">${glance}</div>
    ${extra ? '<div class="hbx-status">' + extra + '</div>' : ''}
    <div class="hbx-acts">${acts}${action}</div>
    <button type="button" class="hb-more-toggle\"""", 'habit template')

HBX_CSS = r"""
/* ===================== CODIS-CLARITY · غرفة التأديب =====================
   البطاقة طبقات واضحة: (1) الهوية — حلقة التقدّم بتسميتها + الاسم + النوع/الأهمية · (2) أرقام مكمّلة بصفّ واحد ·
   (3) حالة اليوم + التراجع · (4) الإجراء الرئيسي بعرض البطاقة ونص صريح · (5) «التفاصيل» تحت فاصل شعري. */
#page-habits .disc-modes{ margin-bottom:var(--sp-md); }
#page-habits .disc-mode-t{ display:flex; flex-direction:column; align-items:flex-start; gap:1px; min-width:0; text-align:start; line-height:1.35; }
#page-habits .disc-mode-t small{ font-size:var(--fs-caption); font-weight:500; color:var(--text-3); }
#page-habits .disc-mode.is-active .disc-mode-t small{ color:var(--text-2); }
#page-habits .disc-toolbar{ align-items:center; justify-content:space-between; gap:var(--sp-md); margin-bottom:var(--sp-lg); }
#page-habits .disc-mode-desc{ flex:1; min-width:0; margin:0; font-size:var(--fs-sub); line-height:1.6; color:var(--text-3); }
#page-habits .disc-add-trigger{ flex:none; }
#page-habits .add-habit{ gap:var(--sp-lg); }
#page-habits .add-habit .field-label{ display:block; margin-bottom:var(--sp-sm); }
#page-habits .habit-card.hbx{ display:flex; flex-direction:column; align-items:stretch; gap:var(--sp-md); padding:var(--sp-lg); padding-inline-start:calc(var(--sp-lg) + 2px); }
#page-habits .hbx .hbx-head{ display:flex; align-items:flex-start; gap:var(--sp-md); }
#page-habits .hbx .hbx-ring{ flex:none; display:flex; flex-direction:column; align-items:center; gap:4px; width:max(var(--disc-ring), 56px); }
#page-habits .hbx .streak-ring{ grid-column:auto; grid-row:auto; }
#page-habits .hbx .hbx-cap{ font-size:var(--fs-micro); font-weight:600; line-height:1.3; color:var(--text-3); text-align:center; }
#page-habits .hbx .habit-body{ display:flex; flex-direction:column; gap:var(--sp-sm); flex:1; min-width:0; padding-top:2px; }
#page-habits .hbx .habit-name{ grid-column:auto; grid-row:auto; font-size:var(--disc-fs-name); line-height:1.5; }
#page-habits .hbx .hb-tags .pill{ padding:3px 10px; font-size:var(--fs-caption); }
#page-habits .hbx .hb-glance{ display:grid; grid-template-columns:repeat(auto-fit, minmax(72px, 1fr)); gap:var(--sp-sm); margin:0; }
#page-habits .hbx .hb-glance > span{ display:flex; flex-direction:column; align-items:flex-start; gap:2px; min-width:0; padding:8px 10px; border-radius:var(--r-sm); background:rgb(var(--hi-rgb) / .035); font-size:var(--fs-caption); line-height:1.35; color:var(--text-3); overflow-wrap:anywhere; }
#page-habits .hbx .hb-glance > span > b{ order:-1; font-size:15px; font-weight:700; color:var(--text); }
#page-habits .hbx .hbx-status{ display:flex; flex-direction:column; align-items:flex-start; gap:var(--sp-sm); }
#page-habits .hbx .hbx-status:empty{ display:none; }
#page-habits .hbx .hbx-status > *{ margin-top:0; }
#page-habits .hbx .hbx-status .hb-days{ align-self:stretch; }
#page-habits .hbx .hb-big{ font-size:var(--fs-callout); font-weight:600; color:var(--text-2); }
#page-habits .hbx .hb-big b{ color:var(--text); font-weight:800; font-variant-numeric:tabular-nums; }
#page-habits .hbx .hb-link{ min-height:36px; margin:-6px 0; color:var(--text-2); }
#page-habits .hbx .hbx-acts{ display:flex; gap:var(--sp-sm); }
#page-habits .hbx .hbx-acts:empty{ display:none; }
#page-habits .hbx .hbx-acts > .hb-acts{ flex:1 1 auto; margin:0; display:flex; gap:var(--sp-sm); }
#page-habits .hbx .hbx-acts .hb-act{ min-height:48px; }
#page-habits .hbx .hbx-acts > .stat-btn{ flex:1; width:auto; height:48px; min-width:0; display:inline-flex; align-items:center; justify-content:center; gap:8px; padding:0 var(--sp-lg); border-radius:var(--disc-r-field); font:inherit; font-size:14px; font-weight:700; color:var(--text-2); }
#page-habits .hbx .hbx-acts > .stat-btn.active{ color:var(--on-aqua); }
#page-habits .hbx .hbx-acts > .stat-btn[aria-disabled="true"]{ cursor:default; }
#page-habits .hbx .hbx-acts > .hb-fell{ flex:1 1 0; width:auto; min-width:0; height:48px; }
#page-habits .hbx .hbx-acts > .hb-acts + .hb-fell, #page-habits .hbx .hbx-acts > .hb-fell:first-child{ flex:1 1 0; }
#page-habits .hbx .hb-more-toggle{ align-self:stretch; justify-content:center; min-height:44px; margin:-4px calc(-1 * var(--sp-sm)) -8px; border-top:1px solid var(--disc-hair); border-radius:0; }
#page-habits .hbx .hb-more{ margin-top:calc(-1 * var(--sp-md)); }
#page-habits .hbx.is-open .hb-more{ margin-top:0; }
@media (max-width:359px){
  #page-habits .hbx .hb-glance{ grid-template-columns:repeat(2, minmax(0, 1fr)); }
  #page-habits .hbx .hbx-acts{ flex-wrap:wrap; }
  #page-habits .hbx .hbx-acts > *{ flex-basis:100%; }
}
"""
CSS.append(HBX_CSS)

# ---------------------------------------------------------------- 4. تفاصيل البكج والاحتمالات (العرض فقط — نفس CodisBoxes.effective(t) التي يسحب بها roll())
cut("""  const rev = groups.slice().reverse(), topPrize""", """function econPackJump(id){""", r"""  const rev = groups.slice().reverse(), topPrize = groups.length ? Math.max.apply(null, groups.map(g=>g.o.max)) : 0;
  /* CODIS-CLARITY: ترويسة مدمجة ← ملخص ← شريط التوزيع ← مجموعات مطويّة (كل صف = هوية + احتمال + نطاق + عدد + احتمال الكرت الواحد) ← الكروت عند الفتح.
     لا نموذج ثانٍ: كل رقم = g.o.pm (بالألف) من effective(t)، والكرت = pm ÷ عدد كروت فئته (نفس توزيع roll() المنتظم داخل الفئة). */
  const sumPm = groups.reduce((q, g)=>q + (Number(g.o.pm) || 0), 0), maxPm = groups.length ? Math.max.apply(null, groups.map(g=>g.o.pm)) : 1;
  const range = o=>econFmt(o.min) + (o.max !== o.min ? '–' + econFmt(o.max) : '');
  const KIND = { pass:'تجاوز عقوبة', holiday:'بطاقة عطلة', pouch:'كيس فضة', cosmetic:'مظهر' };
  const kindOf = it=>KIND[it.kind] || (it.room === 'weekly' ? 'مكافأة أسبوعية' : it.room === 'monthly' ? 'مكافأة شهرية' : 'مكافأة');
  const nameOf = it=>{ if(it.kind === 'cosmetic'){ try{ const d = CodisCosmetics.def(it.cosmeticId); if(d && d.name) return d.name; }catch(e){} } return it.name || '—'; };
  const gem = '<span class="pk-gems" aria-hidden="true">' + [1,2,3,4,5].map(i=>'<i class="' + (i <= t.index ? 'on' : '') + '"></i>').join('') + '</span>';
  const hero = '<header class="pkx-hero"><div class="pkx-art">' + econBoxArt(t.index) + '</div><div class="pkx-id"><h3 id="econ-pack-title">' + escapeHtml(t.name) + '</h3>' +
    '<div class="pkx-tier">' + gem + '<span>المستوى ' + t.index + ' من 5</span></div><div class="pkx-price"><span>سعر الفتح</span>' + econCoin(t.price) + '</div></div></header>' +
    (total ? '<ul class="pkx-facts"><li><b>' + econFmt(total) + '</b><span>كرت ممكن</span></li><li><b>' + econFmt(groups.length) + '</b><span>فئات مؤهّلة</span></li><li><b>' + econFmt(topPrize) + '</b><span>أعلى قيمة</span></li></ul>' : '');
  const overview = groups.length ? '<section class="pkx-ov" aria-labelledby="pkx-ov-h"><div class="pkx-ovh"><h4 class="pkx-h" id="pkx-ov-h">توزيع الاحتمالات</h4><span class="pkx-sum">المجموع <b dir="ltr">' + econPm(sumPm) + '</b></span></div>' +
    '<div class="pk-seg" role="img" aria-label="' + escapeHtml(groups.map(g=>g.o.name + ' ' + econPm(g.o.pm)).join('، ')) + '">' + groups.map(g=>'<i style="flex:' + g.o.pm + ';--k:' + rgb(g.o.tone) + '"></i>').join('') + '</div>' +
    '<p class="pkx-ovn">كل فئة تحت: احتمالها، نطاق قيمتها، عدد كروتها، واحتمال الكرت الواحد. افتح الفئة لترى كروتها.</p></section>' : '';
  const list = groups.length ? '<div class="pkx-groups" role="list">' + rev.map(g=>{
    const each = g.o.pm / 10 / g.items.length, w = Math.max(2, Math.round(g.o.pm / maxPm * 100));
    return '<details class="pkx-grp pk-grp" id="pk-g-' + escapeHtml(g.o.id) + '" role="listitem" style="--k:' + rgb(g.o.tone) + '"><summary class="pkx-gs">' +
      '<span class="pkx-gs-top"><span class="pk-gs-dot" aria-hidden="true"></span><b class="pkx-gn">' + escapeHtml(g.o.name) + '</b><b class="pkx-gp" dir="ltr">' + econPm(g.o.pm) + '</b><span class="pk-gs-c" aria-hidden="true"></span></span>' +
      '<span class="pkx-gbar" aria-hidden="true"><i style="width:' + w + '%"></i></span>' +
      '<span class="pkx-gm"><span>القيمة <b dir="ltr">' + range(g.o) + '</b></span><span><b>' + econFmt(g.items.length) + '</b> كرت</span><span>الكرت الواحد <b dir="ltr">' + pctTxt(each) + '</b></span></span></summary>' +
      '<div class="pkx-cards" role="list">' + g.items.map(it=>'<div class="pkx-cell" role="listitem">' + econPackTileHtml(it, econRarityById(it.rarity)).replace(' role="listitem"', '') +
        '<span class="pkx-cap"><span class="pkx-cn">' + escapeHtml(nameOf(it)) + '</span><span class="pkx-ck">' + escapeHtml(kindOf(it)) + '</span><b class="pkx-cp" dir="ltr">' + pctTxt(each) + '</b></span></div>').join('') + '</div></details>';
  }).join('') + '</div>' : '<div class="eco-empty pk-empty">ماكو كروت مؤهّلة حالياً — أضف مكافآت مفعّلة من الإعدادات ← المكافآت</div>';
  body.innerHTML = hero + overview + list + close;
  codisFitRewardCard(body); codisWatchRewardCards(body);
}
""", 'pack paint')

PKX_CSS = r"""
/* ===================== CODIS-CLARITY · تفاصيل البكج =====================
   ترويسة مدمجة · ملخص ثلاثي · شريط توزيع واحد · فئات مطويّة افتراضياً (هادئة) · كروت بشبكة تلتف (لا تمرير أفقي ضيق) ونص الاسم والاحتمال تحت كل كرت. */
.pkx-hero{ display:grid; grid-template-columns:auto minmax(0, 1fr); align-items:center; gap:var(--sp-lg); padding:2px 4px 0; padding-inline-start:48px; }   /* زر الإغلاق بزاوية البداية فوق الرسمة */
.pkx-art{ width:84px; } .pkx-art img, .pkx-art svg{ display:block; width:100%; height:auto; }
.pkx-id{ display:flex; flex-direction:column; gap:6px; min-width:0; }
.pk-modal .pkx-id h3{ margin:0; font-size:20px; line-height:1.3; text-align:start; overflow-wrap:anywhere; }
.pkx-tier{ display:flex; align-items:center; gap:8px; font-size:var(--fs-caption); color:var(--text-3); }
.pkx-price{ display:flex; align-items:center; gap:8px; font-size:15px; font-weight:800; }
.pkx-price > span{ font-size:var(--fs-caption); font-weight:500; color:var(--text-3); }
.pkx-facts{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:var(--sp-sm); list-style:none; margin:var(--sp-lg) 0 0; padding:0; }
.pkx-facts li{ display:flex; flex-direction:column; align-items:center; gap:2px; padding:10px 4px; border-radius:var(--r-md); background:rgb(var(--hi-rgb) / .045); border:1px solid rgb(var(--hi-rgb) / .07); text-align:center; }
.pkx-facts b{ font-size:17px; font-variant-numeric:tabular-nums; line-height:1.3; }
.pkx-facts span{ font-size:var(--fs-caption); color:var(--text-3); line-height:1.35; }
.pkx-ov{ margin-top:var(--sp-xl); }
.pkx-ovh{ display:flex; align-items:baseline; justify-content:space-between; gap:var(--sp-sm); margin-bottom:var(--sp-sm); }
.pkx-h{ margin:0; font-size:var(--fs-callout); font-weight:700; color:var(--text); }
.pkx-sum{ font-size:var(--fs-caption); color:var(--text-3); } .pkx-sum b{ color:var(--text-2); font-variant-numeric:tabular-nums; }
.pkx-ovn{ margin:var(--sp-sm) 0 0; font-size:var(--fs-caption); line-height:1.7; color:var(--text-3); }
.pkx-groups{ display:flex; flex-direction:column; gap:var(--sp-sm); margin-top:var(--sp-lg); }
.pkx-grp{ border-radius:var(--r-md); border:1px solid rgb(var(--k) / .22); background:rgb(var(--hi-rgb) / .03); }
.pkx-grp[open]{ background:linear-gradient(180deg, rgb(var(--k) / .07), rgb(var(--hi-rgb) / .02) 120px); }
.pkx-gs{ display:flex; flex-direction:column; gap:8px; padding:12px 14px; list-style:none; cursor:pointer; min-height:48px; }
.pkx-gs::-webkit-details-marker{ display:none; }
.pkx-gs:focus-visible{ outline:2px solid rgb(var(--k)); outline-offset:-2px; border-radius:var(--r-md); }
.pkx-gs-top{ display:flex; align-items:center; gap:10px; }
.pkx-gn{ flex:1; min-width:0; font-size:15px; }
.pkx-gp{ font-size:18px; font-weight:800; font-variant-numeric:tabular-nums; color:color-mix(in srgb, rgb(var(--k)) 55%, #fff); }
.pkx-grp .pk-gs-c{ flex:none; }
.pkx-grp[open] .pk-gs-c{ transform:rotate(-135deg); }
.pkx-gbar{ display:block; height:5px; border-radius:var(--r-full); background:rgb(var(--hi-rgb) / .06); overflow:hidden; }
.pkx-gbar i{ display:block; height:100%; border-radius:inherit; background:rgb(var(--k)); }
.pkx-gm{ display:flex; flex-wrap:wrap; gap:2px 14px; font-size:var(--fs-caption); color:var(--text-3); }
.pkx-gm b{ color:var(--text-2); font-weight:700; font-variant-numeric:tabular-nums; }
.pkx-cards{ display:grid; grid-template-columns:repeat(auto-fill, minmax(96px, 1fr)); gap:var(--sp-md) var(--sp-sm); padding:4px 12px 14px; }
.pkx-cell{ display:flex; flex-direction:column; gap:6px; min-width:0; }
.pkx-cell .pk-tile{ width:100%; }
.pkx-cap{ display:flex; flex-direction:column; gap:1px; min-width:0; }
.pkx-cn{ font-size:var(--fs-caption); font-weight:600; line-height:1.4; color:var(--text); overflow-wrap:anywhere; }
.pkx-ck{ font-size:var(--fs-micro); color:var(--text-3); }
.pkx-cp{ align-self:flex-start; margin-top:3px; padding:1px 8px; border-radius:var(--r-full); background:rgb(var(--k) / .14); color:color-mix(in srgb, rgb(var(--k)) 50%, #fff); font-size:var(--fs-caption); font-variant-numeric:tabular-nums; }
@media (max-width:359px){ .pkx-cards{ grid-template-columns:repeat(2, minmax(0, 1fr)); } .pkx-art{ width:68px; } }
"""
CSS.append(PKX_CSS)

# ---------------------------------------------------------------- 5. ظهر البطاقة: بلا قص صامت + معلومات نتائج البكج
rep("""function econBulkInfo(r){""", """/* CODIS-CLARITY: صفوف ظهر بطاقة نتيجة البكج — النوع والقيمة الفعلية (CodisRevealLevels.valueOfResult) بدل الفئة والمصدر فقط */
function econBulkBackRows(r, inf, extra){
  const KIND = { reward:'مكافأة', pass:'تجاوز عقوبة', holiday:'بطاقة عطلة', pouch:'كيس فضة', cosmetic:'مظهر' };
  let v = 0; try{ v = Number(CodisRevealLevels.valueOfResult(r)) || 0; }catch(e){}
  return [['النوع', KIND[inf.kind] || '—'], ['الفئة', r.rarity && r.rarity.name], v > 0 ? ['القيمة', econCoin(v), '', true] : null, ['من', r.tier && r.tier.name]].concat(extra || []);
}
function econBulkInfo(r){""", 'bulk back rows')
rep("""codisFlipHtml(art, codisCardBackHtml(inf.name, [['الفئة', rar.name], ['من', r.tier.name]], { tone:rar.tone,""",
    """codisFlipHtml(art, codisCardBackHtml(inf.name, econBulkBackRows(r, inf), { tone:rar.tone,""", 'bulk cell back')
rep("""  const back = codisCardBackHtml(inf.name, [['الفئة', rar.name], ['من', r.tier.name], ['البكج رقم', econFmt(i + 1)]], { tone:rar.tone, kind:inf.kind });""",
    """  const back = codisCardBackHtml(inf.name, econBulkBackRows(r, inf, [['البكج رقم', econFmt(i + 1)]]), { tone:rar.tone, kind:inf.kind });""", 'bulk zoom back')

CBK_CSS = r"""
/* ===================== CODIS-CLARITY · ظهر البطاقة =====================
   كان: لوح بحدّ 60% + overflow:hidden، العنوان سطران، القيمة سطر واحد بنقاط، الملاحظة سطران ⇒ نص يختفي بصمت.
   الآن: الإطار 4:5 نفسه (والرسم بلا تمديد)؛ اللوح يكبر حتى خط الميدالية (70% من البطاقة) ويلتف كل شيء، وما زاد يُقرأ بتمرير داخلي مضبوط مع تلاشٍ يدلّ عليه. */
.cbk .cbk-in{ max-height:calc(69cqh - 7cqw);   /* الحافة العليا تبقى تحت الميدالية (أعلى 30% من البطاقة) */
  overflow-x:hidden; overflow-y:auto; overscroll-behavior:contain; -webkit-overflow-scrolling:touch; scrollbar-width:thin; scrollbar-color:rgba(var(--k),.45) transparent;
  margin:0 6% 7%; padding:3.6cqw 4.6cqw 4cqw; gap:2cqw; }
.cbk .cbk-in::-webkit-scrollbar{ width:3px; } .cbk .cbk-in::-webkit-scrollbar-thumb{ background:rgba(var(--k),.45); border-radius:3px; }
.cbk .cbk-in .cbk-t{ display:block; -webkit-line-clamp:unset; overflow:visible; font-size:clamp(10px, 9cqw, 15px); line-height:1.35; overflow-wrap:anywhere; }
.cbk .cbk-in .cbk-rows{ gap:1.8cqw; padding-top:2.6cqw; }
.cbk .cbk-in .cbk-rows > div{ flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:.4cqw 3cqw; }
.cbk .cbk-in .cbk-rows dt{ font-size:clamp(8.5px, 7cqw, 11.5px); line-height:1.4; color:var(--text-3); }
.cbk .cbk-in .cbk-rows dd{ flex:1 1 auto; white-space:normal; overflow:visible; text-overflow:clip; overflow-wrap:anywhere; line-height:1.4; font-size:clamp(9px, 7.8cqw, 12.5px); }
.cbk .cbk-in .cbk-rows dd .eco-coin{ display:inline-flex; vertical-align:-.1em; }
.cbk .cbk-in .cbk-note{ display:block; -webkit-line-clamp:unset; overflow:visible; font-size:clamp(8.5px, 6.8cqw, 11px); line-height:1.5; padding-top:1.6cqw; border-top:1px solid rgba(var(--k),.16); }
"""
CBK_CSS += r""".cbk .cbk-in.is-scroll:not(.is-end){ -webkit-mask-image:linear-gradient(180deg, #000 calc(100% - 16px), transparent); mask-image:linear-gradient(180deg, #000 calc(100% - 16px), transparent); }
"""
CSS.append(CBK_CSS)
rep("""  el.classList.toggle('is-flipped', on); el.setAttribute('aria-pressed', on ? 'true' : 'false');
  const f = el.querySelector('.cflip-f'), b = el.querySelector('.cflip-b');""",
    """  el.classList.toggle('is-flipped', on); el.setAttribute('aria-pressed', on ? 'true' : 'false');
  if(on) codisCbkFade(el);
  const f = el.querySelector('.cflip-f'), b = el.querySelector('.cflip-b');""", 'flip fade')
rep("""function codisFlipToggle(el){""", """/* CODIS-CLARITY: لوح ظهر البطاقة الذي يزيد عن مساحته يتمرّر داخلياً؛ تلاشٍ سفلي يدلّ على البقية ويختفي عند آخره */
function codisCbkFade(el){
  requestAnimationFrame(()=>{ (el.querySelectorAll ? el.querySelectorAll('.cbk-in') : []).forEach(p=>{
    const upd = ()=>{ const s = p.scrollHeight > p.clientHeight + 1; p.classList.toggle('is-scroll', s); p.classList.toggle('is-end', !s || p.scrollTop + p.clientHeight >= p.scrollHeight - 2); };
    upd(); if(!p._cbkF){ p._cbkF = 1; p.addEventListener('scroll', upd, { passive:true }); }
  }); });
}
function codisFlipToggle(el){""", 'cbk fade fn')

# ---------------------------------------------------------------- 6. سجل الكوينز (نفس data.wallet؛ الأحدث أولاً؛ نفس الترقيم econLogLimit)
cut("""function econRenderLog(){""", """


/* ================= HABITS ================= */""", r"""function econRenderLog(){
  const box = document.getElementById('eco-log-body'); if(!box) return; const w = data.wallet;
  /* CODIS-CLARITY: الرصيد بارز ← المكتسب/المصروف ← الحركات مجمّعة باليوم (بلا تغيير الترتيب أو الطوابع) ← التقارير ← بطاقات التجاوز المستخدمة */
  const ARW = up=>'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="' + (up ? 'M8 13V3M4 7l4-4 4 4' : 'M8 3v10M4 9l4 4 4-4') + '" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  let html = '<section class="ecl-sum" aria-label="ملخص الكوينز"><div class="ecl-bal"><span class="ecl-lab">الرصيد الحالي</span><span class="ecl-balv">' + econCoin(w.balance) + '</span></div>' +
    '<div class="ecl-pair"><div class="ecl-tot is-up"><span class="ecl-ti">' + ARW(true) + '</span><span class="ecl-lab">إجمالي المكتسب</span><b dir="ltr">' + (w.lifetimeEarned > 0 ? '+' + econFmt(w.lifetimeEarned) : '0') + '</b></div>' +
    '<div class="ecl-tot is-down"><span class="ecl-ti">' + ARW(false) + '</span><span class="ecl-lab">إجمالي المصروف</span><b dir="ltr">' + (w.lifetimeSpent > 0 ? '−' + econFmt(w.lifetimeSpent) : '0') + '</b></div></div></section>';
  const txs = w.transactions.slice().reverse();
  html += '<section class="ecl-sec" aria-labelledby="ecl-h-tx"><header class="ecl-sh"><h3 id="ecl-h-tx" class="ecl-h eco-sec-title">الحركات</h3><span class="ecl-n">' + econFmt(txs.length) + '</span></header>';
  if(!txs.length) html += '<div class="ecl-empty"><span class="ecl-empty-ico">' + codisIcon('coin', { size:'md' }) + '</span><b>ماكو حركات بعد</b><span>كل كوين تكسبه أو تصرفه يظهر هنا مع سببه ووقته — استبدل مكافأة بكوينز لتبدأ.</span></div>';
  else {
    const tk = todayKey(), yk = yesterdayKey(); let cur = null, open = false;
    txs.slice(0, econLogLimit).forEach(t=>{
      const up = t.amount > 0, d = new Date(t.createdAt), ok = !isNaN(d.getTime()), dk = ok ? localDateStr(d) : '';
      if(dk !== cur){ if(open) html += '</div></div>'; cur = dk; open = true;
        html += '<div class="ecl-day"><h4 class="ecl-dh">' + (!ok ? 'بدون تاريخ' : dk === tk ? 'اليوم' : dk === yk ? 'أمس' : escapeHtml(formatArDate(t.createdAt))) + '</h4><div class="ios-list ecl-list">'; }
      const time = ok ? d.toLocaleTimeString('ar', { hour:'2-digit', minute:'2-digit' }) : '';
      html += '<div class="eco-log-row ecl-row ' + (up ? 'is-up' : 'is-down') + '"><span class="ecl-ri" aria-hidden="true">' + ARW(up) + '</span><div class="eco-log-main"><span class="eco-log-reason">' + escapeHtml(t.reason) + '</span>' +
        (t.meta && t.meta.name ? '<span class="eco-log-sub ecl-item">' + escapeHtml(t.meta.name) + '</span>' : '') + '</div>' +
        '<div class="ecl-amt"><b class="' + (up ? 'eco-up' : 'eco-down') + '" dir="ltr"><span class="sr-only">' + (up ? 'مكتسب ' : 'مصروف ') + '</span>' + (up ? '+' : '−') + econFmt(Math.abs(t.amount)) + '</b>' + (time ? '<span class="ecl-time">' + escapeHtml(time) + '</span>' : '') + '</div></div>';
    });
    if(open) html += '</div></div>';
    if(txs.length > econLogLimit) html += '<button type="button" class="btn btn-secondary eco-full ecl-more" onclick="econShowMoreLog()">عرض المزيد · باقي ' + econFmt(txs.length - econLogLimit) + '</button>';
  }
  html += '</section>';
  html += '<section class="ecl-sec" aria-labelledby="ecl-h-rp"><header class="ecl-sh"><h3 id="ecl-h-rp" class="ecl-h eco-sec-title">التقارير المحفوظة</h3></header><div class="settings-card ecl-card">' + econReportsListHtml() + '</div></section>';
  const up = CodisPasses.used().sort((a,b)=>a.usedAt < b.usedAt ? 1 : a.usedAt > b.usedAt ? -1 : 0).slice(0, 20);
  if(up.length) html += '<section class="ecl-sec" aria-labelledby="ecl-h-ps"><header class="ecl-sh"><h3 id="ecl-h-ps" class="ecl-h eco-sec-title">بطاقات التجاوز المستخدمة</h3><span class="ecl-n">' + econFmt(up.length) + '</span></header><div class="ios-list eco-log ecl-list">' + up.map(p=>'<div class="eco-log-row"><b class="eco-log-ico">' + ICONS.check + '</b><div class="eco-log-main"><span class="eco-log-reason">' + escapeHtml(CodisPasses.label(p)) + '</span>' +
    '<span class="eco-log-sub">' + (p.usedForName ? escapeHtml(p.usedForName) + ' · ' : '') + 'بدون كوينز · ' + escapeHtml(formatArDate(p.usedAt)) + '</span></div></div>').join('') + '</div></section>';
  box.innerHTML = html;
}""", 'render log')

ECL_CSS = r"""
/* ===================== CODIS-CLARITY · سجل الكوينز ===================== */
#eco-log-body{ gap:var(--sp-xl); }
.ecl-sum{ display:flex; flex-direction:column; gap:var(--sp-sm); }
.ecl-bal{ display:flex; flex-direction:column; align-items:center; gap:4px; padding:var(--sp-lg) var(--sp-md); border-radius:var(--r-lg); background:radial-gradient(90% 120% at 50% 0%, var(--gold-a12), transparent 70%), var(--mat-panel-fill); border:1px solid var(--mat-panel-edge); box-shadow:var(--mat-panel-shadow); text-align:center; }
.ecl-balv .eco-coin{ font-size:clamp(26px, calc(8 * var(--vw)), 34px); font-weight:800; gap:8px; color:var(--gold-soft); }
.ecl-balv .eco-coin svg{ width:.8em; height:.8em; }
.ecl-lab{ font-size:var(--fs-caption); color:var(--text-3); }
.ecl-pair{ display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:var(--sp-sm); }
.ecl-tot{ display:grid; grid-template-columns:auto minmax(0, 1fr); grid-template-rows:auto auto; column-gap:10px; align-items:center; padding:12px; border-radius:var(--r-md); background:var(--mat-panel-fill); border:1px solid var(--mat-panel-edge); }
.ecl-tot .ecl-ti{ grid-row:1 / 3; }
.ecl-tot b{ font-size:clamp(15px, calc(4.4 * var(--vw)), 18px); font-weight:800; font-variant-numeric:tabular-nums; text-align:start; overflow-wrap:anywhere; }
.ecl-tot.is-up b{ color:var(--success-ink); } .ecl-tot.is-down b{ color:var(--danger-ink); }
.ecl-ti, .ecl-ri{ width:32px; height:32px; flex:none; display:grid; place-items:center; border-radius:var(--r-full); }
.ecl-ti svg, .ecl-ri svg{ width:15px; height:15px; }
.is-up > .ecl-ti, .ecl-row.is-up .ecl-ri{ color:var(--success-ink); background:var(--success-a12); }
.is-down > .ecl-ti, .ecl-row.is-down .ecl-ri{ color:var(--danger-ink); background:var(--danger-a12); }
.ecl-sec{ display:flex; flex-direction:column; gap:var(--sp-md); }
.ecl-sh{ display:flex; align-items:center; gap:var(--sp-sm); }
.ecl-sh .ecl-h{ margin:0; font-size:var(--fs-headline); font-weight:700; }
.ecl-n{ min-width:24px; padding:1px 8px; border-radius:var(--r-full); background:rgb(var(--hi-rgb) / .07); color:var(--text-2); font-size:var(--fs-caption); font-weight:700; text-align:center; font-variant-numeric:tabular-nums; }
.ecl-day{ display:flex; flex-direction:column; gap:6px; }
.ecl-day + .ecl-day{ margin-top:var(--sp-sm); }
.ecl-dh{ margin:0; padding-inline:4px; font-size:var(--fs-caption); font-weight:700; color:var(--text-3); }
.ecl-list{ overflow:hidden; }
.ecl-row{ align-items:center; gap:12px; padding:12px 14px; }
.ecl-row .eco-log-main{ flex:1; }
.ecl-row .eco-log-reason{ font-size:var(--fs-callout); line-height:1.5; overflow-wrap:anywhere; }
.ecl-item{ color:var(--text-2); }
.ecl-amt{ flex:none; display:flex; flex-direction:column; align-items:flex-end; gap:2px; }
.ecl-amt b{ min-width:0; font-size:16px; font-weight:800; font-variant-numeric:tabular-nums; }
.ecl-time{ font-size:var(--fs-caption); color:var(--text-3); font-variant-numeric:tabular-nums; }
.ecl-more{ margin-top:var(--sp-xs); }
.ecl-card{ padding:var(--sp-sm) var(--sp-md); }
.ecl-empty{ display:flex; flex-direction:column; align-items:center; gap:6px; padding:var(--sp-xl) var(--sp-lg); border-radius:var(--r-lg); border:1px dashed var(--glass-border-strong); text-align:center; }
.ecl-empty b{ font-size:var(--fs-body); } .ecl-empty > span:last-child{ font-size:var(--fs-sub); line-height:1.7; color:var(--text-3); max-width:30ch; }
.ecl-empty-ico{ width:44px; height:44px; display:grid; place-items:center; border-radius:var(--r-full); background:var(--gold-a12); color:var(--gold); }
"""
CSS.append(ECL_CSS)

# ---------------------------------------------------------------- 7. المباعة/المستخدمة + «الأكثر استخداماً»
# r.k = العرض الذي يظهر فيه السجل (عدّادات «غير مقروء» كما هي)؛ r.st = الحالة الفعلية (used|expired|sold|silver)؛ r.rk = هوية الترتيب للاستخدام الفعلي فقط
rep("""    const sold = it.status === 'sold';
    rows.push({ k:sold ? 'sold' : 'used', t:it.statusAt, html:""",
    """    const sold = it.status === 'sold';
    rows.push({ k:sold ? 'sold' : 'used', st:sold ? 'sold' : 'used', t:it.statusAt, coins:sold ? Number(it.soldFor) || 0 : 0,
      rk:sold ? null : { key:'r:' + (it.rewardId || ('n:' + it.name + '|' + (it.rarity || '') + '|' + (it.room || it.scope || ''))), name:it.name, type:it.scope === 'weekly' ? 'مكافأة أسبوعية' : it.scope === 'monthly' ? 'مكافأة شهرية' : 'مكافأة' + (it.room && it.room !== 'weekly' && it.room !== 'monthly' ? ' · ' + econRoomLabel(it.room) : '') }, html:""", 'closed inv rows')
rep("""  CodisPasses.used().forEach(p=>rows.push({ k:'used', t:p.usedAt, html:""",
    """  CodisPasses.used().forEach(p=>rows.push({ k:'used', st:'used', t:p.usedAt, rk:{ key:'p:' + p.scope + ':' + econNormSeverity(p.severity, 'MEDIUM'), name:CodisPasses.label(p), type:'تجاوز عقوبة' }, html:""", 'closed pass rows')
rep("""  hcdClosedRows().forEach(r=>{ r.k = 'used'; rows.push(r); }); econSilverRows().forEach(r=>{ r.k = 'used'; rows.push(r); });""",
    """  hcdClosedRows().forEach(r=>{ r.k = 'used'; rows.push(r); }); econSilverRows().forEach(r=>{ r.k = 'used'; r.st = 'silver'; rows.push(r); });""", 'closed hcd silver')
rep("""    const sub = used ? d.ui.closedSub(c) : 'انتهت صلاحيتها';
    return { t:t, html:""", """    const sub = used ? d.ui.closedSub(c) : 'انتهت صلاحيتها';
    /* CODIS-CLARITY: المنتهية تبقى «منتهية» (st:'expired') — لا تُعرض ولا تُحسب كاستخدام */
    return { t:t, st:used ? 'used' : 'expired', rk:used ? { key:'h:' + c.kind, name:d.name, type:'بطاقة عطلة' } : null, html:""", 'hcd closed st')

cut("""function econClosedPanelHtml(){""", """function econToggleClosed(){""", r"""/* CODIS-CLARITY: ترتيب «الأكثر استخداماً» من سجلات الاستخدام الفعلية فقط (لا بيع ولا انتهاء ولا شراء ولا فضة)، مجمّعة بهوية ثابتة */
function econMostUsed(rows){
  const m = new Map();
  (rows || econClosedRows()).forEach(r=>{
    if(r.st !== 'used' || !r.rk) return;
    const e = m.get(r.rk.key) || { key:r.rk.key, name:r.rk.name, type:r.rk.type, n:0, last:'' };
    e.n++; if(r.t && r.t > e.last){ e.last = r.t; e.name = r.rk.name; } m.set(r.rk.key, e);
  });
  return Array.from(m.values()).sort((a, b)=>b.n - a.n || (a.last < b.last ? 1 : a.last > b.last ? -1 : 0));
}
function econClosedPanelHtml(){
  const rows = econClosedRows(), u = econClosedUnread(rows), v = econClosedView;
  const desc = (a, b)=>a.t < b.t ? 1 : a.t > b.t ? -1 : 0, of = st=>rows.filter(r=>r.st === st).sort(desc);
  const sold = of('sold'), used = of('used'), expired = of('expired'), silver = of('silver');
  const ICO = { sold:codisIcon('coin'), used:ICONS.check };
  const tab = (id, label, n)=>'<button type="button" role="tab" id="eco-ctab-' + id + '" aria-controls="eco-cpanel" class="eco-ctab hx-tab' + (v === id ? ' is-on' : '') + '" aria-selected="' + (v === id ? 'true' : 'false') + '" tabindex="' + (v === id ? '0' : '-1') + '" onclick="econClosedSetView(\'' + id + '\')">' +
    '<span class="hx-ti" aria-hidden="true">' + ICO[id] + '</span><span class="hx-tl">' + label + '</span><span class="hx-tc">' + econFmt(n) + '</span>' +
    (u[id] ? '<span class="eco-hist-n eco-ctab-n" aria-label="' + escapeHtml(econFmt(u[id]) + ' غير مقروء') + '">' + econFmt(u[id]) + '</span>' : '') + '</button>';
  const sec = (title, n, body, cls)=>'<section class="hx-sec' + (cls ? ' ' + cls : '') + '"><h4 class="hx-h"><span>' + title + '</span>' + (n !== null ? '<span class="hx-hn">' + econFmt(n) + '</span>' : '') + '</h4>' + body + '</section>';
  const listOf = (list, cls)=>'<div class="ios-list eco-log hx-list' + (cls ? ' ' + cls : '') + '">' + list.slice(0, 60).map(r=>r.html).join('') + '</div>' + (list.length > 60 ? '<p class="hx-more">يُعرض آخر 60 من ' + econFmt(list.length) + '</p>' : '');
  let body = '';
  if(v === 'sold'){
    const total = sold.reduce((q, r)=>q + (r.coins || 0), 0);
    body = sold.length ? '<div class="hx-stat"><span>مجموع ما بعته</span><b class="eco-up" dir="ltr">+' + econFmt(total) + '</b></div>' + sec('سجل البيع', sold.length, listOf(sold))
      : '<div class="hx-empty">ما في مكافآت مباعة بعد — اللي تبيعه من «بحوزتك» يظهر هنا بقيمته وتاريخه.</div>';
  } else {
    const top = econMostUsed(rows), RANK = ['الأكثر استخداماً', 'ثاني أكثر استخداماً', 'ثالث أكثر استخداماً'];
    if(top.length) body += sec('الأكثر استخداماً', null, '<ol class="hx-rank">' + top.slice(0, 5).map((e, i)=>'<li class="hx-rk' + (i < 3 ? ' is-top is-' + (i + 1) : '') + '"><span class="hx-rn" aria-hidden="true">' + (i + 1) + '</span>' +
      '<span class="hx-rm"><span class="hx-rname">' + escapeHtml(e.name) + '</span><span class="hx-rsub">' + escapeHtml((i < 3 ? RANK[i] + ' · ' : '') + e.type) + '</span></span><b class="hx-rc"><span dir="ltr">×' + econFmt(e.n) + '</span><small>' + (e.n === 1 ? 'مرة' : 'مرات') + '</small></b></li>').join('') + '</ol>' +
      '<p class="hx-note">محسوبة من سجل الاستخدام المحفوظ (المكافآت المستخدمة · بطاقات التجاوز · بطاقات العطلة). البيع والانتهاء والشراء ما تنحسب.</p>', 'hx-top');
    body += used.length ? sec('سجل الاستخدام', used.length, listOf(used)) : '<div class="hx-empty">ما في مكافآت مستخدمة بعد — لما تستخدم مكافأة أو بطاقة تظهر هنا.</div>';
    if(expired.length) body += sec('انتهت صلاحيتها', expired.length, listOf(expired, 'is-expired'), 'hx-exp');
    body += hcdTaskLogHtml();
    if(silver.length) body += sec('سجل الفضة', silver.length, listOf(silver));
  }
  return '<div class="settings-card eco-closed hx" id="eco-closed-panel"><div class="eco-ctabs hx-tabs" role="tablist" aria-label="المباعة والمستخدمة">' + tab('sold', 'المباعة', sold.length) + tab('used', 'المستخدمة', used.length) + '</div>' +
    '<div class="hx-panel" id="eco-cpanel" role="tabpanel" aria-labelledby="eco-ctab-' + v + '">' + body + '</div></div>';
}
""", 'closed panel')

HX_CSS = r"""
/* ===================== CODIS-CLARITY · المباعة/المستخدمة ===================== */
.eco-closed.hx{ display:flex; flex-direction:column; gap:var(--sp-lg); }
.hx .hx-tabs{ display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:var(--sp-sm); margin:0; padding:4px; border-radius:var(--r-md); background:var(--mat-well); }
.hx .hx-tab{ position:relative; min-height:48px; gap:8px; padding:0 10px; border-radius:var(--r-sm); border:1px solid transparent; background:transparent; }
.hx .hx-tab.is-on{ background:var(--glass-strong); border-color:var(--aqua-a40); color:var(--text); }
.hx .hx-tab:focus-visible{ outline:2px solid var(--aqua); outline-offset:2px; }
.hx-ti{ display:grid; place-items:center; width:18px; height:18px; } .hx-ti svg, .hx-ti .ico{ width:16px; height:16px; }
.hx-tc{ min-width:22px; padding:0 7px; border-radius:var(--r-full); background:rgb(var(--hi-rgb) / .07); color:var(--text-2); font-size:var(--fs-caption); font-weight:700; line-height:20px; font-variant-numeric:tabular-nums; }
.hx .hx-tab .eco-ctab-n{ position:absolute; top:-6px; inset-inline-end:-4px; }
.hx-panel{ display:flex; flex-direction:column; gap:var(--sp-lg); }
.hx-sec{ display:flex; flex-direction:column; gap:var(--sp-sm); }
.hx-h{ display:flex; align-items:center; gap:var(--sp-sm); margin:0; font-size:var(--fs-callout); font-weight:700; color:var(--text); }
.hx-hn{ min-width:22px; padding:0 7px; border-radius:var(--r-full); background:rgb(var(--hi-rgb) / .07); color:var(--text-2); font-size:var(--fs-caption); line-height:20px; text-align:center; font-variant-numeric:tabular-nums; }
.hx-list .eco-log-row{ padding:12px 14px; }
.hx-list .eco-log-row > b{ min-width:52px; font-variant-numeric:tabular-nums; }
.hx-list.is-expired .eco-log-reason{ color:var(--text-2); }
.hx-stat{ display:flex; align-items:center; justify-content:space-between; gap:var(--sp-md); padding:12px 14px; border-radius:var(--r-md); background:var(--mat-well); font-size:var(--fs-sub); color:var(--text-2); }
.hx-stat b{ font-size:17px; font-weight:800; font-variant-numeric:tabular-nums; }
.hx-more, .hx-note{ margin:0; font-size:var(--fs-caption); line-height:1.7; color:var(--text-3); }
.hx-empty{ padding:var(--sp-lg); border-radius:var(--r-md); border:1px dashed var(--glass-border-strong); text-align:center; font-size:var(--fs-sub); line-height:1.7; color:var(--text-3); }
.hx-rank{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:6px; }
.hx-rk{ display:flex; align-items:center; gap:12px; min-height:56px; padding:8px 12px; border-radius:var(--r-md); background:rgb(var(--hi-rgb) / .035); border:1px solid var(--glass-border); }
.hx-rn{ flex:none; width:28px; height:28px; display:grid; place-items:center; border-radius:var(--r-full); background:rgb(var(--hi-rgb) / .07); color:var(--text-2); font-size:var(--fs-sub); font-weight:800; font-variant-numeric:tabular-nums; }
.hx-rk.is-1 .hx-rn{ background:var(--gold-a30); color:var(--gold-soft); }
.hx-rk.is-2 .hx-rn{ background:rgb(var(--hi-rgb) / .14); color:var(--text); }
.hx-rk.is-3 .hx-rn{ background:rgb(var(--gold-rgb) / .16); color:var(--gold); }
.hx-rk.is-1{ border-color:var(--gold-a30); }
.hx-rm{ flex:1; min-width:0; display:flex; flex-direction:column; gap:2px; }
.hx-rname{ font-size:var(--fs-callout); font-weight:600; line-height:1.45; overflow-wrap:anywhere; }
.hx-rsub{ font-size:var(--fs-caption); color:var(--text-3); }
.hx-rc{ flex:none; display:flex; flex-direction:column; align-items:center; font-size:16px; font-weight:800; font-variant-numeric:tabular-nums; }
.hx-rc small{ font-size:var(--fs-micro); font-weight:500; color:var(--text-3); }
"""
CSS.append(HX_CSS)

# @@NEXT@@

rep("""@media (prefers-reduced-motion:reduce){ .cd-sheet, .cd-back{ transition:none; } }""",
    """@media (prefers-reduced-motion:reduce){ .cd-sheet, .cd-back{ transition:none; } }""" + ''.join(CSS), 'css inject')

open(dst, 'w', encoding='utf-8', newline='').write(s)
print('ok CODIS-CLARITY ->', dst)
