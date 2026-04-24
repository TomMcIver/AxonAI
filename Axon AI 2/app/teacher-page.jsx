
const { useState, useEffect } = React;

// ── MOCK DATA ──────────────────────────────────────────────────────────────
const MOCK_CLASS = { name:'Year 11 Mathematics', total:24, low:{count:8,avg:38}, mid:{count:10,avg:61}, high:{count:6,avg:85}, overall:61 };
const MOCK_AT_RISK = { name:'Jamie Wilson', initials:'JW', mastery:42, trend:'declining', flags:3, engagement:34 };

const MOCK_CONCEPTS = [
  { name:'Quadratic Equations', pct:85, mastered:18, struggling:2 },
  { name:'Linear Functions',    pct:78, mastered:16, struggling:4 },
  { name:'Trigonometry',        pct:62, mastered:12, struggling:7 },
  { name:'Statistics',          pct:55, mastered:10, struggling:9 },
  { name:'Calculus',            pct:41, mastered:7,  struggling:13 },
  { name:'Probability',         pct:69, mastered:14, struggling:5 },
  { name:'Geometry',            pct:74, mastered:15, struggling:4 },
  { name:'Algebra',             pct:81, mastered:17, struggling:3 },
  { name:'Number Theory',       pct:73, mastered:15, struggling:5 },
  { name:'Functions',           pct:58, mastered:11, struggling:8 },
];

const MOCK_STUDENTS = [
  { name:'Aroha Ngata',    initials:'AN', mastery:72, trend:'improving', engagement:'High',   risk:'low' },
  { name:'Jamie Wilson',   initials:'JW', mastery:42, trend:'declining', engagement:'Low',    risk:'high' },
  { name:'Liam Chen',      initials:'LC', mastery:81, trend:'stable',    engagement:'High',   risk:'low' },
  { name:'Mia Taufa',      initials:'MT', mastery:58, trend:'stable',    engagement:'Medium', risk:'medium' },
  { name:'Daniel Park',    initials:'DP', mastery:67, trend:'improving', engagement:'Medium', risk:'low' },
  { name:'Sofia Russo',    initials:'SR', mastery:44, trend:'declining', engagement:'Low',    risk:'high' },
  { name:'Noah Williams',  initials:'NW', mastery:88, trend:'improving', engagement:'High',   risk:'low' },
  { name:'Zara Ahmed',     initials:'ZA', mastery:63, trend:'stable',    engagement:'Medium', risk:'medium' },
  { name:'Ethan Brown',    initials:'EB', mastery:55, trend:'stable',    engagement:'Medium', risk:'medium' },
  { name:'Lily Nguyen',    initials:'LN', mastery:91, trend:'improving', engagement:'High',   risk:'low' },
];

const TOPIC_STRIP = [
  { depth:'Foundational', concepts:[{name:'Number Theory',pct:73},{name:'Basic Algebra',pct:81},{name:'Geometry',pct:74}] },
  { depth:'Core',         concepts:[{name:'Linear Functions',pct:78},{name:'Quadratic Eq.',pct:85},{name:'Statistics',pct:55}] },
  { depth:'Advanced',     concepts:[{name:'Trigonometry',pct:62},{name:'Probability',pct:69},{name:'Functions',pct:58}] },
  { depth:'Extension',    concepts:[{name:'Calculus',pct:41},{name:'Integration',pct:38}] },
];

const SUBJECTS = [
  { name:'Year 11 Mathematics', students:24, topics:12, avgMastery:61, color:'#2D7D6F' },
  { name:'Year 10 Mathematics', students:28, topics:10, avgMastery:74, color:'#5B6FA6' },
  { name:'Year 12 Statistics',  students:18, topics:8,  avgMastery:68, color:'#8B6914' },
];

const GRAPH_NODES = [
  { id:'a', label:'Number Theory',    x:180, y:420, mastery:73, depth:0 },
  { id:'b', label:'Basic Algebra',    x:300, y:420, mastery:81, depth:0 },
  { id:'c', label:'Geometry',         x:420, y:420, mastery:74, depth:0 },
  { id:'d', label:'Linear Functions', x:180, y:300, mastery:78, depth:1 },
  { id:'e', label:'Quadratic Eq.',    x:300, y:300, mastery:85, depth:1 },
  { id:'f', label:'Statistics',       x:420, y:300, mastery:55, depth:1 },
  { id:'g', label:'Trigonometry',     x:180, y:180, mastery:62, depth:2 },
  { id:'h', label:'Probability',      x:300, y:180, mastery:69, depth:2 },
  { id:'i', label:'Functions',        x:420, y:180, mastery:58, depth:2 },
  { id:'j', label:'Calculus',         x:240, y:70,  mastery:41, depth:3 },
  { id:'k', label:'Integration',      x:360, y:70,  mastery:38, depth:3 },
];

