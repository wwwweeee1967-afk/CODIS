"""CODIS-ATELIER (3.19.0) — new visual identity: aged paper · iron-gall ink · real glass.

  py -3 tools/patch_v32.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (after patch_v31 / build_* / set_version)

VISUAL LAYER ONLY. No ID / class / data-attribute / handler / ARIA / JS logic is renamed or removed.
  1. :root colour + material tokens are rewritten (one source of truth stays one source of truth).
  2. tools/identity/engine.py re-materialises every hard-coded colour of the stylesheet IN PLACE by role
     (text → ink, hairline → ink, fill → raised paper / ink tint, highlight → paper light, drop → umber).
  3. Card art and the cinematic stages (reveal, purchase, box ritual, aura, peek) keep the Obsidian look: their
     rules are skipped and their containers get the original dark tokens back (STAGE scope).
  4. Room personalities + material rules are added inside each room's own section (tools/identity/*.css).
  5. Head: theme-color / color-scheme / status bar / favicon + touch icon follow the paper identity.
  6. CODIS-THEME: both looks ship. The live <style id="codis-theme-css"> carries paper; the ORIGINAL stylesheet rides inert in
     <script type="text/plain" id="codis-css-dark"> and is swapped in by CodisTheme (tools/identity/theme_boot.js) from a new
     Settings > المظهر page. Font (Momken, the only typeface) + the appearance-page styles live in one shared <style id="codis-shared-css">.
Backup of the pre-identity build: backups/before_atelier/."""
import re, sys, os, base64
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'identity'))
import engine

src, dst = sys.argv[1], sys.argv[2]
html = open(src, encoding='utf-8').read()
assert '<!-- CODIS-ATELIER -->' not in html, 'already applied'

def once(s, old, new):
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:80])
    return s.replace(old, new)

def read(name): return open(os.path.join(HERE, 'identity', name), encoding='utf-8').read()

css_a = html.index('<style>') + len('<style>')
css_b = html.index('</style>', css_a)
css = html[css_a:css_b]
orig_css = css                      # the 3.18.0 stylesheet, untouched = the "dark" look

# ---------------------------------------------------------------- 1. tokens
tok_a = css.index('  color-scheme: dark;')
tok_b = css.index('  --text-3:#858E9D;') + len('  --text-3:#858E9D;')
old_tokens = css[tok_a:tok_b]
GRAIN = open(os.path.join(HERE, 'identity', 'grain.b64')).read().strip()
new_tokens = read('tokens.css').replace('__GRAIN__', GRAIN).rstrip()
css = css[:tok_a] + new_tokens + css[tok_b:]

# the dark stage scope = the original Obsidian tokens, verbatim
dark = '\n'.join(l for l in old_tokens.split('\n') if l.strip() and not l.strip().startswith('color-scheme'))

# ---------------------------------------------------------------- 2. engine
STAGE_TOK = r'(?:#outcome-overlay|#codis-aura|\.bcx|\.peek\b|\.bk-zoom|\.rwc|\.cbk|\.rvx|\.rv\b|\.pcd|\.scx|\.pnr|\.pnc|\.pn-|\.wkc|\.mwc|\.mtc|\.pwc|\.cb-|\.bk-|\.ca-|\.cflip|\.fz-|\.bx-(?:stage|reveal|sr\b|art|rit|lid|body|world|fx|flash|beam|glow|cine|burst)|\.bxa|\.blk-|\.bulk|\.outcome-|\.dq-rit|\.cine)'
STAGE_RE = re.compile(r'(^|[\s,>+~(])' + STAGE_TOK)
KF_STAGE = re.compile(r'^(bcx|rvx|rv|cb|bk|bx|bulk|blk|cine|ca|aura|cbk|cflip|pn|pc|fz|outcome|codisAura|startup|cs)', re.I)
def skip(sel, kf):
    if kf: return bool(KF_STAGE.match(sel or ''))
    parts = [p.strip() for p in engine.split_top(sel) if p.strip()]
    if not parts: return False
    if parts[0].startswith(':root') and 'color-scheme' in sel: return True
    return all(STAGE_RE.search(' ' + p) for p in parts)

root_end = css.index('}', css.index(':root{')) + 1      # the token rule itself is hand-written: never auto-mapped
css = css[:root_end] + engine.walk(css[root_end:], skip) + ''

# ---------------------------------------------------------------- 3 + 4. scoped stage tokens and identity layers
STAGE_SEL = '#outcome-overlay, #codis-aura, .bcx, .peek, .bk-zoom, .rwc, .cbk, .pcd, .scx, .cb-world, .bk-world, .shop-card .cflip'
stage_rule = ('/* CODIS-ATELIER · dark stages keep the Obsidian material: card art and cinematics are lit scenes, not paper. */\n'
              + STAGE_SEL + '{\n  color-scheme:dark;\n' + dark + '\n  --ink-rgb:var(--hi-rgb); --lite-rgb:var(--hi-rgb);\n}\n'
              + '.bx-card .bx-info, .bx-own-tile .bx-info{ color:rgb(251 247 238 / .9); }\n'
              + ':is(' + STAGE_SEL + ') .btn-secondary{ background:linear-gradient(180deg, rgb(var(--hi-rgb) / .1), rgb(var(--hi-rgb) / .05)); color:var(--text); border-color:rgb(var(--hi-rgb) / .2); box-shadow:inset 0 1px 0 rgb(var(--hi-rgb) / .14); text-shadow:none; }\n')

