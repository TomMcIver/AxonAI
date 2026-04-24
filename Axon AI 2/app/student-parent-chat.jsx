
const { useState, useEffect, useRef } = React;

// ── STUDENT MOCK DATA ──────────────────────────────────────────────────────
const STUDENT_DATA = {
  name:'Aroha', lastName:'Ngata', year:12,
  subjects:[
    { subject:'Mathematics', pct:68, concepts:14 },
    { subject:'Biology',     pct:74, concepts:11 },
  ],
  weakest:[
    { name:'Integration',      pct:42 },
    { name:'Probability',      pct:51 },
    { name:'Cell Division',    pct:55 },
    { name:'Quadratic Roots',  pct:58 },
    { name:'Vectors',          pct:62 },
  ],
  trend:'improving', aiChats:23, lightbulbs:4,
  engagementHistory:[45,52,48,61,58,70,65,72,68,78],
  focusAreas:[
    { concept:'Integration by Parts', type:'stuck_on_concept', subject:'Mathematics' },
    { concept:'Probability Trees',    type:'low_engagement',   subject:'Mathematics' },
    { concept:'Mitosis vs Meiosis',   type:'stuck_on_concept', subject:'Biology' },
  ],
  sessions:[
    { id:1, concept:'Quadratic Equations', subject:'Mathematics', engagement:82, lightbulb:true },
    { id:2, concept:'Cell Respiration',    subject:'Biology',     engagement:76, lightbulb:false },
    { id:3, concept:'Trigonometric Ratios',subject:'Mathematics', engagement:68, lightbulb:false },
    { id:4, concept:'Genetics & Heredity', subject:'Biology',     engagement:88, lightbulb:true },
    { id:5, concept:'Linear Programming',  subject:'Mathematics', engagement:72, lightbulb:false },
  ],
};

const PARENT_DATA = {
  student:{ name:'Aroha', lastName:'Ngata', year:12 },
  attendance:94, riskScore:0.15,
  math:{ pct:68, concepts:14 }, bio:{ pct:74, concepts:11 }, overall:71,
  trend:'improving', engagement:0.78, sessions:23, lightbulbs:4, quizAvg:74,
  bestApproach:{ style:'Scaffolded Discovery', rate:0.86 },
  flags:[
    { concept:'Integration by Parts', subject:'Mathematics', detail:'Needs more practice with chain rule first' },
    { concept:'Probability Trees',    subject:'Mathematics', detail:'Diagram approach working better than equations' },
  ],
};

// Learning map nodes
const STUDENT_GRAPH = [
  { id:'a', label:'Number Theory',   x:120, y:380, mastery:80, depth:0 },
  { id:'b', label:'Basic Algebra',   x:260, y:380, mastery:75, depth:0 },
  { id:'c', label:'Geometry',        x:400, y:380, mastery:71, depth:0 },
  { id:'d', label:'Functions',       x:120, y:270, mastery:65, depth:1 },
  { id:'e', label:'Quadratic Eq.',   x:260, y:270, mastery:58, depth:1 },
  { id:'f', label:'Statistics',      x:400, y:270, mastery:62, depth:1 },
  { id:'g', label:'Trigonometry',    x:180, y:160, mastery:55, depth:2 },
  { id:'h', label:'Probability',     x:330, y:160, mastery:51, depth:2 },
  { id:'i', label:'Integration',     x:260, y:60,  mastery:42, depth:3 },
];
const STUDENT_EDGES = [
  ['a','d'],['b','d'],['b','e'],['c','f'],
  ['d','g'],['e','g'],['e','h'],['f','h'],
  ['g','i'],['h','i'],
];

// ── HELPERS ────────────────────────────────────────────────────────────────
function focusStyle(type) {
  if (type==='stuck_on_concept') return { border:'1px solid rgba(192,57,43,0.3)', background:'rgba(192,57,43,0.04)' };
  if (type==='low_engagement')   return { border:'1px solid rgba(217,119,6,0.3)', background:'rgba(217,119,6,0.04)' };
  return { border:'1px solid rgba(61,43,31,0.1)', background:'rgba(255,255,255,0.5)' };
}

