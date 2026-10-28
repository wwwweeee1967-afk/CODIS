/* Real add-on load flow (no faking of the admin flag) — catches ordering bugs like "adminOK set after the add-on already ran".
   Setup: serve app/ over http AND copy addons/dev-addon.js to app/_addon.js temporarily (private file — delete after!). Open CODIS_FINAL.html on a fresh origin,
   paste this file in the console and call:  await __realFlow()   → expect isAdmin:true, pwr-panel-group:true.
   Change the mocked admins answer to [] to verify a NON-admin gets no panels, no add-on download, and CodisLimits.on() === false. */
window.__realFlow = async function(){
  await new Promise(r=>setTimeout(r,2500));
  const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes('المتابعة بدون حساب')); if(b){ b.click(); await new Promise(r=>setTimeout(r,600)); }
  const SUB='aaaaaaaa-0000-4000-8000-000000000001', b64=o=>btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/=+$/,'').replace(/\+/g,'-').replace(/\//g,'_');
  const tok=b64({alg:'none'})+'.'+b64({sub:SUB,email:'admin@test.local',exp:Math.floor(Date.now()/1000)+3600})+'.sig';
  localStorage.setItem('codis_auth_session', JSON.stringify({access_token:tok, refresh_token:'r', expires_at:Date.now()+3600000}));
  const ofetch=window.fetch.bind(window), addonText=await (await ofetch('/_addon.js')).text(); const log=[];
  window.fetch=async(url,opts)=>{ const u=String(url); log.push(u.replace(/^https?:\/\/[^/]+/,'').slice(0,60));
    const J=(o,s=200)=>new Response(JSON.stringify(o),{status:s,headers:{'Content-Type':'application/json'}});
    if(u.includes('/rest/v1/admins')) return J([{user_id:SUB}]);   // [] for the non-admin case
    if(u.includes('/storage/v1/object/authenticated/dev-addon/')) return new Response(addonText,{status:200});
    if(u.includes('/rpc/save_progress')) return J({ok:true,version:1});
    if(u.includes('/rest/v1/')) return J([]);
    return ofetch(url,opts); };
  CodisAccount.state.session=null; CodisAccount.state.user=null;
  await CodisAccount.init(); await new Promise(r=>setTimeout(r,2500));
  return { isAdmin:CodisAccount.isAdmin(), devLoaded:!!window.__codisDevLoaded, homeRows:['dev-panel-group','adm-panel-group','pwr-panel-group'].map(id=>id+':'+!!document.getElementById(id)).join(' '), calls:log.filter(x=>/admins|storage/.test(x)) };
};