def fill(text):
    text = text.replace('__GRAIN__', GRAIN)
    for k in set(re.findall(r'__([A-Z]+)__', text)):
        text = text.replace('__%s__' % k, read('_%s.txt' % k.lower()).rstrip('\n'))
    return text

# Each layer closes the section it belongs to: it is inserted right before the header comment of the NEXT section,
# so it follows (and refines) that section's own rules instead of piling up at the end of the stylesheet.
inserts = [
    ('/* ===================== RESPONSIVE ===================== */', 'global.css'),       # after base components
    ('OPERATIONS ROOM — غرفة العمليات', 'room_planning.css'),
    ('LEARNING ROOM — غرفة الأستاذ', 'room_ops.css'),
    ('DISCIPLINE ROOM — غرفة التأديب', 'room_learn.css'),
    ('APP LOCK — قفل التطبيق (اختياري)', 'room_discipline.css'),
    ('NAVIGATION — the discipline room\'s dock button', 'lock.css'),
    ('/* ===================== REWARD ECONOMY ===================== */', 'room_settings.css'),
    ('/* ===================== PHONE FRAME =====================', 'store.css'),
]
for marker, f in inserts:
    p = os.path.join(HERE, 'identity', f)
    if not os.path.exists(p): continue
    assert css.count(marker) == 1, (marker, css.count(marker))
    at = css.index(marker)
    if not marker.startswith('/*'): at = css.rindex('/*', 0, at)          # back up to the section's header comment
    block = '/* ==== CODIS-ATELIER · ' + f + ' ==== */\n' + fill(read(f)).rstrip() + '\n'
    css = css[:at] + block + css[at:]
css = css.rstrip() + '\n' + stage_rule

def b64(path): return base64.b64encode(open(os.path.join(HERE, '..', 'assets', 'fonts', path), 'rb').read()).decode()
shared = read('shared.css').replace('__MOMKEN__', b64('Momken-Regular.woff2'))
assert '</script' not in orig_css.lower() and '<!--' not in orig_css, 'dark css cannot ride inside a script tag'
html = (html[:css_a - len('<style>')]
        + '<style id="codis-theme-css">' + css + '</style>\n'
        + '<script type="text/plain" id="codis-css-dark">' + orig_css + '</script>\n'
        + '<style id="codis-shared-css">\n' + shared.rstrip() + '\n</style>\n'
        + '<script>\n' + read('theme_boot.js').rstrip() + '\n</script>'
        + html[css_b + len('</style>'):])
html = once(html, '        <div role="group" aria-label="الأمان">', read('appearance_home.html') + '        <div role="group" aria-label="الأمان">')
html = once(html, '    <!-- ============ قسم: الصوت ============ -->', read('appearance_page.html') + '    <!-- ============ قسم: الصوت ============ -->')

# ---------------------------------------------------------------- 5. head
html = once(html, '<!DOCTYPE html>\n', '<!DOCTYPE html>\n<!-- CODIS-ATELIER -->\n')
html = once(html, '<meta name="theme-color" content="#05070B">', '<meta name="theme-color" content="#E9E0CD">')
html = once(html, '<meta name="color-scheme" content="dark">', '<meta name="color-scheme" content="light">')
html = once(html, '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">', '<meta name="apple-mobile-web-app-status-bar-style" content="default">')
ICON = read('favicon.svg').strip() if os.path.exists(os.path.join(HERE, 'identity', 'favicon.svg')) else None
if ICON:
    m = re.search(r'<link rel="icon" href="data:image/svg\+xml,[^"]*">', html)
    from urllib.parse import quote
    html = html[:m.start()] + '<link rel="icon" href="data:image/svg+xml,' + quote(ICON, safe=" /=:'") + '">' + html[m.end():]
PNG = os.path.join(HERE, 'identity', 'touch_icon.png')
if os.path.exists(PNG):
    m = re.search(r'<link rel="apple-touch-icon" href="data:image/png;base64,[^"]*">', html)
    html = html[:m.start()] + '<link rel="apple-touch-icon" href="data:image/png;base64,' + base64.b64encode(open(PNG, 'rb').read()).decode() + '">' + html[m.end():]
JS = os.path.join(HERE, 'identity', 'js_patches.py')
if os.path.exists(JS):
    ns = {'once': once}; exec(open(JS, encoding='utf-8').read(), ns); html = ns['apply'](html)

open(dst, 'w', encoding='utf-8', newline='').write(html)
print('CODIS-ATELIER applied ->', dst, len(html))