function Sparkline({ data, color='#2D7D6F', w=280, h=80 }) {
  if (!data||data.length<2) return null;
  const max=Math.max(...data), min=Math.min(...data), range=max-min||1;
  const pts=data.map((v,i)=>[(i/(data.length-1))*w, h-((v-min)/range)*(h-16)-8]);
  const d=pts.map((p,i)=>`${i===0?'M':'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
  const fill=`${d} L${w},${h} L0,${h} Z`;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ width:'100%' }}>
      <defs><linearGradient id="spkGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity="0.2"/><stop offset="100%" stopColor={color} stopOpacity="0.02"/></linearGradient></defs>
      <path d={fill} fill="url(#spkGrad)"/>
      <path d={d} stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
      {pts.map((p,i)=><circle key={i} cx={p[0]} cy={p[1]} r="3" fill={color}/>)}
    </svg>
  );
}

// ── STUDENT DASHBOARD ──────────────────────────────────────────────────────
function StudentDashboard({ navigate, currentPage }) {
  const d=STUDENT_DATA;
  const [openSession,setOpenSession]=useState(null);
  const trendCol=d.trend==='improving'?'#059669':'#D97706';

  return (
    <DashboardShell subtitle={`Student · ${d.name}'s overview`} role="student" navigate={navigate} currentPage={currentPage}>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:22, alignItems:'start' }}>

        {/* PROGRESS */}
        <BlossomCard style={{ display:'flex', flexDirection:'column', gap:18 }}>
          <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between' }}>
            <SectionTitle>Your progress</SectionTitle>
            <div style={{ display:'flex', gap:6, flexWrap:'wrap', justifyContent:'flex-end' }}>
              {d.subjects.map(s=><span key={s.subject} style={{ padding:'3px 11px', borderRadius:20, border:'1px solid rgba(61,43,31,0.12)', background:'rgba(253,246,238,0.8)', fontSize:'0.7rem', color:'#6B4A3A', fontStyle:'italic' }}>{s.subject}</span>)}
            </div>
          </div>
          <p style={{ fontSize:'0.88rem', color:'#6B4A3A' }}>Kia ora, <strong style={{ color:'#3D2B1F' }}>{d.name}</strong> 🌸</p>

          {d.subjects.map(s=>{
            const col=masteryColor(s.pct);
            return (
              <div key={s.subject} style={{ display:'flex', flexDirection:'column', gap:7 }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                  <span style={{ fontSize:14, fontWeight:500, color:'#3D2B1F' }}>{s.subject}</span>
                  <span style={{ fontSize:18, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:col }}>{s.pct}%</span>
                </div>
                <div style={{ height:9, borderRadius:5, background:'rgba(61,43,31,0.08)', overflow:'hidden' }}>
                  <div style={{ width:`${s.pct}%`, height:'100%', borderRadius:5, background:col, transition:'width 0.8s cubic-bezier(0.16,1,0.3,1)' }}/>
                </div>
                <span style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>{s.concepts} concepts tracked</span>
              </div>
            );
          })}

          <div style={{ borderTop:'1px solid rgba(61,43,31,0.08)', paddingTop:14 }}>
            <div style={{ fontSize:11, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.1em', color:'#6B4A3A', marginBottom:10 }}>Weakest areas</div>
            {d.weakest.map(c=>{
              const col=masteryColor(c.pct);
              return (
                <div key={c.name} style={{ marginBottom:9 }}>
                  <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3 }}>
                    <span style={{ fontSize:13, color:'#3D2B1F' }}>{c.name}</span>
                    <span style={{ fontSize:12, fontWeight:500, color:'#6B4A3A' }}>{c.pct}%</span>
                  </div>
                  <div style={{ height:6, borderRadius:3, background:'rgba(61,43,31,0.08)', overflow:'hidden' }}>
                    <div style={{ width:`${c.pct}%`, height:'100%', borderRadius:3, background:col }}/>
                  </div>
                </div>
              );
            })}
          </div>
        </BlossomCard>

        {/* MOMENTUM */}
        <BlossomCard style={{ display:'flex', flexDirection:'column', gap:14 }}>
          <SectionTitle>Your momentum</SectionTitle>
          <div style={{ display:'flex', alignItems:'center', gap:8, color:trendCol }}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d={d.trend==='improving'?"M2 13 L6 8 L10 10 L16 4":"M2 4 L6 9 L10 7 L16 13"} stroke={trendCol} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span style={{ fontSize:14, fontWeight:500 }}>{d.trend==='improving'?'On a roll 🔥':'Needs focus'}</span>
          </div>
          <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
            <span style={{ padding:'4px 12px', borderRadius:20, border:'1px solid rgba(61,43,31,0.12)', background:'rgba(255,255,255,0.8)', fontSize:12, color:'#3D2B1F' }}>{d.aiChats} AI chats</span>
            <span style={{ padding:'4px 12px', borderRadius:20, border:'1px solid rgba(217,119,6,0.25)', background:'rgba(217,119,6,0.06)', fontSize:12, color:'#92400e' }}>{d.lightbulbs} lightbulb moments 💡</span>
          </div>
          <Sparkline data={d.engagementHistory} color={TEAL} h={88}/>
          <div style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic', textAlign:'center' }}>Engagement across last 10 sessions</div>
        </BlossomCard>

        {/* FOCUS AREAS */}
        <BlossomCard style={{ display:'flex', flexDirection:'column', gap:10 }}>
          <SectionTitle>Where to focus</SectionTitle>
          <p style={{ fontSize:12, color:'#6B4A3A', fontStyle:'italic', margin:'0 0 4px' }}>Areas needing attention from recent work.</p>
          {d.focusAreas.map((f,i)=>(
            <div key={i} style={{ ...focusStyle(f.type), borderRadius:10, padding:'10px 14px' }}>
              <div style={{ fontSize:13, fontWeight:500, color:'#3D2B1F' }}>{f.concept}</div>
              <div style={{ fontSize:11, color:'#6B4A3A', marginTop:2 }}>{f.subject} · {f.type.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</div>
            </div>
          ))}
          <button onClick={()=>navigate('ai-chat')} style={{ marginTop:6, padding:'11px', borderRadius:12, border:'1.5px solid #3D2B1F', background:'#3D2B1F', fontFamily:"'Lora',serif", fontSize:13, color:'#FDF6EE', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}>
            {NavIcons.chat} Chat with AI Tutor
          </button>
        </BlossomCard>

        {/* RECENT SESSIONS */}
        <BlossomCard style={{ display:'flex', flexDirection:'column', gap:10 }}>
          <SectionTitle>Recent AI sessions</SectionTitle>
          <p style={{ fontSize:12, color:'#6B4A3A', fontStyle:'italic', margin:'0 0 4px' }}>Tap a row to read the full conversation.</p>
          {d.sessions.map(s=>{
            const isOpen=openSession===s.id;
            return (
              <div key={s.id}>
                <button onClick={()=>setOpenSession(isOpen?null:s.id)} style={{ width:'100%', display:'flex', alignItems:'center', justifyContent:'space-between', gap:10, padding:'11px 14px', borderRadius:10, textAlign:'left', cursor:'pointer', border:'none', background:isOpen?TEAL_BG:'rgba(253,246,238,0.7)', outline:isOpen?`1.5px solid ${TEAL_BORDER}`:'none', transition:'all 0.15s' }}>
                  <div style={{ minWidth:0 }}>
                    <div style={{ fontSize:13, fontWeight:500, color:'#3D2B1F', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{s.concept}</div>
                    <div style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>{s.subject}</div>
                  </div>
                  <div style={{ display:'flex', alignItems:'center', gap:8, flexShrink:0 }}>
                    {s.lightbulb&&<span title="Lightbulb moment">💡</span>}
                    <span style={{ padding:'2px 10px', borderRadius:20, background:'rgba(61,43,31,0.07)', fontSize:11, fontWeight:500, color:'#3D2B1F' }}>{s.engagement}%</span>
                  </div>
                </button>
                {isOpen&&<div style={{ marginTop:4, padding:'13px 15px', borderRadius:10, border:'1px solid rgba(61,43,31,0.1)', background:'rgba(253,246,238,0.6)', fontSize:13, color:'#6B4A3A', fontStyle:'italic', lineHeight:1.7 }}>
                  Worked through {s.concept} problems. Engagement: {s.engagement}%. {s.lightbulb?'Lightbulb moment detected — great work! 🌸':'Keep practising to build confidence.'}
                </div>}
              </div>
            );
          })}
        </BlossomCard>

      </div>
    </DashboardShell>
  );
}

// ── STUDENT KNOWLEDGE MAP ──────────────────────────────────────────────────
function StudentGraphPage({ navigate, currentPage }) {
  const [selected,setSelected]=useState(null);
  const selNode=STUDENT_GRAPH.find(n=>n.id===selected);

  return (
    <DashboardShell subtitle="Learning Map · My Concepts" role="student" navigate={navigate} currentPage={currentPage}>
      <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
        <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', flexWrap:'wrap', gap:12 }}>
          <div>
            <SectionLabel>Aroha's journey</SectionLabel>
            <SectionTitle>Your Learning Map</SectionTitle>
            <p style={{ fontSize:13, color:'#6B4A3A', fontStyle:'italic', marginTop:6 }}>Tap a concept to see your mastery and what to work on next.</p>
          </div>
          <button onClick={()=>navigate('ai-chat')} style={{ display:'flex', alignItems:'center', gap:8, padding:'10px 20px', borderRadius:40, border:'none', background:'#3D2B1F', color:'#FDF6EE', fontFamily:"'Lora',serif", fontSize:13, cursor:'pointer' }}>
            {NavIcons.chat} Ask AI Tutor
          </button>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1fr 260px', gap:20, alignItems:'start' }}>
          <BlossomCard style={{ padding:16 }}>
            <svg viewBox="0 0 520 440" style={{ width:'100%' }}>
              {['Foundational','Core','Advanced','Extension'].map((d,di)=>(
                <text key={d} x="8" y={[400,290,180,78][di]} fontSize="9" fill="rgba(107,74,58,0.45)" fontStyle="italic" fontFamily="Georgia,serif">{d}</text>
              ))}
              {[390,280,170,65].map(y=>(
                <line key={y} x1="70" y1={y} x2="490" y2={y} stroke="rgba(61,43,31,0.05)" strokeWidth="1" strokeDasharray="4 4"/>
              ))}
              {STUDENT_EDGES.map(([a,b])=>{
                const na=STUDENT_GRAPH.find(n=>n.id===a), nb=STUDENT_GRAPH.find(n=>n.id===b);
                return <line key={`${a}-${b}`} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke="rgba(61,43,31,0.12)" strokeWidth="1.5"/>;
              })}
              {STUDENT_GRAPH.map(node=>{
                const col=masteryColor(node.mastery);
                const isSel=selected===node.id;
                return (
                  <g key={node.id} onClick={()=>setSelected(isSel?null:node.id)} style={{ cursor:'pointer' }}>
                    <circle cx={node.x} cy={node.y} r={isSel?30:24} fill={`${col}15`} stroke={col} strokeWidth={isSel?3:2}/>
                    <text x={node.x} y={node.y+1} textAnchor="middle" dominantBaseline="middle" fontSize="11" fontWeight="700" fill={col} fontFamily="Georgia,serif">{node.mastery}%</text>
                    <text x={node.x} y={node.y+32} textAnchor="middle" fontSize="9" fill="#6B4A3A" fontFamily="Georgia,serif">{node.label}</text>
                  </g>
                );
              })}
            </svg>
          </BlossomCard>

          <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
            {selNode?(
              <BlossomCard>
                <SectionLabel>Concept Detail</SectionLabel>
                <SectionTitle style={{ marginBottom:12 }}>{selNode.label}</SectionTitle>
                <div style={{ display:'flex', justifyContent:'center', marginBottom:14 }}>
                  <MasteryRing value={selNode.mastery} size={76} strokeWidth={8} label="Your mastery"/>
                </div>
                <div style={{ padding:'10px 12px', borderRadius:10, background:TEAL_BG, border:`1px solid ${TEAL_BORDER}`, marginBottom:12 }}>
                  <p style={{ fontSize:12, color:'#6B4A3A', lineHeight:1.65, margin:0 }}>
                    {selNode.mastery>=70?`Great work on ${selNode.label}! Try the advanced exercises to push further.`:selNode.mastery>=50?`You're developing ${selNode.label}. A few more practice sessions will get you there!`:`${selNode.label} needs more focus. Your AI Tutor can help you build confidence here.`}
                  </p>
                </div>
                <button onClick={()=>navigate('ai-chat')} style={{ width:'100%', padding:'9px', borderRadius:10, border:'none', background:'#3D2B1F', fontFamily:"'Lora',serif", fontSize:12, color:'#FDF6EE', cursor:'pointer' }}>
                  Practice with AI Tutor
                </button>
                <button onClick={()=>setSelected(null)} style={{ width:'100%', padding:'8px', borderRadius:10, border:'1px solid rgba(61,43,31,0.15)', background:'transparent', fontFamily:"'Lora',serif", fontSize:12, color:'#6B4A3A', cursor:'pointer', marginTop:8 }}>Clear</button>
              </BlossomCard>
            ):(
              <BlossomCard style={{ textAlign:'center', padding:28 }}>
                <BlossomTree style={{ width:80, height:100, opacity:0.2, margin:'0 auto 12px' }}/>
                <p style={{ fontSize:13, color:'#6B4A3A', fontStyle:'italic', lineHeight:1.7 }}>Tap any concept to see your progress and next steps</p>
              </BlossomCard>
            )}

            {/* My stats */}
            <BlossomCard style={{ padding:'16px 18px' }}>
              <div style={{ fontSize:11, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.1em', color:'#6B4A3A', marginBottom:12 }}>My Stats</div>
              {[
                { label:'Concepts mastered', val:STUDENT_GRAPH.filter(n=>n.mastery>=70).length, col:'#059669' },
                { label:'In progress',       val:STUDENT_GRAPH.filter(n=>n.mastery>=50&&n.mastery<70).length, col:'#D97706' },
                { label:'Need focus',        val:STUDENT_GRAPH.filter(n=>n.mastery<50).length, col:'#C0392B' },
              ].map(row=>(
                <div key={row.label} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8 }}>
                  <span style={{ fontSize:12, color:'#6B4A3A' }}>{row.label}</span>
                  <span style={{ fontSize:16, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:row.col }}>{row.val}</span>
                </div>
              ))}
            </BlossomCard>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}

// ── PARENT DASHBOARD ───────────────────────────────────────────────────────
function ParentDashboard({ navigate, currentPage }) {
  const d=PARENT_DATA;
  const riskCol=d.riskScore<0.2?'#059669':d.riskScore<0.4?'#D97706':'#C0392B';

  return (
    <DashboardShell subtitle={`Parent · ${d.student.name}'s overview`} role="parent" navigate={navigate} currentPage={currentPage}>
      <div style={{ maxWidth:760, margin:'0 auto', display:'flex', flexDirection:'column', gap:18 }}>

        <BlossomCard>
          <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:16, marginBottom:16 }}>
            <div>
              <SectionLabel>You're viewing</SectionLabel>
              <SectionTitle>{d.student.name} {d.student.lastName}</SectionTitle>
              <div style={{ fontSize:12, color:'#6B4A3A', fontStyle:'italic', marginTop:4 }}>Year {d.student.year}</div>
            </div>
            <div style={{ textAlign:'right', flexShrink:0 }}>
              <div style={{ fontSize:11, color:'#6B4A3A', marginBottom:4 }}>Attendance</div>
              <div style={{ fontSize:28, fontFamily:"'Shippori Mincho',serif", fontWeight:800, color:d.attendance>=90?'#059669':d.attendance>=80?'#D97706':'#C0392B' }}>{d.attendance}%</div>
            </div>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:12, padding:'12px 16px', borderRadius:12, background:`${riskCol}0D`, border:`1px solid ${riskCol}33` }}>
            <span style={{ fontSize:20 }}>{d.riskScore<0.2?'✓':'⚠'}</span>
            <span style={{ fontWeight:500, color:riskCol, fontSize:14 }}>{d.riskScore<0.2?'Your child is on track':d.riskScore<0.4?'Some areas need attention':'Additional support recommended'}</span>
          </div>
        </BlossomCard>

        <BlossomCard>
          <SectionTitle style={{ marginBottom:8 }}>Overall progress</SectionTitle>
          <p style={{ fontSize:13, color:'#6B4A3A', fontStyle:'italic', marginBottom:16 }}>{d.trend==='improving'?`${d.student.name} is improving across their subjects 📈`:`${d.student.name} is maintaining steady progress`}</p>
          <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:18 }}>
            <span style={{ fontSize:12, color:'#6B4A3A', width:60 }}>Overall</span>
            <div style={{ flex:1, height:10, borderRadius:5, background:'rgba(61,43,31,0.08)', overflow:'hidden' }}>
              <div style={{ width:`${d.overall}%`, height:'100%', borderRadius:5, background:TEAL }}/>
            </div>
            <span style={{ fontSize:16, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:TEAL, width:44 }}>{d.overall}%</span>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
            {[['Mathematics','#5B9BD5',d.math],['Biology','#059669',d.bio]].map(([name,col,info])=>(
              <div key={name} style={{ padding:14, borderRadius:14, background:'rgba(253,246,238,0.7)', border:'1px solid rgba(61,43,31,0.08)' }}>
                <div style={{ fontSize:10, textTransform:'uppercase', letterSpacing:'0.14em', color:'#6B4A3A', marginBottom:7 }}>{name}</div>
                <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:5 }}>
                  <div style={{ flex:1, height:7, borderRadius:4, background:'rgba(61,43,31,0.08)', overflow:'hidden' }}>
                    <div style={{ width:`${info.pct}%`, height:'100%', borderRadius:4, background:col }}/>
                  </div>
                  <span style={{ fontSize:14, fontWeight:600, color:'#3D2B1F', width:34 }}>{info.pct}%</span>
                </div>
                <div style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>{info.concepts} concepts assessed</div>
              </div>
            ))}
          </div>
        </BlossomCard>

        <BlossomCard>
          <SectionTitle style={{ marginBottom:8 }}>Engagement at a glance</SectionTitle>
          <p style={{ fontSize:13, color:'#6B4A3A', fontStyle:'italic', marginBottom:14 }}>{d.engagement>=0.7?`${d.student.name} is highly engaged with their learning`:`${d.student.name} is moderately engaged`}</p>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12, textAlign:'center' }}>
            {[{val:d.sessions,label:'Learning sessions',col:TEAL},{val:`${d.lightbulbs} 💡`,label:'Lightbulb moments',col:'#D97706'},{val:`${d.quizAvg}%`,label:'Quiz average',col:'#059669'}].map(({val,label,col})=>(
              <div key={label} style={{ padding:14, borderRadius:12, background:'rgba(253,246,238,0.6)', border:'1px solid rgba(61,43,31,0.08)' }}>
                <div style={{ fontSize:22, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:col, marginBottom:4 }}>{val}</div>
                <div style={{ fontSize:11, color:'#6B4A3A' }}>{label}</div>
              </div>
            ))}
          </div>
        </BlossomCard>

        <BlossomCard>
          <SectionTitle style={{ marginBottom:8 }}>How they learn best</SectionTitle>
          <p style={{ fontSize:13, color:'#6B4A3A', lineHeight:1.7 }}>
            {d.student.name} responds well to <strong style={{ color:'#3D2B1F' }}>{d.bestApproach.style}</strong> with a{' '}
            <strong style={{ color:TEAL }}>{Math.round(d.bestApproach.rate*100)}% success rate</strong>. Try this approach when helping at home.
          </p>
        </BlossomCard>

        {d.flags.length>0&&(
          <BlossomCard>
            <SectionTitle style={{ marginBottom:8 }}>Ideas to support at home</SectionTitle>
            <p style={{ fontSize:12, color:'#6B4A3A', fontStyle:'italic', marginBottom:12 }}>A few concepts {d.student.name} is finding harder right now.</p>
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {d.flags.map((f,i)=>(
                <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:12, padding:'10px 14px', borderRadius:10, background:'rgba(217,119,6,0.05)', border:'1px solid rgba(217,119,6,0.18)' }}>
                  <div style={{ width:6, height:6, borderRadius:'50%', background:'#D97706', marginTop:6, flexShrink:0 }}/>
                  <div>
                    <div style={{ fontSize:13, fontWeight:500, color:'#3D2B1F' }}>{f.concept}</div>
                    <div style={{ fontSize:11, color:'#6B4A3A', marginTop:2 }}>{f.subject} · {f.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </BlossomCard>
        )}

      </div>
    </DashboardShell>
  );
}