const GRAPH_EDGES = [
  ['a','d'],['b','d'],['b','e'],['c','f'],
  ['d','g'],['e','g'],['e','h'],['f','h'],['f','i'],
  ['g','j'],['h','j'],['i','k'],['j','k'],
];

const SETTINGS_USER = { name:'Ms. Sarah Williams', email:'s.williams@school.nz', subject:'Mathematics', year:'Year 11', avatar:'MW' };

// ── CLASS PULSE ────────────────────────────────────────────────────────────
function ClassPulseSection() {
  const { total, low, mid, high, overall } = MOCK_CLASS;
  const segs = [
    { pct:Math.round(low.count/total*100),  color:'#C0392B', label:'At Risk',   count:low.count,  avg:low.avg },
    { pct:Math.round(mid.count/total*100),  color:'#D97706', label:'On Track',  count:mid.count,  avg:mid.avg },
    { pct:100-Math.round(low.count/total*100)-Math.round(mid.count/total*100), color:'#059669', label:'Excelling', count:high.count, avg:high.avg },
  ];
  return (
    <BlossomCard>
      <SectionLabel>Class Pulse</SectionLabel>
      <SectionTitle>{MOCK_CLASS.name}</SectionTitle>
      <div style={{ fontSize:13, color:'#6B4A3A', fontStyle:'italic', marginTop:4, marginBottom:24 }}>{total} students enrolled</div>
      <div style={{ display:'flex', gap:32, alignItems:'flex-start', flexWrap:'wrap' }}>
        <div style={{ flex:'1 1 240px', minWidth:180 }}>
          <div style={{ display:'flex', height:26, borderRadius:999, overflow:'hidden', gap:2 }}>
            {segs.map((s,i)=>(
              <div key={s.label} style={{ width:`${s.pct}%`, background:s.color, display:'flex', alignItems:'center', justifyContent:'center', borderRadius:i===0?'999px 0 0 999px':i===segs.length-1?'0 999px 999px 0':0 }}>
                {s.pct>8&&<span style={{ fontSize:11, fontWeight:700, color:'white', fontFamily:"'Shippori Mincho',serif" }}>{s.pct}%</span>}
              </div>
            ))}
          </div>
          <div style={{ display:'flex', gap:2, marginTop:9 }}>
            {segs.map(s=>(
              <div key={s.label} style={{ width:`${s.pct}%`, display:'flex', flexDirection:'column', alignItems:'center' }}>
                <span style={{ fontSize:11, fontWeight:500, color:s.color, whiteSpace:'nowrap' }}>{s.label}</span>
                <span style={{ fontSize:10, color:'#6B4A3A', fontStyle:'italic', whiteSpace:'nowrap' }}>{s.count} students</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,auto)', gap:'14px 18px', flexShrink:0 }}>
          <MasteryRing value={low.avg}  label="Low band"  size={70} strokeWidth={7}/>
          <MasteryRing value={mid.avg}  label="Mid band"  size={70} strokeWidth={7}/>
          <MasteryRing value={high.avg} label="High band" size={70} strokeWidth={7}/>
          <MasteryRing value={overall}  label="Overall"   size={70} strokeWidth={7}/>
        </div>
      </div>
    </BlossomCard>
  );
}

// ── MASTERY RING ───────────────────────────────────────────────────────────
function MasteryRing({ value, size=72, strokeWidth=7, label }) {
  const r = (size-strokeWidth)/2, circ = 2*Math.PI*r;
  const [offset, setOffset] = useState(circ);
  const [display, setDisplay] = useState(0);
  useEffect(()=>{
    const t = setTimeout(()=>setOffset(circ*(1-value/100)),120);
    const dur=1300, start=Date.now()+120; let raf;
    const tick=()=>{ const el=Date.now()-start; if(el<0){raf=requestAnimationFrame(tick);return;} const p=Math.min(el/dur,1),e=1-Math.pow(1-p,3); setDisplay(Math.round(e*value)); if(p<1)raf=requestAnimationFrame(tick); };
    raf=requestAnimationFrame(tick);
    return ()=>{ clearTimeout(t); cancelAnimationFrame(raf); };
  },[value]);
  const stroke = value>=70?'#059669':value>=50?'#D97706':'#C0392B';
  return (
    <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:5 }}>
      <div style={{ position:'relative', width:size, height:size }}>
        <svg width={size} height={size}>
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(61,43,31,0.08)" strokeWidth={strokeWidth}/>
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={stroke} strokeWidth={strokeWidth}
            strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
            transform={`rotate(-90 ${size/2} ${size/2})`}
            style={{ transition:'stroke-dashoffset 1300ms cubic-bezier(0.22,0.61,0.36,1)' }}/>
        </svg>
        <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:size>60?14:12, color:'#3D2B1F' }}>{display}%</div>
      </div>
      {label&&<span style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic', textAlign:'center' }}>{label}</span>}
    </div>
  );
}

