#!/usr/bin/env python3
"""CODIS-PLANCARD (بعد patch_v13.py): ترتيب بطاقة الخطة الشغّالة بتسلسل أهمية واضح.
 قبل: أربعة أزرار بحجم متقارب (أضف · احفظ · إيقاف · خطة جديدة) فوق بعض.
 بعد: ترويسة (الاسم + الملخص) ← نسبة الإنجاز ← زر رئيسي واحد «أضف للخطة» ← ثلاثة إجراءات ثانوية هادئة بصف واحد (احفظ · خطة جديدة · إيقاف) والإيقاف بلون التحذير فقط."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-PLANCARD' in s: sys.exit('already patched (CODIS-PLANCARD)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

rep("""        <div class="plan-tools">
          <button type="button" class="btn btn-secondary" onclick="startExtendPlan()"><svg data-icon="next" data-size="md"></svg>أضف للخطة</button>
          <button type="button" class="btn btn-secondary" onclick="openSaveActivePlan()">احفظ الخطة</button>
        </div>""",
"""        <div class="plan-cta">
          <button type="button" class="btn btn-primary" onclick="startExtendPlan()"><svg data-icon="next" data-size="md"></svg>أضف للخطة</button>
        </div>""", 'cta')
rep("""        <div class="plan-actions">
          <button type="button" class="btn btn-destructive" onclick="stopCurrentPlan()">إيقاف الخطة</button>
          <button type="button" class="btn btn-primary" onclick="startNewPlanFromActive()">سوي خطة جديدة</button>
        </div>""",
"""        <div class="plan-more" role="group" aria-label="إجراءات الخطة">
          <button type="button" class="pm-btn" onclick="openSaveActivePlan()">احفظ الخطة</button>
          <button type="button" class="pm-btn" onclick="startNewPlanFromActive()">خطة جديدة</button>
          <button type="button" class="pm-btn is-danger" onclick="stopCurrentPlan()">إيقاف الخطة</button>
        </div>""", 'more')
css = r"""
/* CODIS-PLANCARD */
#planning-active .plan-cta{ padding:0 var(--pl-pad, 16px); }
#planning-active .plan-cta .btn{ width:100%; min-height:52px; display:inline-flex; align-items:center; justify-content:center; gap:8px; font-size:16px; font-weight:800; }
#planning-active .plan-cta .btn svg{ width:18px; height:18px; }
#planning-active .plan-save-active{ padding:var(--sp-md, 12px) var(--pl-pad, 16px) 0; }
#planning-active .plan-more{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:4px; margin:var(--sp-md, 12px) var(--pl-pad, 16px) var(--pl-pad, 16px); padding-top:var(--sp-md, 12px); border-top:1px solid rgb(var(--hi-rgb) / .08); }
#planning-active .pm-btn{ min-height:44px; padding:0 6px; border:0; border-radius:12px; background:none; color:var(--text-2); font:inherit; font-size:13.5px; font-weight:600; cursor:pointer; -webkit-tap-highlight-color:transparent; white-space:nowrap; }
#planning-active .pm-btn:active{ background:rgb(var(--hi-rgb) / .08); }
#planning-active .pm-btn:focus-visible{ outline:2px solid var(--aqua); outline-offset:-2px; }
#planning-active .pm-btn.is-danger{ color:rgba(255,138,130,.92); }
@media (hover:hover){ #planning-active .pm-btn:hover{ background:rgb(var(--hi-rgb) / .06); } #planning-active .pm-btn.is-danger:hover{ background:var(--danger-a12); } }
"""
rep("</style>", css + "</style>", 'css')
s = s.replace('<!-- CODIS-PLAN-EXTEND -->', '<!-- CODIS-PLAN-EXTEND -->\n<!-- CODIS-PLANCARD -->', 1)
if 'CODIS-PLANCARD -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v14 OK')
