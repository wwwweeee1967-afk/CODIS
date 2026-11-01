#!/usr/bin/env python3
"""CODIS-PEEK-ALL (3.11.1، بعد patch_v18.py): معاينة الضغط المطوّل تشمل كل عنصر بالمتجر لا الكروت فقط — البكجات، المظاهر، بطاقات العطلة،
 كروت المكافآت، وما بحوزتك — وأي عنصر يُضاف مستقبلاً تلقائياً، لأن القاعدة بنيوية: كل ابن مباشر لقائمة [role="list"] داخل #eco-store-body.
 لا يبدأ الضغط من أزرار الإجراء (.btn / .chip-act / الحقول / الروابط) فقط، فيصلح حتى لو كان الرسم نفسه زراً (bx-open).
 العنصر يُنقل بسلسلة آبائه الحقيقية كأغلفة display:contents فتبقى كل أنماطه المعتمدة على الآباء كما هي، وأزرار الإجراء تُخفى بالمعاينة.
 الاستعمال: py -3 tools/patch_v19.py <in> <out>"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-PEEK-ALL' in s: sys.exit('already patched (CODIS-PEEK-ALL)')
if 'CODIS-TIMERS' not in s: sys.exit('needs patch_v18.py first')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

rep("""    const card = e.target.closest && e.target.closest('#eco-store-body .shop-card'); if(!card || !card.querySelector('.cflip') || card.classList.contains('is-selectable')) return;
    if(e.target.closest('button, a, input, select, textarea')) return;""",
    """    /* CODIS-PEEK-ALL: أي عنصر بالمتجر = ابن مباشر لقائمة داخل المتجر (الحالي والمستقبلي)؛ أزرار الإجراء وحدها لا تبدأ المعاينة */
    const card = e.target.closest && e.target.closest('#eco-store-body [role="list"] > *');
    if(!card || card.classList.contains('is-selectable') || card.classList.contains('peek-ph') || card.getBoundingClientRect().height < 40) return;
    if(e.target.closest('.btn, .chip-act, input, select, textarea, a[href]')) return;""", 'peek target')
rep("""    ov.querySelector('.peek-host').appendChild(card);""",
    """    /* سلسلة الآباء الحقيقية حتى المتجر كأغلفة بلا صندوق: الأنماط المعتمدة على الآباء (.bx-grid .bx-card …) تبقى كما هي */
    let host = ov.querySelector('.peek-host'); const chain = [];
    for(let n = ph.parentElement; n && n.id !== 'eco-store-body' && n !== document.body; n = n.parentElement) chain.unshift(n);
    chain.forEach(a=>{ const w = document.createElement('div'); w.className = a.className; w.style.display = 'contents';
      Array.prototype.forEach.call(a.attributes, at=>{ if(/^(data-|role$)/.test(at.name)) w.setAttribute(at.name, at.value); }); host.appendChild(w); host = w; });
    host.appendChild(card);""", 'peek host chain')
rep(".peek-host{ position:static; }", ".peek-host{ display:contents; }", 'host css')
rep(""".peek .shop-card.is-peek{ transform-origin:50% 50%; will-change:transform; filter:drop-shadow(0 26px 40px rgba(0,0,0,.55)); }
.peek .shop-card.is-peek .store-meta, .peek .shop-card.is-peek .shop-acts, .peek .shop-card.is-peek .st-cap{ visibility:hidden; }""",
    """.peek .is-peek{ transform-origin:50% 50%; will-change:transform; filter:drop-shadow(0 26px 40px rgba(0,0,0,.55)); }
/* CODIS-PEEK-ALL: المعاينة للعرض — أزرار الشراء/البيع/الاستخدام تُخفى (المسافة تبقى فلا يتغيّر الشكل) */
.peek .is-peek :is(.btn, .chip-act, .own-pick){ visibility:hidden; }""", 'peek css')
rep('<p class="peek-hint">اضغط البطاقة لتنقلب · اضغط خارجها للرجوع</p>', '<p class="peek-hint">\' + (card.querySelector(\'.cflip\') ? \'اضغط البطاقة لتنقلب · \' : \'\') + \'اضغط خارجها للرجوع</p>', 'hint')
rep("<!-- CODIS-TIMERS -->", "<!-- CODIS-TIMERS -->\n<!-- CODIS-PEEK-ALL -->", 'marker')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('CODIS-PEEK-ALL applied')
