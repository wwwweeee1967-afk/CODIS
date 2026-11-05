"""CODIS-ATELIER — stylesheet re-materialiser (dark Obsidian glass → paper · ink · real glass).

Walks every CSS rule of the app stylesheet and rewrites colour VALUES in place, by the role the colour plays:
  text  (color / fill / stroke …)      → warm ink
  line  (border / outline …)           → ink hairline
  shadow(box-shadow / text-shadow …)   → highlights stay light, rings become ink, drops become soft umber
  fill  (background …)                 → raised paper (lighter) at rest, ink tint for pressed / hovered / selected
Selectors, properties, order, IDs, classes and every non-colour value are left untouched, so every JS contract survives.
Rules that live inside a dark *stage* (card art, reveal / box / purchase cinematics) are skipped; they get the original
Obsidian tokens back through a scoped token rule (see STAGE in patch_v32.py)."""
import re, colorsys

INK = (52, 42, 32)        # warm iron-gall ink
LITE = (251, 247, 238)    # paper highlight (never pure white)
UMBER = (74, 54, 34)      # shadow colour on paper
TEAL = (47, 122, 116)     # signal (verdigris ink)
BRASS = (154, 110, 34)

TEXT_P = ('color', '-webkit-text-fill-color', 'caret-color', 'fill', 'stroke', 'text-decoration-color', 'text-emphasis-color', 'accent-color')
LINE_P = ('border', 'outline', 'column-rule')
SHADOW_P = ('box-shadow', 'text-shadow', 'filter', '-webkit-filter')
SKIP_P = ('mask', '-webkit-mask', 'mask-image', '-webkit-mask-image', 'mask-box-image', 'content', 'font', 'font-family', 'transition', 'animation', 'will-change')

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def fa(a):
    s = ('%.3f' % a).rstrip('0').rstrip('.')
    if s.startswith('0.'): s = s[1:]
    return s or '0'
def rgb_css(c, a=1.0):
    r, g, b = [int(round(v)) for v in c]
    return 'rgb(%d %d %d)' % (r, g, b) if a >= .999 else 'rgb(%d %d %d / %s)' % (r, g, b, fa(a))
def var_css(ch, a): return 'rgb(var(--%s-rgb) / %s)' % (ch, fa(clamp(a)))

def hls(c): return colorsys.rgb_to_hls(*[v / 255 for v in c])
def from_hls(h, l, s): return tuple(v * 255 for v in colorsys.hls_to_rgb(h, clamp(l), clamp(s)))

def role_of(prop, sel):
    p = prop.lower()
    if p.startswith('--'):
        if re.search(r'hair|rule|tick|edge|border|line|dot|sep|stroke|ring', p): return 'line'
        if re.search(r'shadow|glow', p): return 'shadow'
        if re.search(r'(^|-)(ink|fg|text|c)$|color|-c-|ico-c', p): return 'text'
        return 'fill'
    if p in TEXT_P: return 'text'
    if p.startswith(LINE_P): return 'line'
    if p in SHADOW_P: return 'shadow'
    return 'fill'

PRESSY = re.compile(r':active|:hover|\.active\b|\.is-on\b|\.is-sel|\.sel\b|\[aria-(selected|pressed|checked|current)|:checked|\.on\b|\.current\b|:focus')

def is_neutral(c):
    h, l, s = hls(c)
    return s < .22 or l < .10 or l > .93 or (l < .24 and s < .5) or (l > .82 and s < .45)

