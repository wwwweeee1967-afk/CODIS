'use strict';
/* Runs stub.sql -> codis_supabase_setup.sql (twice, idempotency) -> sqltest.sql on PGlite and writes sql_test_results.txt.
   Usage: NODE_PATH=<dir containing @electric-sql/pglite@0.2.x> node tests/run_sqltest.js
   (On Linux with PostgreSQL 16 the same files can be run with psql directly.) */
const fs=require('fs'),path=require('path'); const ROOT=path.join(__dirname,'..');
const {psqlSync}=require('./pglite_bridge.js');
const read=f=>fs.readFileSync(path.join(ROOT,f),'utf8');
const step=(name,args,input)=>{ const r=psqlSync(args,input); if(r.status!==0){ console.log('FAIL',name,r.stderr); process.exit(1); } return r; };
step('create db',['-q','-c','drop database if exists codis_t','-c','create database codis_t']);
step('stub.sql',['-q','-v','ON_ERROR_STOP=1','-d','codis_t','-f','-'],read('tests/stub.sql'));
step('setup.sql',['-q','-v','ON_ERROR_STOP=1','-d','codis_t','-f','-'],read('sql/codis_supabase_setup.sql'));
step('setup.sql again (idempotent)',['-q','-v','ON_ERROR_STOP=1','-d','codis_t','-f','-'],read('sql/codis_supabase_setup.sql'));
const r=step('sqltest.sql',['-q','-A','-t','-d','codis_t','-f','-'],read('tests/sqltest.sql'));
const rows=r.stdout.split('\n').filter(l=>l.includes('|')&&/^T\d/.test(l)).map(l=>{ const i=l.indexOf('|'); return [l.slice(0,i),l.slice(i+1)]; });
const w=Math.max(...rows.map(x=>x[0].length));
const out=rows.map(([t,v])=>' '+t.padEnd(w)+' | '+v).join('\n')+'\n';
fs.writeFileSync(path.join(__dirname,'sql_test_results.txt'),out);
process.stdout.write(out);
const unexpected=rows.filter(x=>/UNEXPECTED/.test(x[1])).length;
console.log('\nrows:',rows.length,' unexpected:',unexpected, r.stderr?('\nstderr:\n'+r.stderr):'');
process.exit(unexpected?1:0);
