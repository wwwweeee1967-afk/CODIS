'use strict';
const fs=require('fs'),vm=require('vm'),crypto=require('crypto'),{execFileSync}=require('child_process');
const path=require('path'), ROOT=path.join(__dirname,'..');
const FILE=process.argv[2]||path.join(ROOT,'app/CODIS_FINAL.html');
const html=fs.readFileSync(FILE,'utf8');
const a=html.indexOf('const CODIS_BACKEND = {'), b=html.indexOf('/* ---------- صفحات الإعدادات');
const MOD=html.slice(a,b)+'\n;globalThis.__CA = CodisAccount;';
const results=[]; let failures=0;
function ok(name,cond,extra){ results.push({name,pass:!!cond}); if(!cond) failures++; console.log((cond?'PASS ':'FAIL ')+name+(cond||!extra?'':'  -> '+extra)); }
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const b64u=buf=>Buffer.from(buf).toString('base64').replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
const mkjwt=p=>b64u(JSON.stringify({alg:'HS256',typ:'JWT'}))+'.'+b64u(JSON.stringify(p))+'.'+b64u('sig');
const jwtp=t=>JSON.parse(Buffer.from(t.split('.')[1].replace(/-/g,'+').replace(/_/g,'/'),'base64').toString());
const SB='https://abcd.supabase.co', ANON=mkjwt({role:'anon',iss:'supabase'});
const U1={id:'11111111-1111-1111-1111-111111111111',email:'u1@example.com',name:'مستخدم ١'};
const U2={id:'22222222-2222-2222-2222-222222222222',email:'u2@example.com',name:'مستخدم ٢'};

/* ---------- real Postgres ---------- */
// psql runner: Linux `su postgres` by default; CODIS_PG_CONTAINER=<name> uses a PostgreSQL 16 docker container;
// CODIS_PSQL_MODULE=<file> uses an in-process psqlSync(args,input) (e.g. tests/pglite_bridge.js). SQL is fed on stdin.
const PGC=process.env.CODIS_PG_CONTAINER, PSM=process.env.CODIS_PSQL_MODULE&&require(path.resolve(process.env.CODIS_PSQL_MODULE));
const shq=s=>"'"+s.replace(/'/g,"'\"'\"'")+"'";
function psql(args,input){
  if(PSM){ const r=PSM.psqlSync(args,input); if(r.status!==0){ const e=new Error('psql exited '+r.status); e.stderr=r.stderr; e.stdout=r.stdout; throw e; } return r.stdout; }
  const o={encoding:'utf8',input,stdio:['pipe','pipe','pipe']};
  return PGC ? execFileSync('docker',['exec','-i',PGC,'psql','-X','-U','postgres',...args],o)
             : execFileSync('su',['postgres','-c','psql -X '+args.map(shq).join(' ')],o);
}
function resetDb(){
  psql(['-q','-c','drop database if exists codis_h','-c','create database codis_h']);
  psql(['-q','-d','codis_h','-f','-'],fs.readFileSync(path.join(__dirname,'stub.sql'),'utf8'));
  psql(['-q','-v','ON_ERROR_STOP=1','-d','codis_h','-f','-'],fs.readFileSync(path.join(ROOT,'sql/codis_supabase_setup.sql'),'utf8'));
}
function pg(sql,uid){ // run as `authenticated` with JWT sub (or superuser when uid===null)
  const pre=uid?`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false) as _;\n`:'';
  const out=psql(['-At','-q','-v','ON_ERROR_STOP=1','-d','codis_h','-f','-'],pre+sql+';\n');
  const lines=out.split('\n').filter(x=>x.trim()!==''); return uid?lines.slice(1):lines;
}
function pgRows(sql){ return pg(sql,null); }

