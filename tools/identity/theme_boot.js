/* CODIS-THEME — two looks, one app. "paper" (default, CODIS-ATELIER) and "dark" (the original Obsidian Glass, byte-for-byte).
   The live <style id="codis-theme-css"> holds the paper stylesheet; the dark stylesheet sits inert in <script type="text/plain" id="codis-css-dark">
   (never parsed until chosen, so it costs nothing). The choice is a per-device preference (localStorage `codis_theme_v1`) — it is NOT part of
   the user's data model, never synced, and never touches wallet/inventory/plans. Runs before <body> is parsed, so there is no flash. */
(function(){
  var KEY = 'codis_theme_v1', root = document.documentElement;
  var st = document.getElementById('codis-theme-css'), dk = document.getElementById('codis-css-dark');
  var cur = 'paper', paperCss = null;
  var LABEL = { paper:'ورقي', dark:'داكن' };
  var CHROME = { paper:{ bar:'#E9E0CD', scheme:'light', status:'default' }, dark:{ bar:'#05070B', scheme:'dark', status:'black-translucent' } };
  function read(){ try{ return localStorage.getItem(KEY) === 'dark' ? 'dark' : 'paper'; }catch(e){ return 'paper'; } }
  function meta(name, val){ var m = document.querySelector('meta[name="' + name + '"]'); if(m && m.getAttribute('content') !== val) m.setAttribute('content', val); }
  function chrome(){ var c = CHROME[cur]; meta('theme-color', c.bar); meta('color-scheme', c.scheme); meta('apple-mobile-web-app-status-bar-style', c.status); }
  function paint(){
    var b = document.getElementById('home-theme-state'); if(b) b.textContent = LABEL[cur];
    var opts = document.querySelectorAll('#theme-opts .thm-opt');
    for(var i = 0; i < opts.length; i++){ var on = opts[i].getAttribute('data-theme-opt') === cur; opts[i].setAttribute('aria-checked', on ? 'true' : 'false'); opts[i].tabIndex = on ? 0 : -1; }
  }
  function apply(mode){
    if(mode !== 'dark') mode = 'paper';
    if(mode === cur && root.getAttribute('data-theme') === mode) return false;
    if(!st || !dk) return false;
    if(mode === 'dark'){ if(paperCss === null) paperCss = st.textContent; st.textContent = dk.textContent; }
    else if(paperCss !== null){ st.textContent = paperCss; }
    cur = mode; root.setAttribute('data-theme', mode); chrome(); paint();
    return true;
  }
  var api = {
    get: function(){ return cur; },
    set: function(mode, quiet){
      var changed = apply(mode);
      try{ localStorage.setItem(KEY, cur); }catch(e){}
      if(changed && !quiet){ try{ if(typeof codisSfx === 'function') codisSfx('confirm', { ctx:'switch' }); }catch(e){} }
      return changed;
    },
    paint: paint
  };
  window.CodisTheme = api;
  apply(read());
  document.addEventListener('DOMContentLoaded', paint);
  window.addEventListener('storage', function(e){ if(e.key === KEY) apply(read()); });   /* another tab changed it */
})();
