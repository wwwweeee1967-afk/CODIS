"""CODIS-ADMIN (public app side): receive what the developer sends — coin/silver gifts and messages. Run AFTER tools/patch_mobile.py:
    python tools/patch_admin.py <in> <out>
The app holds NO admin power: it only reads the signed-in user's OWN rows (admin_grants / admin_messages, RLS) and marks them received
(ack_my_grants / ack_my_messages). Sending, listing users, banning … are server functions that check public.admins (sql/codis_admin.sql);
the admin panel UI lives only in the private add-on. Gifts are applied once: ledger reference grant|<id> + data.adminGrantsApplied."""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-ADMIN' not in t, 'admin patch already applied'
assert 'CODIS-MOBILE' in t, 'run tools/patch_mobile.py first'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:90]!r}'
    t = t.replace(old, new)

# silver ledger: a gift from the developer is its own transaction type
rep("function econSilverTxTypes(){ return ['DISMANTLE_CARD','OPEN_POUCH','PURCHASE_COSMETIC']; }",
    "function econSilverTxTypes(){ return ['DISMANTLE_CARD','OPEN_POUCH','PURCHASE_COSMETIC','ADMIN_GRANT']; }   /* ADMIN_GRANT: هدية/خصم من المطوّر (CODIS-ADMIN) */")
# list of applied gift ids (survives the 1500-entry ledger trim)
rep("  { const cs = d.closedSeen,",
    "  d.adminGrantsApplied = Array.isArray(d.adminGrantsApplied) ? d.adminGrantsApplied.filter(x=>typeof x === 'string').slice(-2000) : [];   /* CODIS-ADMIN */\n  { const cs = d.closedSeen,")

rep("/* ================= ACCOUNT & SYNC (CodisAccount) =================",
r"""/* ================= CODIS-ADMIN: ما يرسله المطوّر (هدايا + رسائل) =================
   التطبيق هنا يستقبل فقط: صفوف المستخدم نفسه (RLS). لا يوجد في هذا الملف أي صلاحية مطوّر. */
function codisInboxNote(o){
  try{
    const items = data.notifications.items;
    if(items.some(n=>n.uniqueKey === o.key)) return false;
    items.unshift({ id:'n' + Date.now() + '_' + Math.random().toString(36).slice(2, 7), type:'ADMIN', category:'system', priority:'HIGH',
      title:String(o.title || '').slice(0, 120), message:String(o.message || '').slice(0, 2000), icon:o.icon || 'info', tone:o.tone || 'neutral',
      actionPage:null, groupKey:null, uniqueKey:o.key, createdAt:new Date().toISOString(), read:false });
    if(items.length > 200) data.notifications.items = items.slice(0, 200);
    saveData();
    try{ CodisNotifications.renderBadge(); }catch(e){}
    return true;
  }catch(e){ console.warn('[CODIS admin] inbox note:', e && e.message); return false; }
}
/* هدية/خصم: مرة واحدة فقط لكل معرّف. الخصم لا ينزل بالرصيد تحت الصفر. يُرجع true إذا طُبّقت (أو كانت مطبّقة سابقاً) */
function codisApplyAdminGrant(g){
  if(!g || typeof g.id !== 'string' || !/^[0-9a-f-]{36}$/i.test(g.id) || window.CODIS_SYNC_HOLD) return false;
  if(!Array.isArray(data.adminGrantsApplied)) data.adminGrantsApplied = [];
  const done = data.adminGrantsApplied, ref = 'grant|' + g.id;
  if(done.indexOf(g.id) !== -1) return true;
  if(data.wallet.transactions.some(x=>x.referenceId === ref) || CodisWallet.silverTxs().some(x=>x.referenceId === ref)){ done.push(g.id); saveData(); return true; }
  const coins = Math.trunc(Number(g.coins) || 0), silver = Math.trunc(Number(g.silver) || 0), note = String(g.note || '').slice(0, 200);
  const reason = note ? 'من المطوّر: ' + note : 'من المطوّر';
  let gc = 0, gs = 0;
  const r = CodisWallet.transact([], ()=>{
    if(coins){ gc = coins < 0 ? -Math.min(-coins, CodisWallet.balance()) : coins; if(gc && !CodisWallet.apply('ADMIN_ADJUSTMENT', gc, reason, 'admin', ref)) return { ok:false, reason:'tx' }; }
    if(silver){ gs = silver < 0 ? -Math.min(-silver, CodisWallet.silverBalance()) : silver; if(gs && !CodisWallet.applySilver('ADMIN_GRANT', gs, reason, 'admin', ref)) return { ok:false, reason:'tx' }; }
    done.push(g.id); if(done.length > 2000) done.splice(0, done.length - 2000);
    return { ok:true };
  });
  if(!r || !r.ok){ const i = done.indexOf(g.id); if(i !== -1) done.splice(i, 1); return false; }
  const part = (n, unit)=>(n > 0 ? '+' : '−') + econFmt(Math.abs(n)) + ' ' + unit;
  const parts = [gc ? part(gc, 'كوين') : '', gs ? part(gs, 'فضة') : ''].filter(Boolean).join(' · ') || 'بدون تغيير بالرصيد';
  const gift = gc >= 0 && gs >= 0;
  codisInboxNote({ key:ref, title:gift ? 'هدية من المطوّر' : 'تعديل من المطوّر', message:parts + (note ? ' — ' + note : ''), icon:gift ? 'gift' : 'coin', tone:gift ? 'success' : 'neutral' });
  showToast((gift ? 'وصلتك هدية من المطوّر: ' : 'تعديل من المطوّر: ') + parts, gift ? 'var(--success)' : 'var(--warning)', gift ? 'gift' : 'coin');
  try{ if(typeof econRenderAll === 'function') econRenderAll(); }catch(e){}
  return true;
}
function codisDeliverAdminMessage(m){
  if(!m || typeof m.id !== 'string' || window.CODIS_SYNC_HOLD) return false;
  const added = codisInboxNote({ key:'admsg|' + m.id, title:String(m.title || 'رسالة من المطوّر'), message:String(m.body || ''), icon:'bell', tone:'neutral' });
  if(added) showToast('رسالة من المطوّر: ' + String(m.title || '').slice(0, 60), 'var(--aqua)', 'bell');
  return true;
}
/* ================= ACCOUNT & SYNC (CodisAccount) =================""")