def map_literal(c, a, role, ctx):
    """ctx: 'hl' highlight shadow, 'ring', 'drop', 'thin', 'press', ''"""
    h, l, s = hls(c)
    if is_neutral(c):
        light = l >= .5
        if role == 'text':
            return rgb_css(from_hls(.09, .16 + (1 - l) * .5, .22), max(a, .6) if a < 1 else 1)
        if role == 'shadow':
            if ctx == 'hl': return rgb_css(LITE, clamp(a * (2.2 if light else 1.2), .25, .95))
            if ctx == 'ring': return rgb_css(INK, clamp(a * 1.3, .06, .3))
            if light: return rgb_css(LITE, clamp(a * 1.5, 0, .7))      # light glow → paper light
            return rgb_css(UMBER, clamp(a * .42, .03, .3))
        if role == 'line':
            if light: return rgb_css(INK, clamp(a * 1.35, .06, .4))
            return rgb_css(INK, clamp(a * .35 + .08, .06, .3))         # dark line on dark → soft ink hairline
        # fill
        if light:
            if ctx in ('press', 'thin'): return rgb_css(INK, clamp(a * 1.25, .04, .3))
            if a >= .9: return rgb_css((250, 246, 237))
            return rgb_css(LITE, clamp(a * 7.5, .2, .85))
        # dark fill → paper (dark opaque surfaces become raised paper; translucent darks become ink wells)
        if a >= .55:
            pl = .955 - l * .55
            return rgb_css(from_hls(.11, pl, .38), a)
        return rgb_css(INK, clamp(a * .28, .03, .2))
    # saturated
    if .44 <= h <= .56:   # aqua / cyan signal → verdigris
        base = hls(TEAL)
        if role == 'text': return rgb_css(from_hls(base[0], .20, .50), a)
        if role == 'shadow' and ctx == 'hl': return rgb_css(LITE, clamp(a * 1.5, .2, .9))
        nl = clamp(base[1] + (l - .6) * .5, .22, .62)
        return rgb_css(from_hls(base[0], nl, .44), a)
    if .08 <= h <= .15 and s > .35:   # gold / amber
        if role == 'text': return rgb_css(from_hls(.105, .21, .78), a)
        return rgb_css(from_hls(.105, clamp(l * .82, .25, .7), min(s, .62)), a)
    if role == 'text' and l > .5:
        return rgb_css(from_hls(h, .36, min(s, .55)), a)
    if role == 'shadow' and a < .6:
        return rgb_css(from_hls(h, clamp(l * .85), s * .8), a * .65)
    if role in ('fill', 'line') and a >= .6 and l > .62:
        return rgb_css(from_hls(h, l * .82, s * .78), a)
    return rgb_css(from_hls(h, l, s * .86), a)

def map_var(ch, a, role, ctx):
    if ch == 'hi':
        if role == 'text': return var_css('ink', max(a, .55))
        if role == 'line': return var_css('ink', clamp(a * 1.4, .05, .38))
        if role == 'shadow':
            if ctx == 'hl': return var_css('lite', clamp(a * 8, .35, .95))
            if ctx == 'ring': return var_css('ink', clamp(a * 1.4, .05, .3))
            return var_css('lite', clamp(a * 4, .1, .6))
        if ctx in ('press', 'thin'): return var_css('ink', clamp(a * 1.2, .03, .3))
        return var_css('lite', clamp(a * 9, .18, .82))
    # lo channel
    if role == 'shadow': return var_css('lo', clamp(a * .4, .03, .32))
    if role == 'text': return var_css('ink', max(a, .6))
    if role == 'line': return var_css('ink', clamp(a * .5, .05, .3))
    return var_css('ink', clamp(a * .2, .025, .14))

HEX = re.compile(r'#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b')
FUNC = re.compile(r'rgba?\(\s*([^()]*?)\s*\)')
VARC = re.compile(r'rgba?\(\s*var\(--(hi|lo)-rgb\)\s*(?:/|,)\s*([\d.]+)\s*\)')
URL = re.compile(r'url\((?:[^()"\']|"[^"]*"|\'[^\']*\')*\)')

def parse_func(body):
    nums = re.split(r'[\s,/]+', body.strip())
    if len(nums) < 3 or any(not re.match(r'^[\d.]+%?$', n) for n in nums[:4] if n): return None
    try:
        r, g, b = [float(n) for n in nums[:3]]
        a = nums[3] if len(nums) > 3 else '1'
        a = float(a[:-1]) / 100 if a.endswith('%') else float(a)
        return (r, g, b), a
    except ValueError: return None

def split_top(v, ch=','):
    out, d, cur = [], 0, ''
    for x in v:
        if x == '(': d += 1
        elif x == ')': d -= 1
        if x == ch and d == 0: out.append(cur); cur = ''
        else: cur += x
    out.append(cur); return out

