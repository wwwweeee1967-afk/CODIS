"""CODIS contrast report. Reads <prefix>_*.json/.png written by tools/prof/s_contrast.mjs and prints WCAG contrast failures.

  py -3 tools/contrast_report.py <dir> <prefix> [--min 20]

Per item: foreground = computed colour (alpha x ancestor opacity) composited over the REAL background (median colour of the item's rect in the
text-hidden screenshot). Thresholds: 4.5 normal text, 3.0 large text (>=24px, or >=18.66px bold) and icons/placeholders as UI/large.
`worst` re-computes the ratio against the background's 5th/95th-percentile luminance (gradients, grain, glass edges)."""
import sys, os, re, json, glob, collections
from PIL import Image
import numpy as np

def parse(c):
    c = c.strip()
    m = re.match(r'rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)(?:[ ,/]+([\d.%]+))?\s*\)', c)
    if m:
        a = m.group(4); a = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith('%') else float(a))
        return (float(m.group(1)), float(m.group(2)), float(m.group(3))), a
    m = re.match(r'color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*/\s*([\d.%]+))?\s*\)', c)
    if m:
        a = m.group(4); a = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith('%') else float(a))
        return tuple(float(m.group(i)) * 255 for i in (1, 2, 3)), a
    return None, 0

def lin(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
def lum(rgb): return 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2])
def ratio(l1, l2):
    a, b = max(l1, l2), min(l1, l2); return (a + 0.05) / (b + 0.05)

def analyse(d, prefix, limit):
    rows = []
    for jf in sorted(glob.glob(os.path.join(d, prefix + '_*.json'))):
        j = json.load(open(jf, encoding='utf-8')); png = jf[:-5] + '.png'
        if not os.path.exists(png): continue
        im = np.asarray(Image.open(png).convert('RGB')).astype(float); H, W, _ = im.shape; k = j['dpr']
        for it in j['items']:
            fg, a = parse(it['c'])
            if fg is None: continue
            a *= it['o']
            if a < 0.04: continue
            x, y, w, h = [v * k for v in it['r']]
            x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w) + 1), min(H, int(y + h) + 1)
            if x1 - x0 < 2 or y1 - y0 < 2: continue
            px = im[y0:y1, x0:x1].reshape(-1, 3)
            bg = np.median(px, axis=0)
            ls = np.array([lum(p) for p in px[::max(1, len(px) // 400)]])
            blend = lambda b: tuple(a * fg[i] + (1 - a) * b[i] for i in range(3))
            fgc = blend(bg); r_med = ratio(lum(fgc), lum(bg))
            lo, hi = np.percentile(ls, 5), np.percentile(ls, 95)
            lf = lum(fgc); r_worst = min(ratio(lf, lo), ratio(lf, hi))
            large = it['fs'] >= 24 or (it['fs'] >= 18.66 and it['fw'] >= 700)
            thr = 3.0 if (it['k'] in ('icon',) or large) else 4.5
            if it['k'] == 'placeholder': thr = 4.5
            rows.append(dict(screen=j['name'], k=it['k'], sel=it['s'], text=it['t'], fs=it['fs'], fw=it['fw'], r=r_med, worst=r_worst, thr=thr,
                             fg='#%02x%02x%02x' % tuple(int(round(v)) for v in fgc), bg='#%02x%02x%02x' % tuple(int(round(v)) for v in bg), a=a))
    return rows

if __name__ == '__main__':
    d, prefix = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 25
    rows = analyse(d, prefix, limit)
    n = len(rows); fails = [r for r in rows if r['r'] < r['thr']]; marg = [r for r in rows if r['r'] >= r['thr'] and r['worst'] < r['thr'] * 0.92]
    print('%s: %d items · FAIL %d · marginal(worst-case) %d' % (prefix, n, len(fails), len(marg)))
    grp = collections.OrderedDict()
    for r in sorted(fails, key=lambda r: r['r'] - r['thr']):
        key = (r['sel'], r['fg'], r['bg'])
        g = grp.setdefault(key, dict(r=r, n=0, screens=set(), texts=[]))
        g['n'] += 1; g['screens'].add(r['screen']);
        if len(g['texts']) < 3: g['texts'].append(r['text'])
    print('--- FAIL groups (selector · fg on bg · ratio/needed · size) ---')
    for (sel, fg, bg), g in list(grp.items())[:limit * 3]:
        r = g['r']
        print('%5.2f/%.1f  %-58s %s on %s  %dpx w%d  x%d  [%s]  %s' % (r['r'], r['thr'], sel[:58], fg, bg, r['fs'], r['fw'], g['n'], ','.join(sorted(g['screens']))[:50], '|'.join(t[:14] for t in g['texts'])))
    json.dump(rows, open(os.path.join(d, prefix + '_report.json'), 'w', encoding='utf-8'))