// ── NEEDS ATTENTION ────────────────────────────────────────────────────────
function NeedsAttentionSection({ navigate }) {
  const s = MOCK_AT_RISK;
  return (
    <BlossomCard style={{ borderLeft:'4px solid #C0392B' }}>
      <SectionLabel>Needs Attention</SectionLabel>
      <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:12, flexWrap:'wrap' }}>
        {NavIcons.alert}
        <span style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:600, fontSize:'1.05rem', color:'#3D2B1F' }}>{s.name}</span>
        <span style={{ padding:'2px 10px', borderRadius:20, background:'rgba(192,57,43,0.1)', color:'#C0392B', fontSize:10, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.06em' }}>At Risk</span>
      </div>
      <p style={{ fontSize:'0.87rem', color:'#6B4A3A', lineHeight:1.75, marginBottom:14 }}>
        Overall mastery at {s.mastery}%, trend declining. {s.flags} active misconception flags — engagement at {s.engagement}%.
      </p>
      <div style={{ background:'rgba(45,125,111,0.05)', border:'1px solid rgba(45,125,111,0.15)', borderRadius:10, padding:'10px 14px', marginBottom:16, display:'flex', gap:10, alignItems:'flex-start' }}>
        <span style={{ color:TEAL, marginTop:1, flexShrink:0 }}>✦</span>
        <p style={{ fontSize:'0.82rem', color:'#6B4A3A', lineHeight:1.65, margin:0 }}>Focused review of prerequisite concepts before continuing. Consider a 1:1 check-in to rebuild confidence.</p>
      </div>
      <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
        <button onClick={()=>navigate('teacher-students')} style={{ padding:'9px 20px', borderRadius:40, border:'1.5px solid rgba(61,43,31,0.2)', background:'transparent', fontFamily:"'Lora',serif", fontSize:'0.85rem', color:'#6B4A3A', cursor:'pointer' }}>View Profile</button>
        <button onClick={()=>navigate('teacher-students')} style={{ padding:'9px 20px', borderRadius:40, border:'none', background:'#3D2B1F', fontFamily:"'Lora',serif", fontSize:'0.85rem', color:'#FDF6EE', cursor:'pointer' }}>Start Intervention</button>
      </div>
    </BlossomCard>
  );
}