def shadow_ctx(part):
    p = part.strip()
    inset = 'inset' in p
    nums = re.findall(r'(-?[\d.]+)(px)?', re.sub(r'rgba?\([^)]*\)|var\([^)]*\)|#[0-9a-fA-F]+', '', p))
    vals = [float(n[0]) for n in nums]
    if inset and len(vals) >= 4 and vals[0] == 0 and vals[1] == 0 and vals[2] == 0: return 'ring'
    if inset and len(vals) >= 2 and vals[1] > 0 and (len(vals) < 3 or vals[2] <= 2): return 'hl'
    if not inset and len(vals) >= 4 and vals[0] == 0 and vals[1] == 0 and vals[2] == 0: return 'ring'
    return 'drop'

def remap_value(val, role, ctx):
    urls = []
    def keep(m): urls.append(m.group(0)); return '\x00%d\x00' % (len(urls) - 1)
    v = URL.sub(keep, val)
    v = VARC.sub(lambda m: map_var(m.group(1), float(m.group(2)), role, ctx), v)
    def f(m):
        p = parse_func(m.group(1))
        if not p: return m.group(0)
        return map_literal(p[0], p[1], role, ctx)
    v = FUNC.sub(f, v)
    def hx(m):
        s = m.group(1)
        if len(s) in (3, 4): s = ''.join(ch * 2 for ch in s)
        c = tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)); a = int(s[6:8], 16) / 255 if len(s) == 8 else 1
        return map_literal(c, a, role, ctx)
    v = HEX.sub(hx, v)
    v = re.sub(r'(?<![\w-])(white)(?![\w-])', lambda m: map_literal((255, 255, 255), 1, role, ctx), v) if role != 'fill' or ctx else v
    return re.sub(r'\x00(\d+)\x00', lambda m: urls[int(m.group(1))], v)


TRIPLET_PROPS = ('--sec-rgb', '--pt-rgb', '--pc-rgb', '--tr', '--t')
def text_safe_triplet(val):
    """Dark-UI tone triplets ("217,180,92") are used as TEXT colours and as 10-30% tints. On paper they must be deep: lightness capped at .26."""
    m = re.match(r'^(\s*)(\d{1,3})(\s*[, ]\s*)(\d{1,3})(\s*[, ]\s*)(\d{1,3})(\s*)$', val)
    if not m: return None
    r, g, b = int(m.group(2)), int(m.group(4)), int(m.group(6))
    h, l, s = hls((r, g, b))
    if l <= .26: return val
    nr, ng, nb = [int(round(v)) for v in from_hls(h, .26, clamp(max(s, .28), 0, .62))]
    return m.group(1) + str(nr) + m.group(3) + str(ng) + m.group(5) + str(nb) + m.group(7)

def remap_decl(prop, val, sel, rule_body):
    p = prop.strip().lower()
    if p in TRIPLET_PROPS:
        t = text_safe_triplet(val)
        if t is not None: return t
    if p in SKIP_P or p.startswith(('mask', '-webkit-mask', 'transition', 'animation')): return val
    role = role_of(p, sel)
    if role == 'shadow':
        return ','.join(remap_value(part, role, shadow_ctx(part)) for part in split_top(val))
    ctx = ''
    if role == 'fill':
        if PRESSY.search(sel): ctx = 'press'
        elif re.search(r'(?<![\w-])(height|width|block-size|inline-size)\s*:\s*(0\.5|1|1\.5|2)px', rule_body): ctx = 'thin'
    return remap_value(val, role, ctx)

PROP = re.compile(r'^((?:\s|/\*.*?\*/)*)(--[\w-]+|-?[a-zA-Z][\w-]*)(\s*:)(.*)$', re.S)