/* ---------- mock Supabase over fetch ---------- */
function makeServer(){
  const S={calls:[],codes:{},refresh:{},settingsGoogle:true,badKey:false,net:true,failRpc:null,failGet:null,rpcFail500:false,refreshReject:false,users:{},google:'ok'};
  function issue(user,ttl=3600){
    const now=Math.floor(Date.now()/1000);
    const at=mkjwt({sub:user.id,email:user.email,role:'authenticated',aud:'authenticated',exp:now+ttl,user_metadata:{full_name:user.name}});
    const rt='rt_'+crypto.randomBytes(8).toString('hex'); S.refresh[rt]=user.id;
    pgRows(`insert into auth.users(id,email) values('${user.id}','${user.email}') on conflict do nothing`);
    return {access_token:at,refresh_token:rt,expires_in:ttl,token_type:'bearer'};
  }
  S.googleLogin=(user,challenge)=>{ const code='code_'+crypto.randomBytes(6).toString('hex'); S.codes[code]={user,challenge,used:false}; return code; };
  S.issue=issue;
  S.fetch=async(url,init={})=>{
    if(!S.net) throw new TypeError('fetch failed');
    const u=new URL(url); const path=u.pathname+u.search; const method=(init.method||'GET').toUpperCase();
    const h=init.headers||{}; const body=init.body?JSON.parse(init.body):undefined;
    S.calls.push({method,path}); 
    const J=(status,obj)=>({ok:status>=200&&status<300,status,json:async()=>obj===undefined?null:obj,text:async()=>obj===undefined?'':JSON.stringify(obj)});
    if(h.apikey!==ANON||S.badKey) return J(401,{message:'Invalid API key'});
    if(u.pathname==='/auth/v1/settings') return J(200,{external:{google:S.settingsGoogle}});
    if(u.pathname==='/auth/v1/token'&&u.searchParams.get('grant_type')==='pkce'){
      const c=S.codes[body.auth_code]; if(!c||c.used) return J(400,{error_code:'validation_failed',msg:'invalid flow state, no valid flow state found'});
      const chal=b64u(crypto.createHash('sha256').update(body.code_verifier||'').digest());
      if(chal!==c.challenge) return J(400,{error_code:'bad_code_verifier',msg:'code challenge does not match previously saved code verifier'});
      c.used=true; return J(200,issue(c.user));
    }
    if(u.pathname==='/auth/v1/token'&&u.searchParams.get('grant_type')==='refresh_token'){
      if(S.refreshReject) return J(400,{error_code:'refresh_token_not_found',msg:'Invalid Refresh Token'});
      const uid=S.refresh[body.refresh_token]; if(!uid) return J(400,{error_code:'refresh_token_not_found',msg:'Invalid Refresh Token'});
      delete S.refresh[body.refresh_token]; return J(200,issue(uid===U1.id?U1:U2));
    }
    if(u.pathname==='/auth/v1/logout') return J(204);
    // REST/storage need a user JWT
    const auth=(h.Authorization||'').replace(/^Bearer /,''); let claims=null; try{ claims=jwtp(auth);}catch(e){}
    if(!claims||!claims.sub) return J(401,{message:'JWT invalid',code:'PGRST301'});
    if(claims.exp*1000<Date.now()) return J(401,{message:'JWT expired',code:'PGRST303'});
    const uid=claims.sub;
    if(u.pathname==='/rest/v1/progress'){
      if(S.failGet) return J(S.failGet.status,S.failGet.body);
      const l=pg(`select coalesce(json_agg(t),'[]'::json)::text from (select data,version,updated_at from public.progress where user_id='${uid}') t`,uid); return J(200,JSON.parse(l[l.length-1]));
    }
    if(u.pathname==='/rest/v1/rpc/save_progress'){
      if(S.failRpc) return J(S.failRpc.status,S.failRpc.body);
      try{ const l=pg(`select public.save_progress($j$${JSON.stringify(body.p_data)}$j$::jsonb, ${body.p_base_version===null?'null':Number(body.p_base_version)})::text`,uid); return J(200,JSON.parse(l[l.length-1])); }
      catch(e){ return J(400,{code:'P0001',message:String(e.stderr||e.message).split('\n')[0]}); }
    }
    if(u.pathname==='/rest/v1/rpc/delete_my_account'){
      if(S.rpcFail500) return J(500,{message:'internal error'});
      try{ pg(`select public.delete_my_account()`,uid); return J(204); }catch(e){ return J(400,{code:'P0001',message:String(e.stderr||e.message).split('\n')[0]}); }
    }
    if(u.pathname==='/rest/v1/admins'){ const l=pg(`select coalesce(json_agg(t),'[]'::json)::text from (select user_id from public.admins) t`,uid); return J(200,JSON.parse(l[l.length-1])); }
    if(u.pathname==='/storage/v1/object/authenticated/dev-addon/dev-addon.js'){
      const l=pg(`select count(*) from storage.objects where bucket_id='dev-addon' and name='dev-addon.js'`,uid);
      if(l[l.length-1]==='0') return J(404,{message:'Object not found'});
      const code='window.__devAddonRan=1;'+'/*'+'x'.repeat(200)+'*/'; return {ok:true,status:200,json:async()=>({}),text:async()=>code};
    }
    return J(404,{message:'no route '+path});
  };
  return S;
}

/* ---------- browser sandbox ---------- */
function makeStore(){ const m=new Map(); return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k),key:i=>[...m.keys()][i]||null,get length(){return m.size;},_m:m}; }
function makeDevice(){ return {ls:makeStore()}; }
function mkEl(tag){ const cls=new Set(); const kids={}; const el={tag,id:'',innerHTML:'',textContent:'',disabled:false,style:{},attrs:{},
  classList:{add:(...c)=>c.forEach(x=>cls.add(x)),remove:(...c)=>c.forEach(x=>cls.delete(x)),contains:c=>cls.has(c),toggle:(c,f)=>{ (f===undefined?!cls.has(c):f)?cls.add(c):cls.delete(c); }},
  setAttribute(k,v){el.attrs[k]=v;}, addEventListener(ev,fn){ (el._l=el._l||{})[ev]=fn; },
  querySelector(sel){ const id=sel.replace('#',''); return kids[id]||(kids[id]=Object.assign(mkEl('x'),{id})); }, appendChild(c){ (el.children=el.children||[]).push(c); } }; return el; }
