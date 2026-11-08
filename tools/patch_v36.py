"""CODIS-USE-CINE (3.23.0) — مشهد استخدام المكافأة المملوكة (عرض فقط) + محرّك العبارات CodisRewardVoice.

  py -3 tools/patch_v36.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (بعد patch_v35؛ ثم set_version.py 3.23.0)

  • tools/identity/v36_voice.js — CodisRewardVoice (فهم الاسم وصياغة العبارة، محلي) · v36.js — CodisUseCine (المشهد) · v36.css
  • econUse: بعد نجاح markUsed / بدء المؤقت فقط يُستدعى CodisUseCine.play؛ فشله ← التنبيه القديم. لا يمسّ CodisBuyCine ولا الشراء/البيع.
  • CodisBuyCine.useNow (زر «استخدام» بمشهد الشراء): بعد النجاح يُغلق مشهد الشراء ثم يُشغَّل مشهد الاستخدام (حركة الشراء نفسها لم تُمس).
  • codisBackLayer: الرجوع يغلق المشهد أولاً.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-USE-CINE' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:110])
    s = s.replace(old, new)

anchor = '/* — مشهد الشراء: يُشغَّل بعد نجاح CodisEconomy.purchase فقط'
once(anchor, rd('v36_voice.js').rstrip() + '\n\n' + rd('v36.js').rstrip() + '\n\n' + anchor)

# timed reward: scene only when the timer really started (rt.ok) — the old toast stays as the fallback
once("      if(rt.ok){ codisSfx('confirm', { ctx:'use' }); showToast('بدأ المؤقت: ' + CodisDuration.label(_dur.min), 'var(--success)', 'check'); CodisPush.nudge(); }",
     "      if(rt.ok){ codisSfx('confirm', { ctx:'use' }); CodisPush.nudge(); let _pl = false; try{ _pl = CodisUseCine.play(_sn, { timed:true, dur:_dur }); }catch(e){} if(!_pl) showToast('بدأ المؤقت: ' + CodisDuration.label(_dur.min), 'var(--success)', 'check'); }   /* CODIS-USE-CINE */")
once("    const _dur = CodisDuration.parse(it.name);\n    if(_dur){   /* CODIS-TIMERS",
     "    const _dur = CodisDuration.parse(it.name), _sn = CodisUseCine.snap(it);   /* CODIS-USE-CINE: لقطة العرض قبل أي تغيير بالحالة */\n    if(_dur){   /* CODIS-TIMERS")
once("    if(r.ok){ codisSfx('confirm', { ctx:'use' }); showToast('انسجّلت كمستخدَمة', 'var(--success)', 'check'); }",
     "    if(r.ok){ codisSfx('confirm', { ctx:'use' }); let _pl = false; try{ _pl = CodisUseCine.play(_sn, { timed:false }); }catch(e){} if(!_pl) showToast('انسجّلت كمستخدَمة', 'var(--success)', 'check'); }   /* CODIS-USE-CINE */")
once("  if(CodisBuyCine.isOpen()) return { act:CodisBuyCine.keep, el:CodisBuyCine.el() };",
     "  if(CodisUseCine.isOpen()) return { act:CodisUseCine.dismiss, el:CodisUseCine.el() };   /* CODIS-USE-CINE */\n  if(CodisBuyCine.isOpen()) return { act:CodisBuyCine.keep, el:CodisBuyCine.el() };")

# purchase scene «استخدام» (CodisBuyCine.useNow): after success, close the purchase scene then play the use scene (purchase animation itself untouched)
once("""    const uid = s.uid, it = CodisInventory.get(uid); let ok = false, msg = 'هذي المكافأة ما عدت بحوزتك';
    if(it && it.status === 'owned'){
      const d = CodisDuration.parse(it.name);""",
     """    const uid = s.uid, it = CodisInventory.get(uid); let ok = false, msg = 'هذي المكافأة ما عدت بحوزتك', _sn = null, _d = null;   /* CODIS-USE-CINE */
    if(it && it.status === 'owned'){
      const d = CodisDuration.parse(it.name); _sn = CodisUseCine.snap(it); _d = d;""")
once("""    close(()=>{ try{ econRenderAll(); }catch(e){} showToast(msg, ok ? 'var(--success)' : 'var(--warning)', ok ? 'check' : undefined); });
  }
  return { play:play, keep:keep,""",
     """    close(()=>{ try{ econRenderAll(); }catch(e){} let _pl = false; if(ok && _sn){ try{ _pl = CodisUseCine.play(_sn, { timed:!!_d, dur:_d }); }catch(e){} } if(!_pl) showToast(msg, ok ? 'var(--success)' : 'var(--warning)', ok ? 'check' : undefined); });   /* CODIS-USE-CINE */
  }
  return { play:play, keep:keep,""")

css = rd('v36.css'); assert '</style' not in css
i = s.index('<style id="codis-v35-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v36-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v36 ok', len(s))