def split_decls(body):
    """Split a declaration block at top-level ';' (parens, strings and comments respected)."""
    out, cur, d, i, n = [], [], 0, 0, len(body)
    while i < n:
        ch = body[i]
        if body.startswith('/*', i):
            k = body.index('*/', i) + 2; cur.append(body[i:k]); i = k; continue
        if ch in '"\'':
            k = i + 1
            while k < n and body[k] != ch: k += 2 if body[k] == '\\' else 1
            cur.append(body[i:k + 1]); i = k + 1; continue
        if ch == '(': d += 1
        elif ch == ')': d -= 1
        if ch == ';' and d == 0: out.append(''.join(cur)); out.append(';'); cur = []
        else: cur.append(ch)
        i += 1
    out.append(''.join(cur)); return out

def remap_body(body, sel):
    res = []
    for part in split_decls(body):
        if part == ';': res.append(part); continue
        m = PROP.match(part)
        if not m: res.append(part); continue
        val = m.group(4); tail = ''
        mt = re.search(r'(\s*/\*.*?\*/\s*)$', val, re.S)   # trailing comment stays verbatim
        if mt: val, tail = val[:mt.start()], mt.group(1)
        res.append(m.group(1) + m.group(2) + m.group(3) + remap_decl(m.group(2), val, sel, body) + tail)
    return ''.join(res)

def walk(css, skip_sel, on_rule=None):
    """Rewrite declarations of every style rule (nested @media/@supports/@container walked; @keyframes walked with the
    keyframe selector; rules whose selector matches skip_sel left verbatim). Comments preserved."""
    out, i, n = [], 0, len(css)
    stack = []   # selectors of enclosing at-rules (for keyframes context)
    buf_start = 0
    def rule_end(j):
        d = 0
        while j < n:
            ch = css[j]
            if ch == '/' and css.startswith('/*', j): j = css.index('*/', j) + 2; continue
            if ch in '"\'':
                k = j + 1
                while css[k] != ch: k += 2 if css[k] == '\\' else 1
                j = k + 1; continue
            if ch == '{': d += 1
            elif ch == '}':
                d -= 1
                if d == 0: return j
            j += 1
        raise ValueError('unbalanced')
    def process(seg, inherited_kf):
        res, j, m = [], 0, len(seg)
        while j < m:
            if seg.startswith('/*', j):
                k = seg.index('*/', j) + 2; res.append(seg[j:k]); j = k; continue
            if seg[j].isspace() or seg[j] == ';': res.append(seg[j]); j += 1; continue
            # selector or at-rule prelude up to '{' or ';'
            k = j
            while k < m and seg[k] not in '{;':
                if seg.startswith('/*', k): k = seg.index('*/', k) + 2; continue
                k += 1
            if k >= m or seg[k] == ';':
                res.append(seg[j:k + 1]); j = k + 1; continue
            prelude = seg[j:k]
            # matching brace
            d, e = 0, k
            while e < m:
                if seg.startswith('/*', e): e = seg.index('*/', e) + 2; continue
                if seg[e] in '"\'':
                    q = seg[e]; e += 1
                    while seg[e] != q: e += 2 if seg[e] == '\\' else 1
                    e += 1; continue
                if seg[e] == '{': d += 1
                elif seg[e] == '}':
                    d -= 1
                    if d == 0: break
                e += 1
            inner = seg[k + 1:e]
            pl = prelude.strip()
            if pl.startswith('@'):
                kf = pl.startswith(('@keyframes', '@-webkit-keyframes'))
                name = pl.split()[1] if kf and len(pl.split()) > 1 else inherited_kf
                if kf and skip_sel(name, True): res.append(seg[j:e + 1])
                elif pl.startswith(('@font-face', '@property', '@page')): res.append(seg[j:e + 1])
                else: res.append(prelude + '{' + process(inner, name if kf else inherited_kf) + '}')
            else:
                sel = re.sub(r'/\*.*?\*/', '', pl, flags=re.S)
                if inherited_kf is None and skip_sel(sel, False): res.append(seg[j:e + 1])
                else:
                    nb = remap_body(inner, sel if inherited_kf is None else '@kf ' + inherited_kf)
                    if on_rule: on_rule(sel, inner, nb)
                    res.append(prelude + '{' + nb + '}')
            j = e + 1
        return ''.join(res)
    return process(css, None)