async function openPage(dev,server,o){
  o=o||{}; const timers=new Set(); const toasts=[]; const nav=[]; let reloads=0;
  const url=new URL(o.url||'https://app.example.com/codis.html'+(o.search||'')+(o.hash||''));
  const loc={protocol:url.protocol,hostname:url.hostname,origin:url.origin,pathname:url.pathname,search:url.search,hash:url.hash,
    set href(v){ nav.push(v); }, get href(){return url.href;}, reload(){ reloads++; }};
  const els={}; const gate=mkEl('div');
  const doc={ getElementById:id=>id==='codis-gate'&&doc._gate?gate:(els[id]||null), createElement:t=>t==='div'?gate:mkEl(t),
    body:{appendChild(e){ doc._gate=true; }}, head:mkEl('head'), documentElement:{classList:{add(){},remove(){}}}, hidden:false,
    querySelector(sel){ const m=sel.match(/meta\[name="([^"]+)"\]/); if(m&&o.meta&&o.meta[m[1]]!==undefined) return {getAttribute:()=>o.meta[m[1]]}; return null; }, addEventListener(){} };
  gate.id='codis-gate';
  const ss=o.session||makeStore();
  const sb={ console:{log(){},warn(){},debug(){},error(){}}, crypto:crypto.webcrypto, TextEncoder, TextDecoder, atob:s=>Buffer.from(s,'base64').toString('binary'), btoa:s=>Buffer.from(s,'binary').toString('base64'),
    Uint8Array, JSON, Date, Object, Array, String, Number, Promise, Error, Math, URL, URLSearchParams, AbortController, encodeURIComponent, parseInt, isNaN,
    setTimeout:(fn,ms)=>{ const h=setTimeout(()=>{timers.delete(h);fn();},ms); timers.add(h); return h; }, clearTimeout:h=>{clearTimeout(h);timers.delete(h);},
    localStorage:dev.ls, sessionStorage:ss, location:loc, history:{replaceState(_a,_b,p){ loc.search=''; loc.hash=''; }}, document:doc, navigator:{onLine:o.onLine!==false},
    fetch:(u,i)=>server.fetch(u,i), showToast:(m,c)=>toasts.push(m), codisConfirm:async(opts)=>{ sb.__confirms.push(opts); const r=sb.__confirmAnswers.length?sb.__confirmAnswers.shift():true; return r; }, __confirms:[], __confirmAnswers:o.confirm||[],
    STORE_KEY:'life_organizer_data_v1', BACKUP_KEY:'life_organizer_data_v1_corrupt_backup', codisSaveSuspended:false, escapeHtml:s=>String(s), codisRenderAccountPage(){}, 
    CodisStorage:{read:k=>dev.ls.getItem(k),write:(k,v)=>{ dev.ls.setItem(k,v); return true; }},
  };
  sb.window=sb; sb.globalThis=sb; sb.addEventListener=function(){}; if(o.override) sb.CODIS_BACKEND_OVERRIDE=o.override===true?{url:SB,anonKey:ANON}:o.override;
  sb.loadData=()=>JSON.parse(dev.ls.getItem(sb.STORE_KEY)||'null')||{settings:{}}; sb.data=sb.loadData();
  vm.createContext(sb); vm.runInContext(MOD,sb,{filename:'codis-module'});
  const CA=sb.__CA;
  await CA.init();
  await sleep(o.settle===undefined?30:o.settle);
  return {CA,sb,toasts,nav,get reloads(){return reloads;},loc,gate,doc,timers,dispose(){ timers.forEach(clearTimeout); timers.clear(); }};
}
const setData=(dev,obj)=>dev.ls.setItem('life_organizer_data_v1',JSON.stringify(obj));
const getData=dev=>JSON.parse(dev.ls.getItem('life_organizer_data_v1')||'null');
const dbRow=uid=>{ const r=pgRows(`select json_build_object('v',version,'d',data)::text from public.progress where user_id='${uid}'`); return r.length?JSON.parse(r[0]):null; };

(async()=>{
resetDb(); const server=makeServer();

console.log('\n== S0 config validation (unit) ==');
{ const dev=makeDevice(); const pg0=await openPage(dev,server,{override:true}); const T=pg0.CA._test; 
  const L=p=>({protocol:p,hostname:p==='https:'?'app.example.com':'localhost'}); 
  const chk=(c,l)=>T.checkBackend(c,l||L('https:'));
  ok('missing config -> code missing',chk({url:'',anonKey:''}).code==='missing');
  ok('url only -> incomplete',chk({url:SB,anonKey:''}).code==='incomplete');
  ok('garbage url -> url',chk({url:'not a url',anonKey:ANON}).code==='url');
  ok('http remote url rejected',chk({url:'http://abcd.supabase.co',anonKey:ANON}).code==='url');
  ok('url with path rejected',chk({url:SB+'/rest/v1',anonKey:ANON}).code==='url');
  ok('valid anon JWT accepted',chk({url:SB,anonKey:ANON}).ok===true);
  ok('trailing slash normalised',chk({url:SB+'/',anonKey:ANON}).cfg.url===SB);
  ok('local http://localhost url accepted',chk({url:'http://localhost:54321',anonKey:ANON},L('http:')).ok===true);
  ok('service_role JWT rejected',chk({url:SB,anonKey:mkjwt({role:'service_role'})}).code==='secretkey');
  ok('sb_secret_ key rejected',chk({url:SB,anonKey:'sb_secret_abc123'}).code==='secretkey');
  ok('sb_publishable_ key accepted',chk({url:SB,anonKey:'sb_publishable_abc123'}).ok===true);
  ok('garbage key rejected',chk({url:SB,anonKey:'garbage'}).code==='key');
  ok('file:// page rejected (OAuth cannot return)',chk({url:SB,anonKey:ANON},{protocol:'file:',hostname:''}).code==='origin');
  ok('error messages never contain the key',!JSON.stringify([chk({url:SB,anonKey:mkjwt({role:'service_role'})}),chk({url:SB,anonKey:'sb_secret_abc123'})]).includes('abc123')&&!JSON.stringify(chk({url:SB,anonKey:mkjwt({role:'service_role'})})).includes(mkjwt({role:'service_role'})));
  // PKCE primitive: RFC 7636 appendix B vector
  const ch=T.b64u(crypto.createHash('sha256').update('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk').digest());
  ok('PKCE S256 challenge matches RFC 7636 vector',ch==='E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM',ch);
  ok('jwt decoder handles all padding cases',[1,2,3,4,5,6,7].every(n=>{ const t=mkjwt({sub:'x'.repeat(n),email:'é'+n}); const c=T.jwt(t); return c&&c.sub==='x'.repeat(n);}));
  const m1=await openPage(makeDevice(),server,{meta:{'codis-supabase-url':SB,'codis-supabase-key':ANON}}); ok('config via <meta> tags works',m1.CA.configured===true); m1.dispose();
  const m2=await openPage(makeDevice(),server,{meta:{'codis-supabase-url':SB,'codis-supabase-key':ANON},override:{url:'https://zzzz.supabase.co',anonKey:ANON}}); ok('OVERRIDE takes priority over <meta>',m2.CA.configured===true); m2.dispose(); pg0.dispose(); }

console.log('\n== S5 missing / wrong config & guest mode ==');
{ const dev=makeDevice(); const n0=server.calls.length; const p=await openPage(dev,server,{}); 
  ok('no config: not configured, reason shown',p.CA.configured===false&&p.CA.configError.code==='missing');
  ok('no config: no gate, no network (app usable as guest)',!p.gate.classList.contains('is-open')&&server.calls.length===n0);
  await p.CA.signIn(); ok('no config: signIn shows explicit Arabic error, no redirect',p.nav.length===0&&p.toasts.some(m=>/غير مهيّأة/.test(m)),JSON.stringify(p.toasts)); p.dispose();
  const p2=await openPage(makeDevice(),server,{override:{url:SB,anonKey:mkjwt({role:'service_role'})}}); await p2.CA.signIn();
  ok('service_role key: refused, never used for network',p2.CA.configured===false&&p2.CA.configError.code==='secretkey'&&p2.nav.length===0&&server.calls.length===n0); p2.dispose();
  const p3=await openPage(makeDevice(),server,{override:true,url:'file:///C:/codis.html'}); 
  ok('file:// : disabled with explanation, no gate',p3.CA.configured===false&&p3.CA.configError.code==='origin'&&!p3.gate.classList.contains('is-open')); p3.dispose();
  const devG=makeDevice(); devG.ls.setItem('codis_guest_mode','1'); const pg1=await openPage(devG,server,{override:true});
  ok('guest mode: no gate, no network',!pg1.gate.classList.contains('is-open')&&server.calls.length===n0&&pg1.CA.state.user===null); pg1.dispose();
  const pg2=await openPage(makeDevice(),server,{override:true}); ok('configured + not guest + no session: gate shown',pg2.gate.classList.contains('is-open')); pg2.dispose(); }

console.log('\n== S1 first-time Google sign-in (PKCE) + cloud save ==');
const D1=makeDevice(); setData(D1,{settings:{},weeks:{w1:{days:{0:[{t:'a'}]}}},wallet:{coins:5}});
let challenge, redirectTo;
{ const p=await openPage(D1,server,{override:true}); await p.CA.signIn();
  ok('signIn redirects exactly once',p.nav.length===1,String(p.nav.length));
  const u=new URL(p.nav[0]);
  ok('authorize endpoint + provider=google + flow_type=pkce',u.origin===SB&&u.pathname==='/auth/v1/authorize'&&u.searchParams.get('provider')==='google'&&u.searchParams.get('flow_type')==='pkce');
  ok('code_challenge_method=s256',u.searchParams.get('code_challenge_method')==='s256');
  challenge=u.searchParams.get('code_challenge'); redirectTo=u.searchParams.get('redirect_to');
  const pk=JSON.parse(D1.ls.getItem('codis_pkce_verifier'));
  ok('stored verifier: 43-128 chars base64url, hashes to challenge',/^[A-Za-z0-9_-]{43,128}$/.test(pk.v)&&b64u(crypto.createHash('sha256').update(pk.v).digest())===challenge);
  ok('redirect_to = origin + path (no query/hash)',redirectTo==='https://app.example.com/codis.html',redirectTo);
  await p.CA.signIn(); ok('double-click does not start a second redirect',p.nav.length===1); p.dispose(); }
{ const code=server.googleLogin(U1,challenge); const tokBefore=server.calls.filter(c=>c.path.includes('grant_type=pkce')).length;
  const p=await openPage(D1,server,{override:true,search:'?code='+code,settle:400});
  ok('callback: code exchanged exactly once',server.calls.filter(c=>c.path.includes('grant_type=pkce')).length===tokBefore+1);
  ok('callback: URL cleaned (code removed)',p.loc.search==='');
  ok('callback: user loaded from session',p.CA.state.user&&p.CA.state.user.id===U1.id&&p.CA.state.user.email===U1.email);
  ok('callback: verifier consumed',D1.ls.getItem('codis_pkce_verifier')===null);
  const row=dbRow(U1.id); ok('guest progress migrated to the account (server row v1)',row&&row.v===1&&row.d.weeks&&row.d.weeks.w1,JSON.stringify(row));
  ok('status synced, meta.base=1 dirty=false',p.CA.state.status==='synced'&&p.CA.meta().base===1&&p.CA.meta().dirty===false&&p.CA.meta().owner===U1.id,JSON.stringify(p.CA.meta()));
  ok('guest flag cleared; gate hidden',D1.ls.getItem('codis_guest_mode')===null&&!p.gate.classList.contains('is-open'));
  p.dispose(); }
console.log('\n== S1b duplicate callback / reload / injection ==');
{ const code=server.googleLogin(U1,challenge); const n0=server.calls.filter(c=>c.path.includes('grant_type=pkce')).length;
  const p=await openPage(D1,server,{override:true,search:'?code='+code,settle:50});
  ok('replayed code with no verifier: NOT exchanged, explicit message',server.calls.filter(c=>c.path.includes('grant_type=pkce')).length===n0&&p.toasts.some(m=>/انتهت محاولة/.test(m)),JSON.stringify(p.toasts)); p.dispose(); }
{ const dev=makeDevice(); const p=await openPage(dev,server,{override:true,hash:'#access_token='+mkjwt({sub:U2.id,email:'evil@x',exp:9999999999})+'&refresh_token=x&expires_in=3600'});
  ok('tokens injected in URL fragment are ignored (no session fixation)',p.CA.state.user===null&&dev.ls.getItem('codis_auth_session')===null&&p.loc.hash===''); p.dispose(); }
{ const dev=makeDevice(); const kv=makeDevice(); const sig=await (async()=>{const p0=await openPage(dev,server,{override:true}); await p0.CA.signIn(); const ch=new URL(p0.nav[0]).searchParams.get('code_challenge'); p0.dispose(); return ch;})();
  dev.ls.setItem('codis_pkce_verifier',JSON.stringify({v:JSON.parse(dev.ls.getItem('codis_pkce_verifier')).v,t:Date.now()-11*60*1000}));
  const code=server.googleLogin(U2,sig); const n0=server.calls.filter(c=>c.path.includes('grant_type=pkce')).length;
  const p=await openPage(dev,server,{override:true,search:'?code='+code}); ok('stale (>10 min) verifier rejected',p.CA.state.user===null&&server.calls.filter(c=>c.path.includes('grant_type=pkce')).length===n0); p.dispose(); }
{ const n0=server.calls.length; const p=await openPage(D1,server,{override:true,settle:300});
  ok('page reload with valid session: restored, no token calls',p.CA.state.user&&p.CA.state.user.id===U1.id&&!server.calls.slice(n0).some(c=>c.path.includes('/auth/v1/token')),JSON.stringify(server.calls.slice(n0)));
  ok('reload: status synced',p.CA.state.status==='synced'); p.dispose(); }

console.log('\n== S4 cancellation & provider errors ==');
{ const dev=makeDevice(); const p=await openPage(dev,server,{override:true,search:'?error=access_denied&error_code=access_denied&error_description=User+cancelled+the+login'});
  ok('user cancellation: friendly message, no session, URL cleaned',p.toasts.some(m=>/تم إلغاء/.test(m))&&p.CA.state.user===null&&p.loc.search===''); ok('after cancel: gate shown (no loop)',p.gate.classList.contains('is-open')&&p.nav.length===0); p.dispose(); }
{ const p=await openPage(makeDevice(),server,{override:true}); const T=p.CA._test;
  ok('map: provider not enabled',/غير مفعّل/.test(T.authErrMsg('validation_failed','Unsupported provider: provider is not enabled')));
  ok('map: bad Google secret',/Client Secret/.test(T.authErrMsg('server_error','Unable to exchange external code: 4/0AX')));
  ok('map: redirect not allowed',/Redirect URLs/.test(T.authErrMsg('','redirect_to is not allowed'))); p.dispose(); }
{ server.settingsGoogle=false; const dev=makeDevice(); const p=await openPage(dev,server,{override:true}); await p.CA.signIn();
  ok('Google provider disabled in Supabase: explicit error, NO redirect to raw JSON page',p.nav.length===0&&p.toasts.some(m=>/غير مفعّل/.test(m)),JSON.stringify(p.toasts)); p.dispose(); server.settingsGoogle=true; }
{ server.badKey=true; const p=await openPage(makeDevice(),server,{override:true}); await p.CA.signIn(); ok('rejected anon key: explicit error, no redirect',p.nav.length===0&&p.toasts.some(m=>/المفتاح العام مرفوض/.test(m))); p.dispose(); server.badKey=false; }
{ server.net=false; const p=await openPage(makeDevice(),server,{override:true}); await p.CA.signIn(); ok('server unreachable at sign-in: explicit error, no redirect',p.nav.length===0&&p.toasts.some(m=>/تعذّر الوصول/.test(m))); p.dispose(); server.net=true; }

console.log('\n== S2 returning user on a 2nd device (cloud restore) ==');
const D2=makeDevice();
{ const p0=await openPage(D2,server,{override:true}); await p0.CA.signIn(); const ch=new URL(p0.nav[0]).searchParams.get('code_challenge'); p0.dispose();
  const code=server.googleLogin(U1,ch); const ssn=makeStore();
  const p=await openPage(D2,server,{override:true,search:'?code='+code,session:ssn,settle:400});
  const d=getData(D2); ok('restore: device data replaced by the account snapshot',d&&d.weeks&&d.weeks.w1&&d.wallet.coins===5,JSON.stringify(d));
  ok('restore: page reload triggered once (guarded)',p.reloads===1&&ssn.getItem('codis_reload_n')==='1',p.reloads+'/'+ssn.getItem('codis_reload_n'));
  ok('restore: meta base=server version, clean',p.CA.meta().base===1&&p.CA.meta().dirty===false&&p.CA.meta().owner===U1.id); p.dispose();
  const p2=await openPage(D2,server,{override:true,settle:300}); ok('2nd device reload: in sync, no further reload',p2.CA.state.status==='synced'&&p2.reloads===0); p2.dispose(); }

console.log('\n== S3 expired session / refresh ==');
{ const dev=makeDevice(); dev.ls._m.forEach((v,k)=>{}); // fresh device with expired token but valid refresh token
  const tok=server.issue(U1,-120); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()-120000}));
  setData(dev,getData(D1)); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:U1.id,base:1,dirty:false,lastSync:1,changedAt:0}));
  const n0=server.calls.filter(c=>c.path.includes('grant_type=refresh_token')).length; const p=await openPage(dev,server,{override:true,settle:300});
  ok('expired access token refreshed once at boot',server.calls.filter(c=>c.path.includes('grant_type=refresh_token')).length===n0+1&&p.CA.state.status==='synced');
  const stored=JSON.parse(dev.ls.getItem('codis_auth_session')); ok('rotated refresh token persisted',stored.refresh_token!==tok.refresh_token&&stored.expires_at>Date.now());
  p.dispose(); }
{ const dev=makeDevice(); const tok=server.issue(U1,-120); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()-120000}));
  setData(dev,{settings:{},weeks:{wLOCAL:{}}}); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:U1.id,base:1,dirty:true,lastSync:1,changedAt:5}));
  server.refreshReject=true; const p=await openPage(dev,server,{override:true,settle:300}); server.refreshReject=false;
  ok('refresh rejected: status expired + gate shown (no redirect loop)',p.CA.state.status==='expired'&&p.gate.classList.contains('is-open')&&p.nav.length===0);
  ok('expired session did NOT touch local progress',getData(dev).weeks.wLOCAL!==undefined&&JSON.parse(dev.ls.getItem('codis_sync_meta')).dirty===true); p.dispose(); }
{ const dev=makeDevice(); const tok=server.issue(U1,30); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()+30000}));
  setData(dev,getData(D1)); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:U1.id,base:1,dirty:false,lastSync:1,changedAt:0}));
  const p=await openPage(dev,server,{override:true,settle:100,session:makeStore()}); const n0=server.calls.filter(c=>c.path.includes('grant_type=refresh_token')).length;
  p.CA.state.session.expires_at=Date.now()-1; // force expiry then fire parallel calls
  await Promise.all([p.CA.syncNow(),p.CA.syncNow(),p.CA.syncNow()]).catch(()=>{}); await sleep(100);
  ok('parallel requests share ONE refresh (token rotation safe)',server.calls.filter(c=>c.path.includes('grant_type=refresh_token')).length<=n0+1,String(server.calls.filter(c=>c.path.includes('grant_type=refresh_token')).length-n0)); p.dispose(); }