// ── TOPIC STRIP ────────────────────────────────────────────────────────────
function TopicStrip() {
  return (
    <BlossomCard style={{ padding:'22px 26px' }}>
      <div style={{ display:'flex', gap:14, overflowX:'auto', paddingBottom:4 }}>
        {TOPIC_STRIP.map(col=>(
          <div key={col.depth} style={{ flex:'1 1 130px', minWidth:120 }}>
            <div style={{ fontSize:9, letterSpacing:'0.18em', textTransform:'uppercase', color:'#6B4A3A', marginBottom:9, fontStyle:'italic' }}>{col.depth}</div>
            <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
              {col.concepts.map(c=>{
                const col2=masteryColor(c.pct);
                return (
                  <div key={c.name} style={{ padding:'9px 11px', borderRadius:10, background:`${col2}11`, border:`1px solid ${col2}33`, cursor:'pointer', transition:'transform 0.18s' }}
                    onMouseEnter={e=>e.currentTarget.style.transform='translateY(-2px)'}
                    onMouseLeave={e=>e.currentTarget.style.transform=''}>
                    <div style={{ fontSize:12, color:'#3D2B1F', fontWeight:500, marginBottom:3, lineHeight:1.3 }}>{c.name}</div>
                    <div style={{ fontSize:13, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:col2 }}>{c.pct}%</div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </BlossomCard>
  );
}

// ── CONCEPT STRENGTHS ──────────────────────────────────────────────────────
function ConceptStrengthsSection() {
  const [sort,setSort]=useState('mastery');
  const sorted=[...MOCK_CONCEPTS].sort((a,b)=>sort==='mastery'?b.pct-a.pct:sort==='alpha'?a.name.localeCompare(b.name):b.mastered-a.mastered);
  return (
    <div>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:14, flexWrap:'wrap', gap:10 }}>
        <SectionTitle>Class Concept Strengths</SectionTitle>
        <div style={{ display:'flex', gap:6 }}>
          {[['mastery','By Mastery'],['alpha','A–Z'],['questions','By Mastered']].map(([key,label])=>(
            <button key={key} onClick={()=>setSort(key)} style={{ padding:'6px 14px', borderRadius:20, border:'1.5px solid #3D2B1F', cursor:'pointer', fontSize:11, background:sort===key?'#3D2B1F':'#FDF6EE', color:sort===key?'#FDF6EE':'#3D2B1F', fontFamily:"'Lora',serif", boxShadow:'2px 2px 0 #3D2B1F', transition:'all 0.15s' }}>{label}</button>
          ))}
        </div>
      </div>
      <BlossomCard style={{ padding:'18px 22px' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:10, paddingBottom:8, borderBottom:'1px solid rgba(61,43,31,0.08)' }}>
          <span style={{ width:175, flexShrink:0, fontSize:10, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.06em', color:'#6B4A3A' }}>Concept</span>
          <span style={{ flex:1, fontSize:10, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.06em', color:'#6B4A3A' }}>Class Mastery</span>
          <span style={{ width:38, textAlign:'right', fontSize:10, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.06em', color:'#6B4A3A' }}>%</span>
        </div>
        {sorted.map((c,i)=>{
          const col=masteryColor(c.pct);
          return (
            <div key={c.name} style={{ display:'flex', alignItems:'center', gap:10, padding:'8px 6px', borderRadius:8, borderBottom:i<sorted.length-1?'1px solid rgba(61,43,31,0.06)':'none', transition:'background 0.12s', cursor:'pointer' }}
              onMouseEnter={e=>e.currentTarget.style.background='rgba(45,125,111,0.04)'}
              onMouseLeave={e=>e.currentTarget.style.background=''}>
              <span style={{ width:175, flexShrink:0, fontSize:13, color:'#3D2B1F', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{c.name}</span>
              <div style={{ flex:1, height:8, borderRadius:4, background:'rgba(61,43,31,0.08)' }}>
                <div style={{ width:`${c.pct}%`, height:'100%', borderRadius:4, background:col, transition:'width 0.6s cubic-bezier(0.16,1,0.3,1)' }}/>
              </div>
              <span style={{ width:38, textAlign:'right', fontSize:12, fontWeight:600, color:col, fontFamily:"'Shippori Mincho',serif" }}>{c.pct}%</span>
            </div>
          );
        })}
      </BlossomCard>
    </div>
  );
}

// ── TEACHER DASHBOARD ──────────────────────────────────────────────────────
function TeacherDashboard({ navigate, currentPage }) {
  return (
    <DashboardShell subtitle="Year 11 Mathematics · Mastery signal" role="teacher" navigate={navigate} currentPage={currentPage}>
      <div style={{ display:'flex', flexDirection:'column', gap:22 }}>
        <div style={{ display:'grid', gridTemplateColumns:'minmax(0,1.5fr) minmax(0,1fr)', gap:22 }}>
          <ClassPulseSection/>
          <NeedsAttentionSection navigate={navigate}/>
        </div>
        <div>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12 }}>
            <div><SectionLabel>Class mastery snapshot</SectionLabel><SectionTitle>Topic overview by depth</SectionTitle></div>
            <button onClick={()=>navigate('teacher-graph')} style={{ padding:'8px 18px', borderRadius:40, border:'1.5px solid rgba(61,43,31,0.18)', background:'transparent', fontFamily:"'Lora',serif", fontSize:'0.83rem', color:'#6B4A3A', cursor:'pointer', fontStyle:'italic' }}>Full map →</button>
          </div>
          <TopicStrip/>
        </div>
        <ConceptStrengthsSection/>
      </div>
    </DashboardShell>
  );
}

// ── TEACHER STUDENTS ───────────────────────────────────────────────────────
function TeacherStudentsPage({ navigate, currentPage }) {
  const [search,setSearch]=useState('');
  const [filter,setFilter]=useState('all');
  const filtered=MOCK_STUDENTS.filter(s=>{
    const matchSearch=s.name.toLowerCase().includes(search.toLowerCase());
    const matchFilter=filter==='all'||s.risk===filter;
    return matchSearch&&matchFilter;
  });
  return (
    <DashboardShell subtitle="Year 11 · All Students" role="teacher" navigate={navigate} currentPage={currentPage}>
      <div style={{ display:'flex', flexDirection:'column', gap:18 }}>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:12 }}>
          <div><SectionLabel>Year 11 Mathematics</SectionLabel><SectionTitle>All Students</SectionTitle></div>
          <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
            <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search students…" style={{ padding:'9px 16px', borderRadius:40, border:'1.5px solid rgba(61,43,31,0.15)', background:'white', fontFamily:"'Lora',serif", fontSize:13, color:'#3D2B1F', outline:'none', width:200 }}/>
            <div style={{ display:'flex', gap:6 }}>
              {[['all','All'],['low','On Track'],['medium','Watch'],['high','At Risk']].map(([val,label])=>(
                <button key={val} onClick={()=>setFilter(val)} style={{ padding:'8px 14px', borderRadius:20, border:'1.5px solid rgba(61,43,31,0.15)', cursor:'pointer', fontSize:12, fontFamily:"'Lora',serif", background:filter===val?'#3D2B1F':'white', color:filter===val?'#FDF6EE':'#6B4A3A', transition:'all 0.15s' }}>{label}</button>
              ))}
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14 }}>
          {[
            { label:'Total Students', val:MOCK_STUDENTS.length, color:TEAL },
            { label:'On Track',       val:MOCK_STUDENTS.filter(s=>s.risk==='low').length,    color:'#059669' },
            { label:'Needs Watch',    val:MOCK_STUDENTS.filter(s=>s.risk==='medium').length, color:'#D97706' },
            { label:'At Risk',        val:MOCK_STUDENTS.filter(s=>s.risk==='high').length,   color:'#C0392B' },
          ].map(stat=>(
            <BlossomCard key={stat.label} style={{ padding:'18px 20px', textAlign:'center' }}>
              <div style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:800, fontSize:'2rem', color:stat.color }}>{stat.val}</div>
              <div style={{ fontSize:12, color:'#6B4A3A', fontStyle:'italic', marginTop:4 }}>{stat.label}</div>
            </BlossomCard>
          ))}
        </div>

        <BlossomCard style={{ padding:0, overflow:'hidden' }}>
          {/* Table header */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr auto auto auto auto', gap:16, padding:'12px 24px', borderBottom:'1px solid rgba(61,43,31,0.08)', background:'rgba(253,246,238,0.5)' }}>
            {['Student','Mastery','Trend','Engagement','Risk'].map(h=>(
              <div key={h} style={{ fontSize:10, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.1em', color:'#6B4A3A' }}>{h}</div>
            ))}
          </div>
          {filtered.map((s,i)=>{
            const riskCol=s.risk==='high'?'#C0392B':s.risk==='medium'?'#D97706':'#059669';
            const trendIcon=s.trend==='improving'?'↑':s.trend==='declining'?'↓':'→';
            const trendCol=s.trend==='improving'?'#059669':s.trend==='declining'?'#C0392B':'#6B4A3A';
            return (
              <div key={s.name} style={{ display:'grid', gridTemplateColumns:'1fr auto auto auto auto', gap:16, alignItems:'center', padding:'14px 24px', borderBottom:i<filtered.length-1?'1px solid rgba(61,43,31,0.06)':'none', transition:'background 0.15s', cursor:'pointer' }}
                onMouseEnter={e=>e.currentTarget.style.background='rgba(253,246,238,0.8)'}
                onMouseLeave={e=>e.currentTarget.style.background=''}>
                <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                  <div style={{ width:38, height:38, borderRadius:'50%', background:`${riskCol}18`, border:`1.5px solid ${riskCol}44`, display:'flex', alignItems:'center', justifyContent:'center', fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:12, color:riskCol, flexShrink:0 }}>{s.initials}</div>
                  <div>
                    <div style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:600, fontSize:14, color:'#3D2B1F' }}>{s.name}</div>
                    <div style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>Year 11</div>
                  </div>
                </div>
                <div style={{ fontSize:16, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:masteryColor(s.mastery), minWidth:48, textAlign:'center' }}>{s.mastery}%</div>
                <div style={{ fontSize:18, fontWeight:700, color:trendCol, minWidth:32, textAlign:'center' }}>{trendIcon}</div>
                <div style={{ fontSize:12, color:'#6B4A3A', fontStyle:'italic', minWidth:60, textAlign:'center' }}>{s.engagement}</div>
                <div style={{ width:10, height:10, borderRadius:'50%', background:riskCol, flexShrink:0, margin:'0 auto' }}/>
              </div>
            );
          })}
          {filtered.length===0&&<div style={{ padding:'32px', textAlign:'center', color:'#6B4A3A', fontStyle:'italic' }}>No students match your filter.</div>}
        </BlossomCard>
      </div>
    </DashboardShell>
  );
}

// ── TEACHER SUBJECTS ───────────────────────────────────────────────────────
function TeacherSubjectsPage({ navigate, currentPage }) {
  return (
    <DashboardShell subtitle="My Subjects" role="teacher" navigate={navigate} currentPage={currentPage}>
      <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
          <div><SectionLabel>Teaching Portfolio</SectionLabel><SectionTitle>My Subjects</SectionTitle></div>
          <button style={{ display:'flex', alignItems:'center', gap:8, padding:'10px 20px', borderRadius:40, border:'none', background:'#3D2B1F', color:'#FDF6EE', fontFamily:"'Lora',serif", fontSize:13, cursor:'pointer' }}>
            {NavIcons.plus} Add Subject
          </button>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(300px,1fr))', gap:20 }}>
          {SUBJECTS.map(sub=>(
            <BlossomCard key={sub.name} style={{ cursor:'pointer', transition:'transform 0.2s, box-shadow 0.2s' }}
              onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-4px)';e.currentTarget.style.boxShadow='0 12px 40px rgba(61,43,31,0.1)';}}
              onMouseLeave={e=>{e.currentTarget.style.transform='';e.currentTarget.style.boxShadow='';}}>
              <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:16 }}>
                <div style={{ width:44, height:44, borderRadius:12, background:`${sub.color}15`, border:`1.5px solid ${sub.color}30`, display:'flex', alignItems:'center', justifyContent:'center' }}>
                  {NavIcons.book}
                </div>
                <span style={{ padding:'3px 12px', borderRadius:20, background:`${masteryColor(sub.avgMastery)}14`, color:masteryColor(sub.avgMastery), fontSize:11, fontWeight:600 }}>{sub.avgMastery}% avg</span>
              </div>
              <h3 style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:'1.1rem', color:'#3D2B1F', marginBottom:12 }}>{sub.name}</h3>
              <div style={{ display:'flex', gap:20 }}>
                <div><div style={{ fontSize:18, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:'#3D2B1F' }}>{sub.students}</div><div style={{ fontSize:11, color:'#6B4A3A' }}>Students</div></div>
                <div><div style={{ fontSize:18, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:'#3D2B1F' }}>{sub.topics}</div><div style={{ fontSize:11, color:'#6B4A3A' }}>Topics</div></div>
              </div>
              <div style={{ marginTop:14, height:6, borderRadius:4, background:'rgba(61,43,31,0.08)' }}>
                <div style={{ width:`${sub.avgMastery}%`, height:'100%', borderRadius:4, background:masteryColor(sub.avgMastery) }}/>
              </div>
            </BlossomCard>
          ))}
        </div>

        {/* Recent topics table */}
        <div>
          <SectionTitle style={{ marginBottom:14 }}>Topic Performance</SectionTitle>
          <BlossomCard style={{ padding:0, overflow:'hidden' }}>
            {MOCK_CONCEPTS.slice(0,6).map((c,i)=>(
              <div key={c.name} style={{ display:'flex', alignItems:'center', gap:16, padding:'14px 24px', borderBottom:i<5?'1px solid rgba(61,43,31,0.06)':'none' }}>
                <span style={{ flex:1, fontSize:14, color:'#3D2B1F' }}>{c.name}</span>
                <div style={{ width:140, height:7, borderRadius:4, background:'rgba(61,43,31,0.08)' }}>
                  <div style={{ width:`${c.pct}%`, height:'100%', borderRadius:4, background:masteryColor(c.pct) }}/>
                </div>
                <span style={{ width:42, textAlign:'right', fontSize:13, fontWeight:600, color:masteryColor(c.pct), fontFamily:"'Shippori Mincho',serif" }}>{c.pct}%</span>
                <span style={{ width:90, fontSize:11, color:'#6B4A3A', fontStyle:'italic', textAlign:'right' }}>{c.mastered} mastered</span>
              </div>
            ))}
          </BlossomCard>
        </div>
      </div>
    </DashboardShell>
  );
}

