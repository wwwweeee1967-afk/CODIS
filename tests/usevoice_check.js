/* CODIS-USE-VOICE v2 check (node): tools/identity/v36_voice.js — multi-concept understanding, dialects, intents, teams, safety, variety, determinism. */
const fs = require('fs'), path = require('path');
const V = new Function(fs.readFileSync(path.join(__dirname, '..', 'tools', 'identity', 'v36_voice.js'), 'utf8') + '; return CodisRewardVoice;')();
let fail = 0; const T = (n, ok, i)=>{ if(!ok) fail++; console.log((ok ? 'PASS ' : 'FAIL ') + n + (ok ? '' : '  -> ' + JSON.stringify(i))); };
const D = n=>V.analyze(n).frames.map(f=>f.d).join('+'), C = n=>V.analyze(n).companions.join('+'), X = (n, s)=>V.compose(n, s || 'k', { hour:14 }).text;
[['برجر', 'eat'], ['اكل برجر وبيتزا', 'eat'], ['مشاهدة مع الأكل', 'watch+eat'], ['فلم وبيتزا مع الشباب', 'watch+eat'], ['مشاهدة مباراة', 'match'], ['اتفرج على ماتش الزوراء', 'match'], ['ساعة بلايستيشن', 'games'],
 ['لعب ببجي', 'games'], ['العب طوبه', 'sport'], ['جيم', 'sport'], ['ساعتين نوم', 'sleep'], ['قيلولة', 'sleep'], ['يوم اوف', 'dayoff'], ['قهوة', 'drink'], ['استكان چاي', 'drink'], ['كنافة', 'sweet'],
 ['طلعة للمول', 'outing'], ['سفرة للشمال', 'outing'], ['اشتري لعبة جديدة', 'shopping'], ['شراء حذاء', 'shopping'], ['ساعه يد', 'shopping'], ['ساعة تيك توك', 'sm'], ['نص ساعة سوشل ميديا', 'sm'],
 ['قراءة رواية', 'learn'], ['كورس انكليزي', 'learn'], ['رسم', 'art'], ['حلاقة', 'care'], ['عيد ميلاد', 'celebrate'], ['اركيلة مع الربع', 'smoke'], ['هاكل شاورما', 'eat'], ['بشوف فلم', 'watch'],
 ['بيتزااا', 'eat'], ['برغرر', 'eat'], ['مسلسل كوري وجكليت', 'watch+sweet'], ['عشا بالمطعم مع حبيبتي', 'eat'], ['مباراة بلايستيشن', 'games'], ['نتفلكس وفشار', 'watch+eat']
].forEach(([n, d])=>T('«' + n + '» → ' + d, D(n) === d, D(n)));
[['فلم وبيتزا مع الشباب', 'الأصدقاء'], ['طلعة للمول ويا اهلي', 'الأهل'], ['عشا مع حبيبتي', 'اللي تحب']].forEach(([n, c])=>T('companion «' + n + '» → ' + c, C(n) === c, C(n)));
T('both items addressed (watch + food)', (t=>/مشاهدة|فرجة|فلم/.test(t) && /البيتزا|عافية|صحتين|الشفا/.test(t))(X('فلم وبيتزا')), X('فلم وبيتزا'));
T('real items echoed («البيتزا»)', /البيتزا/.test(X('اكل بيتزا', 'a1') + X('اكل بيتزا', 'a2') + X('اكل بيتزا', 'a3')));
T('two teams named only from the text', (t=>/ريال مدريد/.test(t) && /برشلونة/.test(t))(X('مباراة ريال مدريد وبرشلونة')), X('مباراة ريال مدريد وبرشلونة'));
T('ambiguous team word without a match is ignored («الاهلي» alone)', !V.analyze('الاهلي').teams.length);
T('«النصر» counts as team inside a match', V.analyze('مباراة النصر').teams[0] === 'النصر');
['شي غريب', 'xyz', 'مكافأة', '!!!', 'ملخبط عجيب'].forEach(n=>{ const a = V.analyze(n); T('unknown «' + n + '» → no fake context', !a.frames.length && !a.companions.length, a.frames); });
T('unknown → elegant generic', /«شي غريب»|بالهنا|مستحقة|ثمرته/.test(X('شي غريب')));
T('no evening closer that contradicts the name', !/ليلتك/.test(V.compose('قهوة الصبح', 'x', { hour:22 }).text));
const tm = V.compose('ساعة سوشل ميديا', 'z', { timed:true }); T('timed: says time started + platform', /بدأ|انطلق/.test(tm.text) && /سوشل|تصفّح|سكرول/.test(tm.text), tm.text);
T('deterministic without memo', V.compose('برجر', 'u1').text === V.compose('برجر', 'u1').text);
const set = new Set(); for(let i = 0; i < 60; i++) set.add(V.compose('برجر', 'uid' + i).text); T('variety for same reward (>=4 distinct)', set.size >= 4, [...set]);
let long = 0, empty = 0; for(let i = 0; i < 200; i++) ['فلم وبيتزا مع الشباب وجكليت', 'نوم', 'مباراة', 'xx'].forEach(n=>{ const t = V.compose(n, 's' + i).text; if(t.length > 110) long++; if(!t.trim()) empty++; }); T('bounded length, never empty', !long && !empty, { long, empty });
T('hostile input safe', ['<script>', '😀😀', '\u0000', 'ا'.repeat(5000), null, undefined, 12, {}].every(x=>typeof V.compose(x, 's').text === 'string'));
V.extend({ domain:'pets2', name:'أليف', n:['وقت حلو ويا الأليف'] }); V.extend({ domain:'pets2', label:'القطة', terms:['قطوه', 'بسه'], say:['دلع للقطة ووقت حلو'] });
T('extend: new domain + terms + say', D('لعب ويا البسه').indexOf('pets2') > -1 && /قطة|الأليف/.test(X('بسه')), [D('لعب ويا البسه'), X('بسه')]);
console.log(fail ? fail + ' FAILED' : 'ALL PASSED'); process.exit(fail ? 1 : 0);
