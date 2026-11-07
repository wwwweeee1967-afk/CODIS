"""CODIS-ATMOS-V2 maintenance: in the V2 motif block of tools/atmos_engine.js, a two-argument `P(path, fill)` call
(no `c`/stroke argument) throws at render time (P needs `c.k`) and CodisAtmos swallows it, silently dropping the card's decoration.
This rewrites every top-level two-argument P(...) call to F(...) (fill-only). Idempotent.
Usage: py -3 tools/fix_atmos_two_arg_P.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(HERE, 'atmos_engine.js')
e = open(path, encoding='utf-8').read()
a = e.index('    /* ===== CODIS-ATMOS-V2 · الدفعة 1'); b = e.index('  const V2 = new Set(')
seg = e[a:b]
BACKSLASH = chr(92)
out = []; i = 0; fixed = 0
while i < len(seg):
    if seg.startswith('P(', i) and (i == 0 or not (seg[i - 1].isalnum() or seg[i - 1] == '_')):
        j = i + 2; depth = 1; q = None; commas = 0
        while j < len(seg) and depth:
            ch = seg[j]
            if q:
                if ch == BACKSLASH: j += 1
                elif ch == q: q = None
            elif ch in ("'", '"', '`'): q = ch
            elif ch in '([{': depth += 1
            elif ch in ')]}': depth -= 1
            elif ch == ',' and depth == 1: commas += 1
            j += 1
        if commas == 1:
            out.append('F('); fixed += 1; i += 2; continue
    out.append(seg[i]); i += 1
e = e[:a] + ''.join(out) + e[b:]
open(path, 'w', encoding='utf-8', newline='\n').write(e)
print('fixed', fixed)