// ── KNOWLEDGE GRAPH ────────────────────────────────────────────────────────
function TeacherGraphPage({ navigate, currentPage }) {
  const [selected,setSelected]=useState(null);
  const selNode=GRAPH_NODES.find(n=>n.id===selected);

  return (
    <DashboardShell subtitle="Knowledge Graph · Mathematics" role="teacher" navigate={navigate} currentPage={currentPage}>
      <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:12 }}>
          <div><SectionLabel>Year 11 Mathematics</SectionLabel><SectionTitle>Concept Knowledge Graph</SectionTitle></div>
          <div style={{ display:'flex', gap:14, alignItems:'center' }}>
            {[['#059669','Strong ≥70%'],['#D97706','Developing 50–69%'],['#C0392B','Focus <50%']].map(([c,l])=>(
              <div key={l} style={{ display:'flex', alignItems:'center', gap:6 }}>
                <div style={{ width:10, height:10, borderRadius:'50%', background:c }}/>
                <span style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>{l}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1fr 280px', gap:20, alignItems:'start' }}>
          {/* Graph canvas */}
          <BlossomCard style={{ padding:16 }}>
            <svg viewBox="0 0 560 480" style={{ width:'100%' }}>
              {/* Depth labels */}
              {['Foundational','Core','Advanced','Extension'].map((d,di)=>(
                <text key={d} x="10" y={[445,325,205,90][di]} fontSize="10" fill="rgba(107,74,58,0.5)" fontStyle="italic" fontFamily="Georgia,serif">{d}</text>
              ))}
              {/* Grid lines */}
              {[440,320,200,80].map(y=>(
                <line key={y} x1="80" y1={y} x2="540" y2={y} stroke="rgba(61,43,31,0.06)" strokeWidth="1" strokeDasharray="4 4"/>
              ))}
              {/* Edges */}
              {GRAPH_EDGES.map(([a,b])=>{
                const na=GRAPH_NODES.find(n=>n.id===a), nb=GRAPH_NODES.find(n=>n.id===b);
                return <line key={`${a}-${b}`} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke="rgba(61,43,31,0.15)" strokeWidth="1.5"/>;
              })}
              {/* Nodes */}
              {GRAPH_NODES.map(node=>{
                const col=masteryColor(node.mastery);
                const isSel=selected===node.id;
                return (
                  <g key={node.id} onClick={()=>setSelected(isSel?null:node.id)} style={{ cursor:'pointer' }}>
                    <circle cx={node.x} cy={node.y} r={isSel?28:22} fill={`${col}18`} stroke={col} strokeWidth={isSel?2.5:1.5}/>
                    <text x={node.x} y={node.y-2} textAnchor="middle" fontSize="10" fill="#3D2B1F" fontWeight="600" fontFamily="Georgia,serif">{node.mastery}%</text>
                    <text x={node.x} y={node.y+28+10} textAnchor="middle" fontSize="9" fill="#6B4A3A" fontFamily="Georgia,serif">{node.label.split(' ')[0]}</text>
                    {node.label.split(' ').length>1&&<text x={node.x} y={node.y+38+10} textAnchor="middle" fontSize="9" fill="#6B4A3A" fontFamily="Georgia,serif">{node.label.split(' ').slice(1).join(' ')}</text>}
                  </g>
                );
              })}
            </svg>
          </BlossomCard>

          {/* Detail panel */}
          <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
            {selNode ? (
              <BlossomCard>
                <SectionLabel>Selected Concept</SectionLabel>
                <SectionTitle style={{ marginBottom:12 }}>{selNode.label}</SectionTitle>
                <div style={{ display:'flex', justifyContent:'center', marginBottom:16 }}>
                  <MasteryRing value={selNode.mastery} size={80} strokeWidth={8} label="Class mastery"/>
                </div>
                {[
                  ['Depth level', ['Foundational','Core','Advanced','Extension'][selNode.depth]],
                  ['Students on track', `${Math.round(selNode.mastery/100*MOCK_CLASS.total)}`],
                  ['Needing support', `${MOCK_CLASS.total - Math.round(selNode.mastery/100*MOCK_CLASS.total)}`],
                ].map(([k,v])=>(
                  <div key={k} style={{ display:'flex', justifyContent:'space-between', padding:'8px 0', borderBottom:'1px solid rgba(61,43,31,0.07)' }}>
                    <span style={{ fontSize:12, color:'#6B4A3A', fontStyle:'italic' }}>{k}</span>
                    <span style={{ fontSize:13, fontWeight:500, color:'#3D2B1F' }}>{v}</span>
                  </div>
                ))}
                <button onClick={()=>setSelected(null)} style={{ marginTop:14, width:'100%', padding:'8px', borderRadius:10, border:'1px solid rgba(61,43,31,0.15)', background:'transparent', fontFamily:"'Lora',serif", fontSize:12, color:'#6B4A3A', cursor:'pointer' }}>Clear selection</button>
              </BlossomCard>
            ) : (
              <BlossomCard style={{ textAlign:'center', padding:32 }}>
                <BlossomTree style={{ width:80, height:100, opacity:0.2, margin:'0 auto 12px' }}/>
                <p style={{ fontSize:13, color:'#6B4A3A', fontStyle:'italic', lineHeight:1.7 }}>Click any concept node to see cohort details</p>
              </BlossomCard>
            )}

            {/* Legend */}
            <BlossomCard style={{ padding:'16px 18px' }}>
              <div style={{ fontSize:11, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.1em', color:'#6B4A3A', marginBottom:10 }}>Mastery Scale</div>
              {[['#059669','≥ 70%','Strong'],['#D97706','50–69%','Developing'],['#C0392B','< 50%','Focus area']].map(([c,range,label])=>(
                <div key={label} style={{ display:'flex', alignItems:'center', gap:10, marginBottom:8 }}>
                  <div style={{ width:28, height:28, borderRadius:'50%', background:`${c}18`, border:`1.5px solid ${c}`, flexShrink:0 }}/>
                  <div>
                    <div style={{ fontSize:12, fontWeight:500, color:'#3D2B1F' }}>{label}</div>
                    <div style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>{range}</div>
                  </div>
                </div>
              ))}
            </BlossomCard>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}

// ── TEACHER SETTINGS ───────────────────────────────────────────────────────
function TeacherSettingsPage({ navigate, currentPage }) {
  const [u,setU]=useState(SETTINGS_USER);
  const [saved,setSaved]=useState(false);
  const save=()=>{ setSaved(true); setTimeout(()=>setSaved(false),2500); };
  const field=(label,key,type='text')=>(
    <div key={key} style={{ marginBottom:18 }}>
      <label style={{ display:'block', fontSize:11, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.1em', color:'#6B4A3A', marginBottom:6 }}>{label}</label>
      <input type={type} value={u[key]} onChange={e=>setU({...u,[key]:e.target.value})} style={{ width:'100%', padding:'11px 16px', borderRadius:12, border:'1.5px solid rgba(61,43,31,0.15)', background:'white', fontFamily:"'Lora',serif", fontSize:14, color:'#3D2B1F', outline:'none', transition:'border-color 0.2s' }}
        onFocus={e=>e.target.style.borderColor=TEAL}
        onBlur={e=>e.target.style.borderColor='rgba(61,43,31,0.15)'}/>
    </div>
  );
  return (
    <DashboardShell subtitle="Settings" role="teacher" navigate={navigate} currentPage={currentPage}>
      <div style={{ maxWidth:680, display:'flex', flexDirection:'column', gap:20 }}>
        <div><SectionLabel>Account</SectionLabel><SectionTitle>Profile Settings</SectionTitle></div>

        {/* Avatar */}
        <BlossomCard style={{ display:'flex', alignItems:'center', gap:20 }}>
          <div style={{ width:72, height:72, borderRadius:'50%', background:TEAL_BG, border:`2px solid ${TEAL_BORDER}`, display:'flex', alignItems:'center', justifyContent:'center', fontFamily:"'Shippori Mincho',serif", fontWeight:800, fontSize:26, color:TEAL, flexShrink:0 }}>{u.avatar}</div>
          <div>
            <div style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:'1.1rem', color:'#3D2B1F' }}>{u.name}</div>
            <div style={{ fontSize:12, color:'#6B4A3A', fontStyle:'italic', marginTop:2 }}>{u.subject} · {u.year}</div>
          </div>
        </BlossomCard>

        <BlossomCard>
          <div style={{ fontSize:12, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.1em', color:'#6B4A3A', marginBottom:18 }}>Personal Information</div>
          {field('Full Name','name')}
          {field('Email Address','email','email')}
          {field('Subject','subject')}
          {field('Year Level','year')}
        </BlossomCard>

        <BlossomCard>
          <div style={{ fontSize:12, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.1em', color:'#6B4A3A', marginBottom:18 }}>Notifications</div>
          {[['Student at-risk alerts','Receive alerts when a student drops below threshold'],['Weekly class summary','Email digest every Monday morning'],['Lightbulb moments','Notify when a student has a breakthrough']].map(([title,desc],i)=>(
            <div key={i} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:14, paddingBottom:14, borderBottom:i<2?'1px solid rgba(61,43,31,0.07)':'none' }}>
              <div>
                <div style={{ fontSize:13, fontWeight:500, color:'#3D2B1F' }}>{title}</div>
                <div style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic', marginTop:2 }}>{desc}</div>
              </div>
              <div style={{ width:44, height:24, borderRadius:12, background:TEAL, position:'relative', cursor:'pointer', flexShrink:0 }}>
                <div style={{ position:'absolute', right:3, top:3, width:18, height:18, borderRadius:'50%', background:'white' }}/>
              </div>
            </div>
          ))}
        </BlossomCard>

        <div style={{ display:'flex', gap:12 }}>
          <button onClick={save} style={{ flex:1, padding:'13px', borderRadius:12, border:'none', background:'#3D2B1F', fontFamily:"'Lora',serif", fontSize:14, color:'#FDF6EE', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', gap:8, transition:'background 0.2s' }}
            onMouseEnter={e=>e.target.style.background=TEAL}
            onMouseLeave={e=>e.target.style.background='#3D2B1F'}>
            {saved ? <>{NavIcons.check} Saved!</> : 'Save changes'}
          </button>
          <button onClick={()=>setU(SETTINGS_USER)} style={{ padding:'13px 24px', borderRadius:12, border:'1.5px solid rgba(61,43,31,0.15)', background:'transparent', fontFamily:"'Lora',serif", fontSize:14, color:'#6B4A3A', cursor:'pointer' }}>Reset</button>
        </div>
      </div>
    </DashboardShell>
  );
}

Object.assign(window, {
  MasteryRing,
  TeacherDashboard,
  TeacherStudentsPage,
  TeacherSubjectsPage,
  TeacherGraphPage,
  TeacherSettingsPage,
});