console.log('\n== S6 network interruption, save & recovery ==');
{ const dev=makeDevice(); const tok=server.issue(U1); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()+3600000}));
  setData(dev,getData(D1)); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:U1.id,base:1,dirty:false,lastSync:1,changedAt:0}));
  const p=await openPage(dev,server,{override:true,settle:300}); const before=dbRow(U1.id).v;
  const d=getData(dev); d.weeks.w2={days:{}}; setData(dev,d); p.sb.data=d; p.CA.noteChange(); server.net=false; await p.CA.syncNow(); await sleep(50);
  ok('offline: status offline, progress kept locally & still dirty',p.CA.state.status==='offline'&&JSON.parse(dev.ls.getItem('codis_sync_meta')).dirty===true&&getData(dev).weeks.w2!==undefined);
  ok('offline: automatic retry scheduled (not dropped)',p.timers.size>0);
  server.net=true; await p.CA.syncNow(); await sleep(100); const row=dbRow(U1.id);
  ok('back online: saved, version incremented, local==cloud',p.CA.state.status==='synced'&&row.v===before+1&&row.d.weeks.w2!==undefined,JSON.stringify({s:p.CA.state.status,v:row&&row.v})); p.dispose(); }

console.log('\n== S8 conflict between two devices ==');
{ const mk=()=>{ const dev=makeDevice(); const tok=server.issue(U1); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()+3600000})); return dev; };
  const base=dbRow(U1.id); const A=mk(), B=mk();
  for(const [dev,tag] of [[A,'A'],[B,'B']]){ setData(dev,Object.assign({},base.d,{tag})); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:U1.id,base:base.v,dirty:true,lastSync:1,changedAt:Date.now()})); }
  const pA=await openPage(A,server,{override:true,settle:400});  // A reconciles+pushes first
  ok('device A saved first (server advanced)',dbRow(U1.id).v===base.v+1&&dbRow(U1.id).d.tag==='A',JSON.stringify(dbRow(U1.id).v));
  const pB=await openPage(B,server,{override:true,settle:500,confirm:[false]});   // B conflicts -> user keeps device copy
  ok('conflict detected & user asked (no silent merge)',pB.sb.__confirms.length===1,String(pB.sb.__confirms.length));
  ok('chose device copy: pushed on top of server version',dbRow(U1.id).d.tag==='B'&&dbRow(U1.id).v===base.v+2,JSON.stringify(dbRow(U1.id).v+':'+dbRow(U1.id).d.tag));
  ok('overwritten account copy kept as local backup',[...B.ls._m.keys()].some(k=>k.startsWith('codis_bk_')));
  pA.dispose(); pB.dispose();
  const C=mk(); setData(C,Object.assign({},base.d,{tag:'C-old'})); C.ls.setItem('codis_sync_meta',JSON.stringify({owner:U1.id,base:base.v,dirty:true,lastSync:1,changedAt:Date.now()}));
  const pC=await openPage(C,server,{override:true,settle:500,confirm:[true]}); 
  ok('chose account copy: device replaced with server data + reload',getData(C).tag==='B'&&pC.reloads===1&&dbRow(U1.id).d.tag==='B'); pC.dispose(); }

