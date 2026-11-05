# CODIS-ATELIER · the few colours that live in markup (brand mark accent). Called by patch_v32.py with apply(html).
def apply(html):
    html = once(html, 'style="fill:var(--mark-accent,#56CFDB)"', 'style="fill:var(--mark-accent,#2F7A74)"')
    html = once(html, '<rect class="c-point" x="51" y="41" width="18" height="18" rx="5" fill="#56CFDB"/>',
                '<rect class="c-point" x="51" y="41" width="18" height="18" rx="5" fill="#2F7A74"/>')
    html = once(html, 'White body, Aqua accent. -->', 'Ink body, Verdigris accent (CODIS-ATELIER). -->')
    return html
