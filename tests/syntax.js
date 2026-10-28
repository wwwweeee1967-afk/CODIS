const fs=require('fs'),vm=require('vm'),path=require('path');
function check(f){
  const t=fs.readFileSync(f,'utf8'); const re=/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi; let m,n=0,bad=0;
  while((m=re.exec(t))){ n++; try{ new vm.Script(m[1],{filename:f+'#script'+n}); }catch(e){ bad++; console.log('SYNTAX ERROR in script',n,e.message); } }
  console.log(path.basename(f),'inline scripts:',n,'errors:',bad); return bad;
}
// usage: node tests/syntax.js [file.html ...]  (default: src/CODIS_9-7-2.html + app/CODIS_FINAL.html)
const root=path.join(__dirname,'..');
const files=process.argv.length>2?process.argv.slice(2):[path.join(root,'src/CODIS_9-7-2.html'),path.join(root,'app/CODIS_FINAL.html')];
let bad=0; files.forEach(f=>{ bad+=check(f); }); process.exit(bad?1:0);