// ── AI CHAT ────────────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `You are an AI Tutor for AxonAI, helping Aroha Ngata (a Year 12 student) with Mathematics and Biology. You are warm, encouraging, and pedagogically sound. Use the Socratic method — ask guiding questions rather than giving direct answers. Keep responses concise (2-4 sentences unless explaining a concept). Address Aroha by name occasionally.`;

function AIChatPage({ navigate, currentPage }) {
  const [messages,setMessages]=useState([
    { role:'ai', text:"Kia ora Aroha! 🌸 I'm your AI Tutor — here to help with Mathematics and Biology. What would you like to work on today?" },
  ]);
  const [input,setInput]=useState('');
  const [loading,setLoading]=useState(false);
  const bottomRef=useRef(null);

  useEffect(()=>{ if(bottomRef.current) bottomRef.current.scrollTop=bottomRef.current.scrollHeight; },[messages]);

  const sendMessage=async(text)=>{
    const msg=text||input.trim();
    if(!msg||loading) return;
    setInput('');
    setMessages(prev=>[...prev,{role:'user',text:msg}]);
    setLoading(true);
    try {
      const history=messages.map(m=>({ role:m.role==='ai'?'assistant':'user', content:m.text }));
      const reply=await window.claude.complete({ messages:[...history,{role:'user',content:msg}], system:SYSTEM_PROMPT });
      setMessages(prev=>[...prev,{role:'ai',text:reply}]);
    } catch {
      setMessages(prev=>[...prev,{role:'ai',text:"Sorry, I couldn't connect right now. Please try again in a moment."}]);
    }
    setLoading(false);
  };

  const quick=["Explain this concept to me","Give me a practice problem","Help me understand my mistake","What should I focus on?"];

  return (
    <div style={{ height:'100vh', display:'flex', flexDirection:'column', background:'#FDF6EE', fontFamily:"'Lora',serif", position:'relative' }}>
      <BlossomTree style={{ position:'fixed', right:-60, top:-40, width:400, height:540, opacity:0.1, pointerEvents:'none', zIndex:0 }}/>
      <PetalLayer count={25}/>

      {/* Header */}
      <div style={{ display:'flex', alignItems:'center', gap:14, padding:'13px 22px', background:'rgba(253,246,238,0.95)', backdropFilter:'blur(14px)', borderBottom:'2px solid #3D2B1F', flexShrink:0, zIndex:200, position:'relative' }}>
        <button onClick={()=>navigate('student-dashboard')} style={{ width:36, height:36, borderRadius:10, border:'1.5px solid rgba(61,43,31,0.18)', background:'white', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center' }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8l4 4" stroke="#3D2B1F" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
        <div style={{ width:36, height:36, borderRadius:12, background:TEAL_BG, border:`1.5px solid ${TEAL_BORDER}`, display:'flex', alignItems:'center', justifyContent:'center' }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 1a8 8 0 100 16A8 8 0 009 1z" stroke={TEAL} strokeWidth="1.4" fill="none"/><circle cx="9" cy="9" r="2" fill={TEAL}/><path d="M9 5v2M9 11v2M5 9H3M15 9h-2" stroke={TEAL} strokeWidth="1.1" strokeLinecap="round"/></svg>
        </div>
        <div>
          <div style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:600, fontSize:15, color:'#3D2B1F' }}>AI Tutor</div>
          <div style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>Year 12 · Mathematics & Biology</div>
        </div>
        <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6 }}>
          <div style={{ width:7, height:7, borderRadius:'50%', background:'#059669', boxShadow:'0 0 7px rgba(5,150,105,0.5)' }}/>
          <span style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>Online</span>
        </div>
      </div>

      {/* Messages */}
      <div ref={bottomRef} style={{ flex:1, overflowY:'auto', padding:'18px 18px 0', display:'flex', flexDirection:'column', gap:14, position:'relative', zIndex:5 }}>
        {messages.map((m,i)=>(
          <div key={i} style={{ display:'flex', gap:10, alignItems:'flex-start', flexDirection:m.role==='user'?'row-reverse':'row' }}>
            <div style={{ width:32, height:32, borderRadius:'50%', background:m.role==='ai'?TEAL_BG:'rgba(61,43,31,0.1)', border:`1.5px solid ${m.role==='ai'?TEAL_BORDER:'rgba(61,43,31,0.18)'}`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, fontSize:12, fontFamily:"'Shippori Mincho',serif", fontWeight:700, color:m.role==='ai'?TEAL:'#3D2B1F' }}>
              {m.role==='ai'?'✦':'AN'}
            </div>
            <div style={{ maxWidth:'72%', padding:'12px 15px', borderRadius:m.role==='ai'?'4px 18px 18px 18px':'18px 4px 18px 18px', background:m.role==='ai'?'white':'#3D2B1F', border:m.role==='ai'?'1px solid rgba(61,43,31,0.1)':'none', color:m.role==='ai'?'#3D2B1F':'#FDF6EE', fontSize:14, lineHeight:1.7, boxShadow:'0 2px 10px rgba(61,43,31,0.05)' }}>
              {m.text}
            </div>
          </div>
        ))}
        {loading&&(
          <div style={{ display:'flex', gap:10, alignItems:'flex-start' }}>
            <div style={{ width:32, height:32, borderRadius:'50%', background:TEAL_BG, border:`1.5px solid ${TEAL_BORDER}`, display:'flex', alignItems:'center', justifyContent:'center', color:TEAL, fontSize:12, fontFamily:"'Shippori Mincho',serif", fontWeight:700 }}>✦</div>
            <div style={{ padding:'13px 16px', borderRadius:'4px 18px 18px 18px', background:'white', border:'1px solid rgba(61,43,31,0.1)' }}>
              <div style={{ display:'flex', gap:5, alignItems:'center' }}>
                {[0,1,2].map(i=><div key={i} style={{ width:7, height:7, borderRadius:'50%', background:TEAL, opacity:0.5, animation:`typing 1.2s ${i*0.2}s ease-in-out infinite` }}/>)}
              </div>
            </div>
          </div>
        )}
        <div style={{ height:16 }}/>
      </div>

      {/* Quick actions */}
      <div style={{ padding:'10px 18px 0', display:'flex', gap:7, overflowX:'auto', flexShrink:0, position:'relative', zIndex:5 }}>
        {quick.map(q=>(
          <button key={q} onClick={()=>sendMessage(q)} style={{ padding:'7px 13px', borderRadius:20, border:`1px solid ${TEAL_BORDER}`, background:'white', fontFamily:"'Lora',serif", fontSize:12, color:'#6B4A3A', cursor:'pointer', whiteSpace:'nowrap', flexShrink:0, transition:'all 0.15s' }}
            onMouseEnter={e=>{e.target.style.borderColor=TEAL;e.target.style.color=TEAL;}}
            onMouseLeave={e=>{e.target.style.borderColor=TEAL_BORDER;e.target.style.color='#6B4A3A';}}
          >{q}</button>
        ))}
      </div>

      {/* Input */}
      <div style={{ padding:'10px 18px 18px', flexShrink:0, background:'rgba(253,246,238,0.96)', backdropFilter:'blur(8px)', position:'relative', zIndex:5 }}>
        <div style={{ display:'flex', gap:8, alignItems:'flex-end', background:'white', border:`1.5px solid rgba(61,43,31,0.15)`, borderRadius:20, padding:'7px 7px 7px 15px', boxShadow:'0 2px 14px rgba(61,43,31,0.06)' }}>
          <textarea value={input} onChange={e=>{setInput(e.target.value);e.target.style.height='auto';e.target.style.height=Math.min(e.target.scrollHeight,120)+'px';}} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}}} placeholder="Ask me anything…" rows={1} style={{ flex:1, border:'none', outline:'none', fontFamily:"'Lora',serif", fontSize:14, color:'#3D2B1F', background:'transparent', resize:'none', lineHeight:1.6, paddingTop:5 }}/>
          <button onClick={()=>sendMessage()} disabled={loading||!input.trim()} style={{ width:38, height:38, borderRadius:11, border:'none', background:loading||!input.trim()?'rgba(61,43,31,0.08)':'#3D2B1F', cursor:loading||!input.trim()?'not-allowed':'pointer', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, transition:'background 0.2s' }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8l12-6-6 12V8H2z" fill={loading||!input.trim()?'#6B4A3A':'#FDF6EE'}/></svg>
          </button>
        </div>
      </div>

      <style>{`@keyframes typing{0%,80%,100%{opacity:0.3;transform:scale(1)}40%{opacity:1;transform:scale(1.2)}}`}</style>
    </div>
  );
}

Object.assign(window, { StudentDashboard, StudentGraphPage, ParentDashboard, AIChatPage });