console.log('\n== S7 logout / switching accounts / no data leak ==');
{ const dev=makeDevice(); const p0=await openPage(dev,server,{override:true}); await p0.CA.signIn(); const ch=new URL(p0.nav[0]).searchParams.get('code_challenge'); p0.dispose();
  setData(dev,{settings:{},weeks:{wU1:{}}}); const code=server.googleLogin(U1,ch); const p=await openPage(dev,server,{override:true,search:'?code='+code,settle:500});
  const nLogout=server.calls.filter(c=>c.path.includes('/auth/v1/logout')).length; await p.CA.signOut();
  ok('logout: server session revoked',server.calls.filter(c=>c.path.includes('/auth/v1/logout')).length===nLogout+1);
  ok('logout: session + local private data cleared, reload',dev.ls.getItem('codis_auth_session')===null&&dev.ls.getItem('life_organizer_data_v1')===null&&p.reloads>=1);
  p.dispose(); const p2=await openPage(dev,server,{override:true}); ok('after logout: gate shown, no authenticated state',p2.gate.classList.contains('is-open')&&p2.CA.state.user===null); 
  await p2.CA.signIn(); const ch2=new URL(p2.nav[0]).searchParams.get('code_challenge'); p2.dispose();
  const code2=server.googleLogin(U2,ch2); const p3=await openPage(dev,server,{override:true,search:'?code='+code2,settle:500});
  ok('login as different account: signed in as U2',p3.CA.state.user.id===U2.id);
  ok('U1 private data NOT visible to U2 (local)',!JSON.stringify(getData(dev)||{}).includes('wU1'));
  ok('U1 private data NOT written to U2 account (server)',!JSON.stringify(dbRow(U2.id)||{}).includes('wU1')); p3.dispose(); }
{ // switching account without logout while the previous owner has unsynced data
  const dev=makeDevice(); const tok=server.issue(U2); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()+3600000}));
  setData(dev,{settings:{},weeks:{wSECRET_U1:{}}}); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:U1.id,base:3,dirty:true,lastSync:1,changedAt:9}));
  const p=await openPage(dev,server,{override:true,settle:300});
  ok('owner mismatch: previous account data NOT pushed to the new account',!JSON.stringify(dbRow(U2.id)||{}).includes('SECRET_U1'));
  ok('owner mismatch: unsynced data stashed for its owner, device wiped, reload',dev.ls.getItem('codis_acct_'+U1.id)!==null&&dev.ls.getItem('life_organizer_data_v1')===null&&p.reloads===1); p.dispose(); }