rep("  /* ---------- بدء التشغيل ---------- */\n  async function init(){",
r"""  /* ---------- CODIS-ADMIN: صندوق الوارد (هدايا/رسائل المطوّر لهذا المستخدم فقط) ---------- */
  let inboxAt = 0, inboxBusy = false;
  async function pullInbox(force){
    if(!S.user || !S.session || window.CODIS_SYNC_HOLD || inboxBusy) return;
    if(!force && Date.now() - inboxAt < 30000) return;
    inboxBusy = true; inboxAt = Date.now();
    try{
      const g = await api('/rest/v1/admin_grants?select=id,coins,silver,note,created_at&claimed_at=is.null&cancelled_at=is.null&order=created_at.asc&limit=100');
      if(g.ok){
        const rows = await g.json(), ids = [];
        (Array.isArray(rows) ? rows : []).forEach(x=>{ try{ if(codisApplyAdminGrant(x)) ids.push(x.id); }catch(e){} });
        if(ids.length){ try{ await rpc('ack_my_grants', { p_ids:ids }); }catch(e){ console.debug('[CODIS] ack grants:', e && e.message); } }
      }
      const m = await api('/rest/v1/admin_messages?select=id,title,body,created_at&delivered_at=is.null&order=created_at.asc&limit=100');
      if(m.ok){
        const rows = await m.json(), ids = [];
        (Array.isArray(rows) ? rows : []).forEach(x=>{ try{ if(codisDeliverAdminMessage(x)) ids.push(x.id); }catch(e){} });
        if(ids.length){ try{ await rpc('ack_my_messages', { p_ids:ids }); }catch(e){ console.debug('[CODIS] ack messages:', e && e.message); } }
      }
    }catch(e){ console.debug('[CODIS] inbox:', e && e.message); }   // الجداول غير موجودة بعد / بدون شبكة: لا شيء
    finally{ inboxBusy = false; }
  }
  /* استدعاء دوال الأدمن بجلسة المستخدم الحالية — للوحة المطوّر فقط. الخادم يرفض أي حساب ليس في public.admins */
  async function adminCall(name, body){
    if(!S.user) throw Object.assign(new Error('not signed in'), { code:'28000' });
    if(!/^admin_[a-z_]+$/.test(String(name))) throw new Error('bad function');
    return rpc(name, body || {});
  }

  /* ---------- بدء التشغيل ---------- */
  async function init(){""")
rep("    await reconcile();\n    loadAdmin();\n",
    "    await reconcile();\n    loadAdmin();\n    pullInbox(true);\n"
    "    document.addEventListener('visibilitychange', () => { if(!document.hidden) pullInbox(); });\n"
    "    setInterval(() => { if(!document.hidden) pullInbox(); }, 300000);\n")
rep("  return { init, signIn, signOut, deleteAccount, syncNow, noteChange, state:S,",
    "  return { init, signIn, signOut, deleteAccount, syncNow, noteChange, pullInbox, adminCall, state:S,")

open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
