"""CODIS-AUDIT-V38 (3.25.0) — engineering audit fixes (see docs/AUDIT_REPORT.md).

  py -3 tools/patch_v38.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (after patch_v37; then set_version.py 3.25.0)

  • Content-Security-Policy + referrer policy (defence in depth: no foreign scripts/objects/<base>, data only to self + *.supabase.co)
  • viewport: zoom allowed (WCAG 1.4.4) + iOS-only 16px form controls (no Safari focus-zoom) — tools/identity/v38.css
  • narrow phones (< 360px): room labels in the bottom bar wrap the same way
  • CodisTabGuard: two tabs no longer overwrite each other (proven data loss before)
  • dead code proven unused by ESLint scope analysis: errMsg (superseded by httpErr), prim, D/W/MO
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-AUDIT-V38' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:110])
    s = s.replace(old, new)

CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; "
       "font-src 'self' data:; connect-src 'self' https://*.supabase.co wss://*.supabase.co; worker-src 'self'; manifest-src 'self'; "
       "media-src 'self' data: blob:; object-src 'none'; base-uri 'self'; form-action 'self'")
once('<meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">',
     '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
     '<!-- CODIS-AUDIT-V38: defence-in-depth CSP. inline is required (single-file app + dev add-on); everything external is blocked except Supabase (data) and https images (Google avatar). -->\n'
     '<meta http-equiv="Content-Security-Policy" content="' + CSP + '">\n'
     '<meta name="referrer" content="strict-origin-when-cross-origin">')

# dead code (ESLint no-unused-vars, verified: no other reference in its scope)
once("  async function errMsg(r){ try{ const j = await r.json(); return j.message || j.msg || j.error_description || j.error || ('HTTP ' + r.status); }catch(e){ return 'HTTP ' + r.status; } }\n", "")
for line in ["const prim = v=>v === null || typeof v !== 'object';", "const D = 'd', W = 'w', MO = 'm';"]:
    i = s.index(line); assert s.count(line) == 1
    ls = s.rfind('\n', 0, i) + 1; le = s.index('\n', i) + 1
    assert s[ls:i].strip() == '' and s[i + len(line):le].strip() == '', ('not a whole line', line)
    s = s[:ls] + s[le:]

# multi-tab data guard (CodisTabGuard): proven data loss with two tabs → newest writer wins, stale tab stops saving/syncing and reloads
once("function codisSfx(name, opts){ try{ return CodisAudio.play(name, opts); }catch(e){ return false; } }",
     "function codisSfx(name, opts){ try{ return CodisAudio.play(name, opts); }catch(e){ return false; } }" + chr(10) + rd('v38.js').rstrip())

css = rd('v38.css'); assert '</style' not in css
i = s.index('<style id="codis-v37-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v38-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v38 ok', len(s))