console.log('\n== S12 backend errors (missing schema / RLS / large) ==');
{ const mk=()=>{ const dev=makeDevice(); const tok=server.issue(U1); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()+3600000})); setData(dev,{settings:{},weeks:{x:{}}}); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:U1.id,base:dbRow(U1.id).v,dirty:true,lastSync:1,changedAt:1})); return dev; };
  server.failRpc={status:404,body:{code:'PGRST202',message:'Could not find the function public.save_progress'}}; let p=await openPage(mk(),server,{override:true,settle:300});
  ok('missing RPC: Arabic setup hint, status error, NO auto-retry loop',p.CA.state.status==='error'&&/codis_supabase_setup\.sql/.test(p.CA.state.err)&&p.timers.size===0,p.CA.state.err+' timers='+p.timers.size); p.dispose();
  server.failRpc=null; server.failGet={status:404,body:{code:'42P01',message:'relation "public.progress" does not exist'}}; p=await openPage(mk(),server,{override:true,settle:300});
  ok('missing table on read: Arabic setup hint, no retry loop',p.CA.state.status==='error'&&/الجداول|جداول/.test(p.CA.state.err)&&p.timers.size===0,p.CA.state.err); p.dispose();
  server.failGet=null; server.failRpc={status:403,body:{code:'42501',message:'permission denied for table progress'}}; p=await openPage(mk(),server,{override:true,settle:300});
  ok('RLS/permission denied: explicit message, no retry loop',p.CA.state.status==='error'&&/صلاحية/.test(p.CA.state.err)&&p.timers.size===0); p.dispose();
  server.failRpc={status:503,body:{message:'upstream'}}; p=await openPage(mk(),server,{override:true,settle:300});
  ok('5xx: transient — retry scheduled, local data kept',p.CA.state.status==='error'&&p.timers.size>0); p.dispose(); server.failRpc=null; }

