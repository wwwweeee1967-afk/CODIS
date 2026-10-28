'use strict';
/* Admin-powers isolation tests: stub.sql (+ extra auth.users columns) -> codis_supabase_setup.sql -> codis_admin.sql (twice, idempotency) -> admin_sqltest.sql.
   Usage: NODE_PATH=<dir containing @electric-sql/pglite@0.2.x> node tests/run_admin_sqltest.js   (writes tests/admin_sql_test_results.txt)
   A row is a failure if it says UNEXPECTED, or if a denial test was expected but the action succeeded. */
const fs=require('fs'),path=require('path'); const ROOT=path.join(__dirname,'..');
const {psqlSync}=require('./pglite_bridge.js');
const read=f=>fs.readFileSync(path.join(ROOT,f),'utf8');
const step=(name,args,input)=>{ const r=psqlSync(args,input); if(r.status!==0){ console.log('FAIL',name,r.stderr); process.exit(1); } return r; };
const run=(name,sql)=>step(name,['-q','-v','ON_ERROR_STOP=1','-d','codis_a','-f','-'],sql);
step('create db',['-q','-c','drop database if exists codis_a','-c','create database codis_a']);
run('stub.sql',read('tests/stub.sql'));
run('auth.users extra columns',"alter table auth.users add column if not exists raw_user_meta_data jsonb default '{}'::jsonb, add column if not exists created_at timestamptz default now(), add column if not exists last_sign_in_at timestamptz, add column if not exists banned_until timestamptz;");
run('setup.sql',read('sql/codis_supabase_setup.sql'));
run('admin.sql',read('sql/codis_admin.sql'));
run('admin.sql again (idempotent)',read('sql/codis_admin.sql'));
const r=step('admin_sqltest.sql',['-q','-A','-t','-d','codis_a','-f','-'],read('tests/admin_sqltest.sql'));
const rows=r.stdout.split('\n').filter(l=>l.includes('|')&&/^A\d/.test(l)).map(l=>{ const i=l.indexOf('|'); return [l.slice(0,i),l.slice(i+1)]; });
const w=Math.max(...rows.map(x=>x[0].length));
const out=rows.map(([t,v])=>' '+t.padEnd(w)+' | '+v).join('\n')+'\n';
fs.writeFileSync(path.join(__dirname,'admin_sql_test_results.txt'),out);
process.stdout.write(out);
const bad=rows.filter(x=>/UNEXPECTED/.test(x[1])).length;
console.log('\nrows:',rows.length,' unexpected:',bad, r.stderr?('\nstderr:\n'+r.stderr):'');
process.exit(bad?1:0);
