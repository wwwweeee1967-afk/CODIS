"""CODIS-V33 (3.20.0) — UI/UX/identity refinement. Visual + interaction only; no data, economy, storage or schema change.

  py -3 tools/patch_v33.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (after patch_v32; then set_version.py)

  2  reward editor re-layout (root cause of overflow: grid tracks sized by input intrinsic width)   -> econRewardEditor + v33.css
  3  distinct empty states for Planning / Operations / Teacher (own copy + own vector art)           -> HTML + codisEsMark
  4  paper depth tokens, lighter blur (all backdrop sources), «يُحفظ الاختيار…» removed
  5  paper look for the dock fused under the reward card (tinted from --oc)                         -> v33.css
  6  circular es-mark retired for all empty states (art per room / state)
  7  no selection / callout on content (inputs exempt)
  8  CodisNav: internal back = right-edge -> left only, never twice, iOS native swipe only swallowed
  9  habits list keeps scroll position across re-render
 10  CodisTaskDrag: whole card is a handle (only real controls block), 140ms hold, mouse drags on move
 11  «محسوبة من سجل الاستخدام…» removed
 12  dismantle / pouch quantity sheet re-laid out (same ids, same logic)
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'id="codis-v33-css"' not in s, 'already applied'

def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:90])
    s = s.replace(old, new)
def many(old, new, minimum=1):
    global s
    n = s.count(old); assert n >= minimum, ('anchor missing', old[:90]); s = s.replace(old, new); print('  replaced', n, 'x', old[:50])
def between(a, b, new):
    global s
    i = s.index(a); j = s.index(b, i); s = s[:i] + new + s[j:]

# ------------------------------------------------------------------ art (room identities + status marks)
def svg(cls, body): return '<svg class="ea ea-%s" viewBox="0 0 132 92" aria-hidden="true" focusable="false">%s</svg>' % (cls, body)
BOOK_L = 'M66 22C54 15 34 15 14 20V70C34 65 54 65 66 72Z'; BOOK_R = 'M66 22C78 15 98 15 118 20V70C98 65 78 65 66 72Z'
ART = {
 'plan': svg('plan', '<rect class="sh" x="12" y="14" width="112" height="72" rx="10"/><rect class="pap" x="8" y="8" width="112" height="72" rx="10"/><path class="soft" d="M8 24h112M20 16h18M44 16h8"/>'
   '<rect class="accw rise d1" x="18" y="32" width="28" height="18" rx="4"/><path class="soft rise d2" d="M24 38h14M24 44h9"/>'
   '<path class="soft dash" d="M31 64C46 64 48 46 66 46S90 40 103 38"/><path class="acc route" pathLength="100" d="M31 64C46 64 48 46 66 46S90 40 103 38"/>'
   '<rect class="accf pop d1" x="27" y="60" width="8" height="8" rx="2.5"/><rect class="accf pop d2" x="62" y="42" width="8" height="8" rx="2.5"/>'
   '<path class="ink" d="M103 48V28"/><path class="accf flag" d="M103 28h14l-3.5 5 3.5 5h-14z"/>'),
 'ops': svg('ops', '<rect class="sh" x="30" y="18" width="76" height="68" rx="9"/><rect class="pap" x="26" y="14" width="76" height="68" rx="9"/><rect class="accw" x="48" y="8" width="32" height="12" rx="5"/>'
   '<rect class="soft dash" x="36" y="32" width="10" height="10" rx="3"/><path class="soft dash" d="M54 37h38"/><rect class="soft dash" x="36" y="48" width="10" height="10" rx="3"/><path class="soft dash" d="M54 53h30"/>'
   '<rect class="soft dash" x="36" y="64" width="10" height="10" rx="3"/><path class="soft dash" d="M54 69h34"/><g class="drop"><path class="acc" d="M117 22v28M110 43l7 7 7-7"/></g>'),
 'opsr': svg('opsr', '<rect class="sh" x="26" y="20" width="84" height="58" rx="8"/><rect class="pap" x="22" y="16" width="84" height="58" rx="8"/><path class="soft" d="M22 32h84M32 24h20"/>'
   '<rect class="soft dash" x="32" y="40" width="14" height="14" rx="4"/><path class="acc rise d1" d="M39 43.5v7M35.5 47h7"/><path class="soft dash" d="M54 47h40"/><path class="soft dash" d="M32 62h62"/>'),
 'opsd': svg('opsd', '<rect class="sh" x="24" y="16" width="84" height="62" rx="8"/><rect class="pap" x="20" y="12" width="84" height="62" rx="8"/><path class="soft" d="M32 30h44M32 42h54M32 54h34"/>'
   '<g class="stamp"><rect class="accw" x="54" y="42" width="58" height="38" rx="7"/><rect class="acc thin" x="59" y="47" width="48" height="28" rx="4"/><path class="acc stamp-chk" pathLength="100" d="M71 61l8 8 15-16"/></g>'),
 'lrn': svg('lrn', '<path class="pap" d="M66 8C56 3 40 3 24 6V40C40 37 56 37 66 43Z"/><path class="pap" d="M66 8C76 3 92 3 108 6V40C92 37 76 37 66 43Z"/><path class="soft" d="M34 16h22M34 24h18M76 16h22M76 24h16"/>'
   '<path class="soft dash" d="M66 46v12M28 70h76"/><rect class="accw pop d1" x="22" y="64" width="12" height="12" rx="3.5"/><rect class="accw pop d2" x="60" y="64" width="12" height="12" rx="3.5"/><rect class="soft dash" x="98" y="64" width="12" height="12" rx="3.5"/><path class="acc rise d3" d="M64.5 70l2.5 2.5 4-5"/>'),
 'lrnr': svg('lrnr', '<path class="sh" d="M70 26C58 19 38 19 18 24V74C38 69 58 69 70 76Z"/><path class="pap" d="%s"/><path class="pap" d="%s"/><path class="soft dash" d="M26 34h28M26 44h28M26 54h22"/>'
   '<path class="acc rise d1" d="M78 34h18"/><path class="soft dash" d="M78 44h18M78 54h14"/><path class="accf drop" d="M100 18v22l6-5 6 5V19z"/>' % (BOOK_L, BOOK_R)),
 'lrnd': svg('lrnd', '<path class="sh" d="M70 26C58 19 38 19 18 24V74C38 69 58 69 70 76Z"/><path class="pap" d="%s"/><path class="pap" d="%s"/><path class="soft" d="M26 34h28M26 44h28M26 54h22"/>'
   '<path class="acc stamp-chk" pathLength="100" d="M82 46l8 8 16-18"/><path class="ink" d="M66 22V6"/><path class="accf flag" d="M66 6h14l-3.5 5 3.5 5H66z"/>' % (BOOK_L, BOOK_R)),
}
def mark(k): return '<div class="es-mark es-art" aria-hidden="true">' + ART[k] + '</div>'
PLAIN_MARK = '<div class="es-mark"><svg viewBox="0 0 100 100" aria-hidden="true"><use href="#codis-mark"/></svg></div>'
assert s.count(PLAIN_MARK) == 3

# ---- Phase 3: three distinct empty states (ids + onclick handlers untouched)
once('''        ''' + PLAIN_MARK + '''
        <div class="es-title">ماكو خطة لهذا الأسبوع بعد</div>
        <div class="es-copy">اكتب اللي براسك، والباقي علينا.</div>
        <button type="button" class="btn btn-primary" onclick="startNewPlan()">إضافة خطة</button>''',
     '''        ''' + mark('plan') + '''
        <div class="es-title">ابدأ بناء خطة أسبوعك</div>
        <div class="es-copy">وزّع أهدافك على الأيام وارسم مسارك قبل ما يبدأ الأسبوع — والترتيب علينا.</div>
        <button type="button" class="btn btn-primary" onclick="startNewPlan()">ابدأ بناء الخطة</button>''')
once('''        ''' + PLAIN_MARK + '''
        <div class="es-title">ماكو خطة لهذا الأسبوع بعد</div>
        <div class="es-copy">اكتب اللي براسك، والباقي علينا.</div>
        <button type="button" class="btn btn-primary" onclick="goToPlanning('tasks')">''',
     '''        ''' + mark('ops') + '''
        <div class="es-title">العمليات بانتظار خطة</div>
        <div class="es-copy">أول ما تُبنى خطة الأسبوع تنزل مهامك هنا، فتنفّذها وتحسمها يوماً بيوم.</div>
        <button type="button" class="btn btn-primary" onclick="goToPlanning('tasks')">''')
once('''        ''' + PLAIN_MARK + '''
        <div class="es-title">ماكو خطة تعلم لهذا الأسبوع بعد</div>
        <div class="es-copy">اكتب اللي براسك، والباقي علينا.</div>''',
     '''        ''' + mark('lrn') + '''
        <div class="es-title">مسارك التعليمي لم يبدأ بعد</div>
        <div class="es-copy">حدّد محطاتك الدراسية في الخطة، وتظهر هنا درساً بعد درس لتتابع تقدّمك.</div>''')

# ---- Phase 6: status marks in the task / learn lists (celebrate-in-a-circle retired)
for txt, k, isl in [('أضف مهمة للبدء', 'opsr', 0), ('كل مهام اليوم محسومة', 'opsd', 0), ('أضف عنصراً للبدء', 'lrnr', 1), ('كل عناصر اليوم محسومة', 'lrnd', 1)]:
    once('<div class="es-mark">${ICONS.celebrate}</div><div class="es-copy">' + txt + '</div>', "${codisEsMark('" + k + "')}<div class=\"es-copy\">" + txt + '</div>')
import json
once('function codisTaskItemHtml(task, withHint){',
     '/* CODIS-V33: status marks for empty / cleared lists — vector art per room & state (replaces the circle + ICONS.celebrate) */\n'
     'function codisEsMark(k){ const A = ' + json.dumps({k: ART[k] for k in ('opsr', 'opsd', 'lrnr', 'lrnd')}, ensure_ascii=False) + '; return \'<div class="es-mark es-art" aria-hidden="true">\' + (A[k] || \'\') + \'</div>\'; }\n'
     'function codisTaskItemHtml(task, withHint){')

# ---- Phase 4 / 11 text removals
once('          <div class="settings-note">يُحفظ الاختيار على هذا الجهاز فقط.</div>\n', '')
i = s.index("'</ol>' +\n      '<p class=\"hx-note\">محسوبة من سجل الاستخدام المحفوظ")
j = s.index("', 'hx-top');", i)
s = s[:i] + "'</ol>" + s[j:]
assert 'محسوبة من سجل الاستخدام' not in s

# ---- blur: every source (tokens, chrome, stages, scrims)
many('--mat-chrome-blur:blur(18px) saturate(150%);', '--mat-chrome-blur:blur(8px) saturate(135%);', 1)
many('--mat-chrome-blur:blur(24px) saturate(170%);', '--mat-chrome-blur:blur(11px) saturate(140%);', 2)
many('blur(7px) saturate(.9)', 'blur(4px) saturate(.9)', 1)
many('blur(6px)', 'blur(3px)', 1)
many('--mat-chrome-fill:rgb(247 242 231 / .74);', '--mat-chrome-fill:rgb(247 242 231 / .82);', 1)

# ---- Phase 2: reward editor
EI = lambda n: "ICONS." + n
between('function econRewardEditor(prefix, it){', '/* السعر ثابت: تغيير الندرة أو القائمة', r"""function econRewardEditor(prefix, it){
  const d = it || { name:'', rarity:econCfg().rarities[0].id, weight:10, coinValue:null, storePrice:null, enabled:true, room:settingsRoom };
  const wOpen = d.weight !== 10, ic = k=>'<span aria-hidden="true">' + ICONS[k] + '</span>';
  return '<div class="eco-form rwe">' +
    '<div class="rwe-top">' +
      econField(ic('gift') + 'اسم المكافأة', '<input type="text" class="eco-txt" id="' + prefix + '-name" maxlength="120" value="' + escapeHtml(d.name) + '" placeholder="مثلاً: تطلب أكل تحبه">') +
      '<div class="rwe-f"><span class="rwe-lab">' + ic('sparkle') + 'الستيكر <em>اختياري</em></span>' + codisStickerRowHtml(prefix, d.stickerId) + '</div>' +
    '</div>' +
    '<div class="rwe-pair">' +
      '<div id="' + prefix + '-rarity-wrap"' + (d.room === 'learn' ? ' style="display:none;"' : '') + '>' + econField(ic('star') + 'الندرة', '<select class="eco-sel" id="' + prefix + '-rarity" onchange="econRewardRarityChanged(\'' + prefix + '\')">' + econRarityOptions().map(o=>'<option value="' + escapeHtml(o[0]) + '"' + (o[0] === d.rarity ? ' selected' : '') + '>' + escapeHtml(o[1]) + '</option>').join('') + '</select>') + '</div>' +
      econField(ic('clipboard-check') + 'القائمة', '<select class="eco-sel" id="' + prefix + '-room" onchange="econRewardRarityChanged(\'' + prefix + '\')">' + econRoomOptions().map(o=>'<option value="' + o[0] + '"' + (o[0] === d.room ? ' selected' : '') + '>' + o[1] + '</option>').join('') + '</select>') +
    '</div>' +
    '<p class="eco-note" id="' + prefix + '-hint">' + econRewardHintText(d.rarity, d.room) + '</p>' +
    '<div class="rwe-foot"><span class="eco-switch-row"><input type="checkbox" class="ios-switch" id="' + prefix + '-on" ' + (d.enabled ? 'checked' : '') + ' aria-label="مفعّلة"><span>مفعّلة</span></span>' +
      '<button type="button" class="rwe-more" aria-expanded="' + (wOpen ? 'true' : 'false') + '" onclick="var o=this.getAttribute(\'aria-expanded\')!==\'true\';this.setAttribute(\'aria-expanded\',o);this.closest(\'.rwe\').querySelector(\'.rwe-wt\').hidden=!o;">وزن الظهور<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button></div>' +
    '<div class="rwe-wt"' + (wOpen ? '' : ' hidden') + '>' + econField('وزن الظهور', '<input type="number" class="eco-num" id="' + prefix + '-weight" min="0" step="1" value="' + d.weight + '">', 'داخل نفس الندرة') + '</div></div>';
}
""")

# ---- Phase 9: habits keep scroll
once("  [[buildWrap, data.habits.build],[quitWrap, data.habits.quit]].forEach(([wrap, list])=>{\n    wrap.innerHTML = '';",
     "  const _sc = codisScrollerOf(buildWrap), _st = _sc.scrollTop, _wy = window.scrollY;   /* CODIS-V33: the re-render must not move the reader */\n"
     "  [[buildWrap, data.habits.build],[quitWrap, data.habits.quit]].forEach(([wrap, list])=>{\n    wrap.innerHTML = '';")
once("  codisJustChangedId = null;\n  updatePlanBar();   /* العادات اليومية جزء من شريط الأسبوع */",
     "  codisJustChangedId = null;\n  if(_sc.scrollTop !== _st) _sc.scrollTop = _st; if(window.scrollY !== _wy) window.scrollTo(0, _wy);\n"
     "  requestAnimationFrame(()=>{ if(Math.abs(_sc.scrollTop - _st) > 1) _sc.scrollTop = _st; });\n  updatePlanBar();   /* العادات اليومية جزء من شريط الأسبوع */")

# ---- Phase 10: task drag
once("const SLOP = 9, EDGE = 76, BLOCK = 'button, a, input, textarea, select, label, [contenteditable], .status-group, .task-meta, .tt-row, .task-partial';",
     "const SLOP = 8, EDGE = 76, BLOCK = 'button, a, input, textarea, select, label, [contenteditable], [role=\"slider\"], .tp-range';   /* v33: only real controls block — the whole card is a handle */")
once("p = { id:id, x:x, y:y, item:item, list:list, t:setTimeout(()=>begin(), e.pointerType === 'mouse' ? 260 : 380) };",
     "const mouse = e.pointerType === 'mouse';\n    p = { id:id, x:x, y:y, item:item, list:list, mouse:mouse, t:mouse ? 0 : setTimeout(()=>begin(), 140) };   /* touch: 140ms hold (scroll cancels it); mouse: drag on first move */")
once("if(p && !d && e.pointerId === p.id){ if(Math.hypot(e.clientX - p.x, e.clientY - p.y) > SLOP) clearP(); return; }",
     "if(p && !d && e.pointerId === p.id){ const mv = Math.hypot(e.clientX - p.x, e.clientY - p.y); if(p.mouse){ if(mv > 4) begin(); return; } if(mv > SLOP) clearP(); return; }")
once("st.item.style.transition = 'transform 190ms cubic-bezier(.22,1,.36,1)'; st.item.style.transform = 'translate3d(0,' + target + 'px,0)';\n    setTimeout(cb, 200);",
     "st.item.style.transition = 'transform 160ms cubic-bezier(.22,1,.36,1)'; st.item.style.transform = 'translate3d(0,' + target + 'px,0)';\n    setTimeout(cb, 170);")

# ---- Phase 8: back gesture
once("let lastBack = 0, busyDrag = false;",
     "let lastBack = 0, busyDrag = false, swipedAt = 0;\n  const iosBrowser = /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);   /* v33: there the browser's own back swipe (from the LEFT edge) is not an in-app back */")
once("lastBack = now;\n    try{ codisHaptic([8]); }catch(e){}", "lastBack = now; swipedAt = now;\n    try{ codisHaptic([8]); }catch(e){}")
once("    back();                                                   /* رجوع داخلي واحد (أو لا شيء في الغرف الرئيسية) */",
     "    if(!iosBrowser && Date.now() - swipedAt > 700) back();    /* v33: رجوع النظام (زر أندرويد) = رجوع داخلي واحد؛ سحب المتصفح الأصلي على iOS يُبتلع فقط؛ لا مضاعفة بعد سحبنا */")
once("  if(!nativeSwipe){\n    document.addEventListener('touchstart', e=>{", "  {   /* v33: the in-app swipe now exists everywhere — one direction only: right edge -> left */\n    document.addEventListener('touchstart', e=>{")
once("side = t.clientX <= b.left + EDGE ? 'l' : (t.clientX >= b.right - EDGE ? 'r' : '');", "side = t.clientX >= b.right - EDGE ? 'r' : '';")

# ---- Phase 12: dismantle / pouch sheet markup (ids unchanged)
once("""'<div class="dq-stage is-qty" id="dq-stage"><div class="dq-stack" id="dq-stack"></div>""", """'<div class="dq-top"><div class="dq-stage is-qty" id="dq-stage"><div class="dq-stack" id="dq-stack"></div>""")
once("""'<div class="dq-stage is-qty" id="dq-stage"><div class="pch-art is-big">""", """'<div class="dq-top"><div class="dq-stage is-qty" id="dq-stage"><div class="pch-art is-big">""")
many("""<span class="dq-count-of" id="dq-of"></span></div>'""", """<span class="dq-count-of" id="dq-of"></span></div></div>'""", 2)
once("dqHold(s.kind === 'pouch' ? 470 : 0);", "dqHold(s.kind === 'pouch' ? 470 : 400);")

# ---- stylesheet + touch script
css = open(os.path.join(HERE, 'identity', 'v33.css'), encoding='utf-8').read()
assert '</style' not in css and '<!--' not in css
js = r"""<script>
/* CODIS-V33: long-press on content must not open the browser's selection / image menu (inputs and editable text keep theirs) */
document.addEventListener('contextmenu', function(e){
  var t = e.target && e.target.nodeType === 1 ? e.target : e.target && e.target.parentElement;
  if(!t || !t.closest || t.closest('input, textarea, [contenteditable]:not([contenteditable="false"]), .sel-ok')) return;
  try{ if(window.matchMedia('(pointer: coarse)').matches) e.preventDefault(); }catch(x){}
});
document.addEventListener('selectstart', function(e){
  var t = e.target && e.target.nodeType === 1 ? e.target : e.target && e.target.parentElement;
  if(t && t.closest && !t.closest('input, textarea, [contenteditable]:not([contenteditable="false"]), .sel-ok')){ try{ if(window.matchMedia('(pointer: coarse)').matches) e.preventDefault(); }catch(x){} }
});
</script>
"""
once('<script>\n/* CODIS-THEME — two looks, one app.', '<style id="codis-v33-css">\n' + css + '</style>\n' + js + '<script>\n/* CODIS-THEME — two looks, one app.')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v33 ok', len(s))