console.log('\n== S13 admin gating & protected storage ==');
{ const mk=u=>{ const dev=makeDevice(); const tok=server.issue(u); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()+3600000})); setData(dev,{settings:{}}); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:u.id,base:0,dirty:false,lastSync:1,changedAt:0})); return dev; };
  pgRows(`insert into storage.objects(bucket_id,name) values('dev-addon','dev-addon.js')`);
  const n0=server.calls.length; let p=await openPage(mk(U2),server,{override:true,settle:400});
  ok('non-admin: not admin, add-on storage never requested',p.CA.isAdmin()===false&&!server.calls.slice(n0).some(c=>c.path.includes('/storage/')),JSON.stringify(server.calls.slice(n0).map(c=>c.path))); 
  const tok=server.issue(U2); const direct=await server.fetch(SB+'/storage/v1/object/authenticated/dev-addon/dev-addon.js',{headers:{apikey:ANON,Authorization:'Bearer '+tok.access_token}});
  ok('non-admin direct download of private add-on blocked by server (404)',direct.status===404); p.dispose();
  pgRows(`insert into public.admins(user_id) values('${U1.id}')`); p=await openPage(mk(U1),server,{override:true,settle:400});
  ok('admin (server-verified): add-on loaded',p.CA.isAdmin()===true&&(p.doc.head.children||[]).some(e=>/__devAddonRan/.test(e.textContent||'')),String(p.CA.isAdmin())); p.dispose(); }

