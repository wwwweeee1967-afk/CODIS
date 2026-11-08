    /* ===== CODIS-USE-CINE · أصوات مشهد استخدام المكافأة (ورق · حبر · خشب · صندوق موسيقى) — كلها مولّدة، قناة المكافآت، تتدرج بالمستوى (o.lv) ===== */
    'use.whoosh':     { ch:'reward', p:3, cd:0, fn(v,o){ const lv = o.lv || 1, d = .34 + lv * .025;   /* بطاقة ورق تشق الهواء */
                        v.noise({ dur:d, peak:.045 + lv * .004, type:'bandpass', f:420, f2:2600 + lv * 90, q:.75, a:d * .6 });
                        v.grains({ t:d * .15, dur:d * .75, n:5, peak:.011, f:3800, gd:.01, type:'highpass', shape:'swell' });
                        v.tone({ f:160, f2:92, dur:d + .08, a:d * .55, peak:.034, lp:360, partials:BODY });
                        v.pan(-.3); v.panTo(.08, d); } },
    'use.flip':       { ch:'reward', p:3, cd:0, fn(v,o){ const n = Math.max(1, Math.min(2, o.n || 1));   /* رفرفة ورق ثم «فلاب» كارتوني وطقّة نظيفة */
                        for(let k = 0; k < n; k++){ const t = k * .15;
                          v.grains({ t:t, dur:.14, n:6, peak:.028, f:2400, gd:.012, type:'bandpass', shape:'swell' });
                          v.noise({ t:t + .13, dur:.04, peak:.045, type:'bandpass', f:1700, q:1.2, a:.002 }); }
                        v.noise({ t:n * .15 + .02, dur:.035, peak:.04, type:'highpass', f:2600, a:.001 });
                        v.tone({ t:n * .15 + .02, f:900, f2:600, dur:.05, a:.002, peak:.008 }); } },
    'use.land':       { ch:'reward', p:3, cd:0, fn(v){ v.noise({ dur:.08, peak:.05, type:'lowpass', f:1200, f2:450, a:.003 }); v.strike('wood', 230, .04, 0, { decay:.7, ex:.25 }); } },
    'use.drop':       { ch:'reward', p:3, cd:0, fn(v){ v.noise({ dur:.14, peak:.045, type:'bandpass', f:700, f2:1800, q:.9, a:.11 }); } },   /* الختم ينزل */
    'use.stamp':      { ch:'reward', p:3, cd:0, wet:.1, duck:true, fn(v,o){ const lv = o.lv || 1, k = .78 + lv * .045, foil = o.foil || 'ink';   /* ختم مطاط على ورق سميك فوق مكتب خشب */
                        v.tone({ f:118, f2:54, dur:.24, a:.002, peak:.17 * k, lp:360, partials:BODY });
                        v.strike('wood', 140, .085 * k, 0, { decay:1.1, ex:.5, exF:800 });
                        v.noise({ dur:.055, peak:.09 * k, type:'bandpass', f:1500, q:.6, a:.0006 });
                        v.noise({ t:.012, dur:.18, peak:.04, type:'lowpass', f:900, f2:160, a:.015 });
                        v.grains({ t:.03, dur:.08, n:4, peak:.01, f:2200, gd:.01, type:'bandpass' });
                        v.tone({ t:.004, f:340, f2:150, dur:.12, a:.002, peak:.045, partials:SOFT });
                        if(lv >= 5) v.tone({ f:62, f2:36, dur:.55, a:.005, peak:.09 + .01 * (lv - 5), lp:150 });
                        if(foil === 'gold' || foil === 'holo' || foil === 'prism') v.strike('gold', N.A5, .03, .03, { decay:1.1, bright:.55 });
                        else if(foil === 'copper') v.strike('bronze', N.D5, .022, .03, { decay:.7 });
                        if(foil === 'prism') v.strike('crystal', N.E6, .018, .05, { decay:.9 }); } },
    'use.check':      { ch:'reward', p:3, cd:0, fn(v){ v.grains({ dur:.22, n:11, peak:.04, f:3600, gd:.011, type:'bandpass', shape:'swell' }); v.noise({ t:.21, dur:.025, peak:.02, type:'highpass', f:4200 }); } },   /* ريشة حبر */
    'use.tick':       { ch:'reward', p:3, cd:0, wet:.12, fn(v){ v.strike('wood', 2000, .035, 0, { decay:.25, ex:.4 }); v.strike('wood', 1580, .032, .17, { decay:.25, ex:.4 }); v.tone({ t:.34, f:N.A5, dur:.9, a:.002, peak:.022, partials:BELL }); } },   /* ساعة جيب قديمة */
    'use.sparkle':    { ch:'reward', p:3, cd:0, wet:.25, fn(v,o){ const lv = o.lv || 1, S = [N.A5, N.D6, N.E6, N.Fs6, N.A5 * 2, N.B5 * 2, N.D6 * 2], n = Math.min(7, 2 + Math.round(lv * .6)), gap = lv >= 6 ? .055 : .065;   /* صندوق موسيقى + لمعة */
                        for(let i = 0; i < n; i++) v.tone({ t:i * gap, f:S[i], dur:.8, a:.002, peak:.028 * (1 - i * .05), partials:BELL });
                        v.grains({ t:.02, dur:.4 + lv * .06, n:6 + lv * 3, peak:.01, f:7500, gd:.008, type:'highpass', shape:'fade' });
                        if(lv >= 4) [N.D4, N.Fs4, N.A4].forEach((f, i)=>v.tone({ t:.06, f:f, dur:1.4 + lv * .08, a:.3, peak:.012 + .0015 * lv, lp:1600, partials:SOFT, det:i * 4 }));
                        if(lv >= 7) v.strike('crystal', N.D6, .018, .12, { decay:1.2 });
                        if(lv >= 9){ v.tone({ t:.05, f:N.D3, dur:2.2, a:.4, peak:.03, lp:500, partials:BODY }); v.fm({ t:.1, f:N.D5, ratio:3.5, index:3, index2:.1, dur:2, peak:.02 }); } } },
    'use.tag':        { ch:'reward', p:2, cd:0, max:4, fn(v,o){ const i = o.i || 0; v.strike('poly', [1250, 1400, 1570, 1760][i % 4], .024, 0, { ex:.35 }); v.noise({ dur:.018, peak:.01, type:'bandpass', f:2600, q:2 }); } },   /* وسم ورقي */
    'use.word':       { ch:'reward', p:2, cd:0, max:8, fn(v,o){ const i = o.i || 0; v.noise({ dur:.028, peak:.016, type:'bandpass', f:1300 + (i % 5) * 140, q:1.8, a:.0008 }); v.tone({ f:210 + (i % 4) * 14, dur:.045, a:.001, peak:.008, lp:800 }); } },   /* حرف مطبعي */
    'use.close':      { ch:'reward', p:2, cd:200, fn(v){ v.noise({ dur:.24, peak:.03, type:'bandpass', f:2600, f2:700, q:.8, a:.06 }); v.grains({ dur:.18, n:4, peak:.008, f:3200, gd:.01 }); v.strike('wood', 260, .02, .06, { decay:.5, ex:.2 }); } },   /* الورقة تنسحب */