console.log('\n== S9 account deletion ==');
{ const dev=makeDevice(); const tok=server.issue(U2); dev.ls.setItem('codis_auth_session',JSON.stringify({access_token:tok.access_token,refresh_token:tok.refresh_token,expires_at:Date.now()+3600000})); setData(dev,{settings:{},weeks:{k:{}}}); dev.ls.setItem('codis_sync_meta',JSON.stringify({owner:U2.id,base:dbRow(U2.id)?dbRow(U2.id).v:0,dirty:false,lastSync:1,changedAt:0}));
  const p=await openPage(dev,server,{override:true,settle:300}); server.rpcFail500=true; const r=await p.CA.deleteAccount({wipeLocal:true}); server.rpcFail500=false;
  ok('server failure: NOT reported as success, session & data kept, error shown',r.ok===false&&dev.ls.getItem('codis_auth_session')!==null&&pgRows(`select count(*) from auth.users where id='${U2.id}'`)[0]==='1'&&p.toasts.some(m=>/لم يُحذف شيء/.test(m)));
  const r2=await p.CA.deleteAccount({wipeLocal:true}); await sleep(250);
  ok('deletion succeeds: server identity + data removed',r2.ok===true&&pgRows(`select count(*) from auth.users where id='${U2.id}'`)[0]==='0'&&pgRows(`select count(*) from public.progress where user_id='${U2.id}'`)[0]==='0');
  ok('deletion: local session and app data wiped',dev.ls.getItem('codis_auth_session')===null&&dev.ls.getItem('life_organizer_data_v1')===null);
  const stale=await server.fetch(SB+'/rest/v1/rpc/save_progress',{method:'POST',headers:{apikey:ANON,Authorization:'Bearer '+tok.access_token},body:JSON.stringify({p_data:{a:1},p_base_version:0})});
  ok('deleted account\'s still-valid JWT cannot recreate data',stale.status===400&&pgRows(`select count(*) from public.progress where user_id='${U2.id}'`)[0]==='0'); p.dispose(); }

console.log('\n'+(failures?('FAILED: '+failures):'ALL PASSED')+'  ('+results.filter(r=>r.pass).length+'/'+results.length+')');
fs.writeFileSync(path.join(__dirname,'js_test_results.json'),JSON.stringify({file:FILE,total:results.length,failures,results},null,1));
process.exit(failures?1:0);
})().catch(e=>{ console.error('HARNESS ERROR',e); process.exit(2); });
