
const { useState, useEffect, useRef } = React;

// ── PETAL LAYER — z-index 1, always behind UI content ─────────────────────
const PETAL_COLORS = ['#F8D0D5','#F0B8C0','#FDE8EB','#E89AA8','#FDD5DA','#FCEAED'];

function makePetalSVG(color, size) {
  const s = `<svg xmlns='http://www.w3.org/2000/svg' width='${size}' height='${size}' viewBox='-18 -18 36 36'>
    <ellipse cx='0' cy='-9' rx='4.5' ry='8' fill='${color}' transform='rotate(0)' opacity='0.9'/>
    <ellipse cx='0' cy='-9' rx='4.5' ry='8' fill='${color}' transform='rotate(72)' opacity='0.9'/>
    <ellipse cx='0' cy='-9' rx='4.5' ry='8' fill='${color}' transform='rotate(144)' opacity='0.9'/>
    <ellipse cx='0' cy='-9' rx='4.5' ry='8' fill='${color}' transform='rotate(216)' opacity='0.9'/>
    <ellipse cx='0' cy='-9' rx='4.5' ry='8' fill='${color}' transform='rotate(288)' opacity='0.9'/>
    <circle cx='0' cy='0' r='2.8' fill='#FFF8F0' opacity='0.75'/>
  </svg>`;
  return 'data:image/svg+xml;utf8,' + encodeURIComponent(s);
}

function PetalLayer({ count = 38 }) {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const petals = [];
    const styleEl = document.createElement('style');
    for (let i = 0; i < count; i++) {
      const color  = PETAL_COLORS[Math.floor(Math.random() * PETAL_COLORS.length)];
      const size   = 12 + Math.random() * 15;
      const left   = Math.random() * 110 - 5;
      const dur    = 9 + Math.random() * 13;
      const delay  = Math.random() * 22;
      const drift  = (Math.random() - 0.5) * 120;
      const sway   = (Math.random() - 0.5) * 35;
      const rotEnd = 300 + Math.random() * 400;

      styleEl.textContent += `
        @keyframes pf${i} {
          0%   { transform:translateY(0) translateX(0) rotate(0deg); opacity:0; }
          7%   { opacity:${0.45 + Math.random() * 0.4}; }
          50%  { transform:translateY(46vh) translateX(${sway}px) rotate(${rotEnd*0.5}deg); }
          93%  { opacity:${0.3 + Math.random() * 0.35}; }
          100% { transform:translateY(108vh) translateX(${drift}px) rotate(${rotEnd}deg); opacity:0; }
        }`;

      const img = document.createElement('img');
      img.src   = makePetalSVG(color, size);
      img.style.cssText = `
        position:absolute; top:-${size+10}px; left:${left}%;
        width:${size}px; height:${size}px; pointer-events:none;
        animation:pf${i} ${dur}s ${delay}s linear infinite; opacity:0;`;
      canvas.appendChild(img);
      petals.push(img);
    }
    document.head.appendChild(styleEl);
    return () => { document.head.removeChild(styleEl); petals.forEach(p => p.remove()); };
  }, [count]);

  return (
    <div ref={canvasRef} style={{
      position:'fixed', inset:0, pointerEvents:'none',
      /* z-index 1 — above background, BELOW all page content (which is z-index 5+) */
      zIndex:1, overflow:'hidden',
    }}/>
  );
}

// ── REDESIGNED BLOSSOM TREE ────────────────────────────────────────────────
// Anime/Ghibli cherry blossom — organic trunk, wide canopy,
// dense layered flower clouds. Pink ONLY on blossoms.
function BlossomTree({ style = {} }) {
  const bark  = '#2E1A0E';
  const bark2 = '#3D2410';
  // Blossom palette: warm pinks for depth
  const p0 = '#FEEEF2'; // palest — outer glow
  const p1 = '#FAD8E0'; // soft base
  const p2 = '#F5C0CE'; // mid
  const p3 = '#EFA8BC'; // deeper
  const p4 = '#E88FA8'; // richest — inner shadows

  // Flower cloud: multiple overlapping ellipses + individual flowers
  const cloud = (cx, cy, r, key, angle = 0) => {
    const cos = Math.cos(angle * Math.PI / 180);
    const sin = Math.sin(angle * Math.PI / 180);
    const offsets = [
      [0, 0, r * 1.35, r * 1.0, p0, 0.55],
      [-r*0.42, r*0.08, r*1.1, r*0.85, p1, 0.65],
      [r*0.48, -r*0.06, r*1.0, r*0.78, p1, 0.62],
      [r*0.08, -r*0.38, r*0.88, r*0.7, p2, 0.68],
      [-r*0.18, r*0.44, r*0.82, r*0.65, p2, 0.62],
      [r*0.38, r*0.36, r*0.75, r*0.6, p3, 0.6],
      [-r*0.44, -r*0.28, r*0.7, r*0.55, p3, 0.58],
      [r*0.1, r*0.12, r*0.5, r*0.4, p4, 0.5],
    ];

    // Individual 5-petal cherry flowers
    const flowers = [
      [0, -r*0.05], [r*0.3, r*0.22], [-r*0.3, r*0.18],
      [r*0.18, -r*0.28], [-r*0.22, -r*0.25], [r*0.42, -r*0.05],
      [-r*0.38, r*0.05],
    ];

    return (
      <g key={key}>
        {offsets.map(([dx, dy, rx, ry, fill, op], i) => (
          <ellipse key={i}
            cx={cx + dx} cy={cy + dy} rx={rx} ry={ry}
            fill={fill} opacity={op}
            transform={`rotate(${angle},${cx},${cy})`}
          />
        ))}
        {/* Soft highlight */}
        <ellipse cx={cx - r*0.1} cy={cy - r*0.22} rx={r*0.42} ry={r*0.3}
          fill="white" opacity="0.18"
          transform={`rotate(${angle},${cx},${cy})`}
        />
        {/* Cherry blossoms */}
        {flowers.map(([fx, fy], fi) => {
          const fr = r * 0.14;
          return (
            <g key={fi} transform={`translate(${cx + fx},${cy + fy})`}>
              {[0,72,144,216,288].map(rot => (
                <ellipse key={rot} cx="0" cy={-fr * 1.6}
                  rx={fr * 0.75} ry={fr * 1.4}
                  fill={fi % 3 === 0 ? p3 : fi % 3 === 1 ? p2 : p4}
                  transform={`rotate(${rot})`} opacity="0.95"/>
              ))}
              <circle cx="0" cy="0" r={fr * 0.6} fill="#FFF5E0" opacity="0.9"/>
              {/* Stamen dots */}
              {[0,60,120,180,240,300].map(a => (
                <circle key={a}
                  cx={Math.cos(a*Math.PI/180)*fr*0.9}
                  cy={Math.sin(a*Math.PI/180)*fr*0.9}
                  r={fr*0.18} fill="#F5C060" opacity="0.8"/>
              ))}
            </g>
          );
        })}
      </g>
    );
  };

  return (
    <svg viewBox="0 0 500 700" fill="none" style={style}>
      <defs>
        <linearGradient id="trunkGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={bark}/>
          <stop offset="40%" stopColor={bark2}/>
          <stop offset="100%" stopColor={bark}/>
        </linearGradient>
      </defs>

      {/* === TRUNK === */}
      <path d="M252 698 C248 658 242 608 236 566 C230 524 224 490 226 456 C228 424 234 398 238 368 C242 340 244 316 242 292"
        stroke="url(#trunkGrad)" strokeWidth="30" strokeLinecap="round" fill="none"/>
      {/* Bark texture highlights */}
      <path d="M246 680 C243 648 240 608 238 572" stroke="rgba(255,255,255,0.07)" strokeWidth="9" strokeLinecap="round" fill="none"/>
      <path d="M256 640 C254 615 252 585 250 558" stroke="rgba(0,0,0,0.1)" strokeWidth="6" strokeLinecap="round" fill="none"/>

      {/* Root flares */}
      <path d="M252 698 C268 684 294 672 318 664" stroke={bark} strokeWidth="13" strokeLinecap="round" fill="none"/>
      <path d="M252 698 C234 682 208 670 184 663" stroke={bark} strokeWidth="12" strokeLinecap="round" fill="none"/>
      <path d="M248 710 C256 700 270 694 284 690" stroke={bark} strokeWidth="8" strokeLinecap="round" fill="none"/>
      <path d="M248 710 C240 698 226 692 212 688" stroke={bark} strokeWidth="7" strokeLinecap="round" fill="none"/>

      {/* === MAIN LEFT BRANCH === */}
      <path d="M236 308 C218 280 194 250 164 222 C138 198 106 176 74 160"
        stroke={bark} strokeWidth="16" strokeLinecap="round" fill="none"/>
      {/* Left sub-far */}
      <path d="M74 160 C52 142 32 120 14 96 C2 80 -4 64 -4 50"
        stroke={bark} strokeWidth="10" strokeLinecap="round" fill="none"/>
      {/* Left sub-up */}
      <path d="M110 196 C96 170 84 140 76 110 C68 84 66 60 68 38"
        stroke={bark} strokeWidth="9" strokeLinecap="round" fill="none"/>
      {/* Left drooping arm */}
      <path d="M74 160 C80 178 82 198 78 218 C74 235 66 250 56 262"
        stroke={bark} strokeWidth="7" strokeLinecap="round" fill="none"/>
      {/* Left mid-arm */}
      <path d="M140 230 C124 218 108 202 94 184 C82 168 72 152 64 136"
        stroke={bark} strokeWidth="8" strokeLinecap="round" fill="none"/>

      {/* === MAIN RIGHT BRANCH === */}
      <path d="M242 300 C260 270 284 240 312 214 C336 192 368 170 402 154"
        stroke={bark} strokeWidth="16" strokeLinecap="round" fill="none"/>
      {/* Right sub-far */}
      <path d="M402 154 C424 136 446 114 464 90 C478 72 486 56 488 42"
        stroke={bark} strokeWidth="10" strokeLinecap="round" fill="none"/>
      {/* Right sub-up */}
      <path d="M366 182 C380 156 390 126 396 96 C400 70 400 48 396 28"
        stroke={bark} strokeWidth="9" strokeLinecap="round" fill="none"/>
      {/* Right drooping arm */}
      <path d="M402 154 C410 172 414 192 410 212 C406 230 396 246 382 258"
        stroke={bark} strokeWidth="7" strokeLinecap="round" fill="none"/>
      {/* Right mid-arm */}
      <path d="M352 196 C370 182 388 164 402 144 C414 126 422 108 426 90"
        stroke={bark} strokeWidth="8" strokeLinecap="round" fill="none"/>

      {/* === CENTER UPPER BRANCH === */}
      <path d="M240 278 C236 246 230 212 224 178 C218 148 212 120 208 94"
        stroke={bark} strokeWidth="13" strokeLinecap="round" fill="none"/>
      {/* Center-left arm */}
      <path d="M222 186 C206 164 186 144 164 128 C144 114 124 104 106 98"
        stroke={bark} strokeWidth="8" strokeLinecap="round" fill="none"/>
      {/* Center-right arm */}
      <path d="M220 204 C238 182 260 162 282 146 C300 132 318 122 334 116"
        stroke={bark} strokeWidth="8" strokeLinecap="round" fill="none"/>
      {/* Top twigs */}
      <path d="M208 94 C200 72 192 50 186 30" stroke={bark} strokeWidth="6" strokeLinecap="round" fill="none"/>
      <path d="M208 94 C216 72 224 52 230 32" stroke={bark} strokeWidth="5.5" strokeLinecap="round" fill="none"/>
      <path d="M208 94 C222 78 234 60 244 42" stroke={bark} strokeWidth="5" strokeLinecap="round" fill="none"/>

      {/* === MID-TRUNK SIDE BRANCHES === */}
      <path d="M228 400 C210 378 188 358 164 342 C142 328 122 320 104 316"
        stroke={bark} strokeWidth="10" strokeLinecap="round" fill="none"/>
      <path d="M232 388 C252 368 274 350 296 336 C315 324 332 316 348 312"
        stroke={bark} strokeWidth="9" strokeLinecap="round" fill="none"/>

      {/* Extra small twigs */}
      <path d="M106 98 C90 84 76 68 64 52" stroke={bark} strokeWidth="5.5" strokeLinecap="round" fill="none"/>
      <path d="M334 116 C350 100 364 82 374 64" stroke={bark} strokeWidth="5.5" strokeLinecap="round" fill="none"/>
      <path d="M56 262 C48 278 38 292 26 302" stroke={bark} strokeWidth="5" strokeLinecap="round" fill="none"/>
      <path d="M382 258 C394 272 404 288 412 302" stroke={bark} strokeWidth="5" strokeLinecap="round" fill="none"/>

      {/* ====== BLOSSOM CLOUDS ====== */}
      {/* Left major tip */}
      {cloud(62, 144, 54, 'L1')}
      {/* Left far sub */}
      {cloud(-2, 42, 46, 'L2')}
      {/* Left sub-up */}
      {cloud(68, 28, 48, 'L3')}
      {/* Left mid-arm */}
      {cloud(60, 124, 36, 'L4')}
      {/* Left drooping tip */}
      {cloud(52, 256, 38, 'L5')}
      {/* Left sub-far branch */}
      {cloud(94, 178, 34, 'L6')}

      {/* Right major tip */}
      {cloud(412, 142, 56, 'R1')}
      {/* Right far sub */}
      {cloud(490, 34, 48, 'R2')}
      {/* Right sub-up */}
      {cloud(394, 18, 50, 'R3')}
      {/* Right mid-arm */}
      {cloud(428, 80, 38, 'R4')}
      {/* Right drooping tip */}
      {cloud(380, 252, 38, 'R5')}
      {/* Right sub-far */}
      {cloud(346, 198, 34, 'R6')}

      {/* Center top */}
      {cloud(204, 76, 50, 'C1')}
      {cloud(184, 22, 42, 'C2')}
      {cloud(232, 24, 40, 'C3')}
      {cloud(246, 36, 32, 'C4')}

      {/* Center arms */}
      {cloud(100, 90, 42, 'CA1')}
      {cloud(60, 44, 36, 'CA2')}
      {cloud(336, 108, 42, 'CA3')}
      {cloud(376, 56, 38, 'CA4')}

      {/* Mid-trunk tips */}
      {cloud(98, 308, 40, 'M1')}
      {cloud(350, 304, 40, 'M2')}

      {/* Scattered mid-branch */}
      {cloud(152, 218, 32, 'S1')}
      {cloud(316, 208, 32, 'S2')}
      {cloud(202, 170, 28, 'S3')}
      {cloud(172, 124, 28, 'S4')}
      {cloud(270, 142, 28, 'S5')}
      {cloud(128, 100, 26, 'S6')}
      {cloud(360, 182, 28, 'S7')}
    </svg>
  );
}

// ── NAV ICONS ─────────────────────────────────────────────────────────────
const NavIcons = {
  dashboard: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="1" y="1" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5"/><rect x="9" y="1" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5"/><rect x="1" y="9" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5"/><rect x="9" y="9" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5"/></svg>,
  students:  <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="6" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.5"/><path d="M1 13c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/><circle cx="12" cy="5" r="2" stroke="currentColor" strokeWidth="1.5"/><path d="M12 10c1.8.3 3 1.8 3 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  book:      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 2h8a2 2 0 012 2v9a2 2 0 01-2 2H3V2z" stroke="currentColor" strokeWidth="1.5"/><path d="M7 2v13M3 6h3M3 9h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  graph:     <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.5"/><circle cx="2" cy="4" r="1.5" stroke="currentColor" strokeWidth="1.3"/><circle cx="14" cy="4" r="1.5" stroke="currentColor" strokeWidth="1.3"/><circle cx="2" cy="12" r="1.5" stroke="currentColor" strokeWidth="1.3"/><circle cx="14" cy="12" r="1.5" stroke="currentColor" strokeWidth="1.3"/><path d="M3.5 4.5L6 7M10 7l2.5-2.5M3.5 11.5L6 9M10 9l2.5 2.5" stroke="currentColor" strokeWidth="1.2"/></svg>,
  settings:  <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.5"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  chat:      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 3a1 1 0 011-1h10a1 1 0 011 1v8a1 1 0 01-1 1H5l-3 2V3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg>,
  map:       <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 2l4 2 4-2v11l-4 2-4-2-4 2V3l4-1z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/><path d="M6 2v11M10 4v11" stroke="currentColor" strokeWidth="1.4"/></svg>,
  alert:     <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2L1 13h14L8 2z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/><path d="M8 7v3M8 11.5v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  logout:    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M5 7h7M9 5l2 2-2 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M7 2H3a1 1 0 00-1 1v8a1 1 0 001 1h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  upload:    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 10V3M5 6l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M3 11v2h10v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  plus:      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>,
  check:     <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8l3.5 3.5L13 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>,
};

const NAV_ITEMS = {
  teacher: [
    { icon:'dashboard', label:'Dashboard',       page:'teacher-dashboard' },
    { icon:'students',  label:'Students',        page:'teacher-students' },
    { icon:'book',      label:'Subjects',        page:'teacher-subjects' },
    { icon:'graph',     label:'Knowledge Graph', page:'teacher-graph' },
    { icon:'settings',  label:'Settings',        page:'teacher-settings' },
  ],
  student: [
    { icon:'dashboard', label:'Overview',     page:'student-dashboard' },
    { icon:'map',       label:'Learning Map', page:'student-graph' },
    { icon:'chat',      label:'AI Tutor',     page:'ai-chat' },
  ],
  parent: [
    { icon:'dashboard', label:'Overview', page:'parent-dashboard' },
  ],
};

const ROLE_USERS = {
  teacher: { name:'Ms. Williams', sub:'Year 11 · Mathematics', initials:'MW' },
  student: { name:'Aroha Ngata',  sub:'Year 12 · Student',     initials:'AN' },
  parent:  { name:'Parent View',  sub:'Whanau / Caregiver',    initials:'PV' },
};

const TEAL        = '#2D7D6F';
const TEAL_BG     = 'rgba(45,125,111,0.1)';
const TEAL_BORDER = 'rgba(45,125,111,0.28)';

// ── SHARED CARD + LABEL HELPERS ────────────────────────────────────────────
function BlossomCard({ children, style = {} }) {
  return (
    <div style={{
      background:'white', border:'1px solid rgba(61,43,31,0.09)',
      borderRadius:20, boxShadow:'0 2px 18px rgba(61,43,31,0.05)',
      padding:'26px 30px', position:'relative', zIndex:5, ...style,
    }}>
      {children}
    </div>
  );
}

function SectionLabel({ children }) {
  return <div style={{ fontSize:10, letterSpacing:'0.18em', textTransform:'uppercase', color:TEAL, fontStyle:'italic', marginBottom:6 }}>{children}</div>;
}

function SectionTitle({ children, style = {} }) {
  return <h2 style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:'1.35rem', color:'#3D2B1F', letterSpacing:'-0.02em', margin:0, ...style }}>{children}</h2>;
}

function masteryColor(pct) {
  return pct >= 70 ? '#059669' : pct >= 50 ? '#D97706' : '#C0392B';
}

// ── DASHBOARD SHELL ────────────────────────────────────────────────────────
function DashboardShell({ children, subtitle, role = 'teacher', navigate, currentPage }) {
  const [open, setOpen] = useState(false);
  const items = NAV_ITEMS[role] || NAV_ITEMS.teacher;
  const user  = ROLE_USERS[role]  || ROLE_USERS.teacher;

  return (
    <div style={{ minHeight:'100vh', background:'#FDF6EE', position:'relative', fontFamily:"'Lora',serif" }}>

      {/* Tree — z-index 0, purely decorative */}
      <BlossomTree style={{
        position:'fixed', right:-70, top:-50,
        width:440, height:600, opacity:0.14,
        pointerEvents:'none', zIndex:0,
      }}/>

      {/* Petals — z-index 1, behind all content */}
      <PetalLayer count={32}/>

      {/* HEADER — z-index 200 */}
      <header style={{
        position:'sticky', top:0, zIndex:200,
        background:'rgba(253,246,238,0.95)', backdropFilter:'blur(16px)',
        borderBottom:'2px solid #3D2B1F',
        display:'flex', alignItems:'center', gap:16, padding:'14px 28px',
      }}>
        <button onClick={() => setOpen(true)} style={{
          width:40, height:40, borderRadius:10,
          border:'1.5px solid #3D2B1F', background:'#FDF6EE', cursor:'pointer',
          display:'flex', alignItems:'center', justifyContent:'center',
          boxShadow:'2px 2px 0 #3D2B1F', flexShrink:0, position:'relative', zIndex:5,
        }}>
          <svg width="18" height="14" viewBox="0 0 18 14" fill="none">
            <path d="M1 1h16M1 7h16M1 13h16" stroke="#3D2B1F" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>
        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ fontSize:10, letterSpacing:'0.18em', textTransform:'uppercase', color:TEAL, fontStyle:'italic' }}>
            {role==='teacher'?'Teacher':role==='student'?'Student':'Parent'} · AxonAI
          </div>
          <div style={{ fontSize:16, fontFamily:"'Shippori Mincho',serif", fontWeight:600, color:'#3D2B1F', marginTop:2, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>
            {subtitle || 'Dashboard'}
          </div>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:10, flexShrink:0 }}>
          <div style={{ display:'flex', alignItems:'center', gap:6, padding:'5px 12px', borderRadius:20, border:'1px solid rgba(61,43,31,0.1)', background:'rgba(255,255,255,0.7)' }}>
            <div style={{ width:7, height:7, borderRadius:'50%', background:'#059669', boxShadow:'0 0 7px rgba(5,150,105,0.5)' }}/>
            <span style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>API Live</span>
          </div>
          <div style={{ width:36, height:36, borderRadius:'50%', background:TEAL_BG, border:`1.5px solid ${TEAL_BORDER}`, display:'flex', alignItems:'center', justifyContent:'center', fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:13, color:TEAL }}>
            {user.initials}
          </div>
        </div>
      </header>

      {/* SIDEBAR — z-index 500+ */}
      {open && <>
        <div onClick={() => setOpen(false)} style={{ position:'fixed', inset:0, background:'rgba(61,43,31,0.45)', backdropFilter:'blur(3px)', zIndex:500 }}/>
        <aside style={{ position:'fixed', top:0, left:0, bottom:0, width:280, background:'#F0E6D6', borderRight:'2px solid #3D2B1F', zIndex:510, display:'flex', flexDirection:'column', boxShadow:'8px 0 40px rgba(61,43,31,0.2)', overflowY:'auto' }}>
          <BlossomTree style={{ position:'absolute', right:-50, top:-10, width:180, height:240, opacity:0.14, pointerEvents:'none' }}/>

          <div style={{ padding:'18px 20px', borderBottom:'1px solid rgba(61,43,31,0.1)', display:'flex', alignItems:'center', gap:12, position:'relative', zIndex:2 }}>
            <button onClick={() => setOpen(false)} style={{ width:32, height:32, borderRadius:8, border:'1px solid rgba(61,43,31,0.15)', background:'white', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M1 1l10 10M11 1L1 11" stroke="#3D2B1F" strokeWidth="1.8" strokeLinecap="round"/></svg>
            </button>
            <div>
              <div style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:18, color:'#3D2B1F' }}>AxonAI</div>
              <div style={{ fontSize:9, letterSpacing:'0.2em', textTransform:'uppercase', color:'#6B4A3A' }}>School Intelligence</div>
            </div>
          </div>

          <div style={{ padding:'12px 20px 6px', display:'flex', alignItems:'center', gap:10, position:'relative', zIndex:2 }}>
            <span style={{ width:28, height:28, borderRadius:'50%', background:TEAL_BG, border:`1px solid ${TEAL_BORDER}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:10, fontWeight:700, color:TEAL }}>
              {role==='teacher'?'T':role==='student'?'S':'P'}
            </span>
            <span style={{ fontSize:11, letterSpacing:'0.12em', textTransform:'uppercase', color:'#6B4A3A', fontStyle:'italic' }}>
              {role==='teacher'?'Teacher view':role==='student'?'Student view':'Parent view'}
            </span>
          </div>

          <nav style={{ flex:1, padding:'8px 12px', position:'relative', zIndex:2 }}>
            {items.map(item => {
              const active = currentPage === item.page;
              return (
                <button key={item.page} onClick={() => { navigate(item.page); setOpen(false); }} style={{
                  width:'100%', display:'flex', alignItems:'center', gap:12, padding:'11px 14px', borderRadius:12,
                  border:'none', cursor:'pointer', marginBottom:4,
                  background: active ? TEAL_BG : 'transparent',
                  color: active ? TEAL : '#6B4A3A',
                  outline: active ? `1.5px solid ${TEAL_BORDER}` : 'none',
                  fontFamily:"'Lora',serif", fontSize:14, textAlign:'left', transition:'background 0.15s',
                }}>
                  <span style={{ width:28, height:28, borderRadius:8, flexShrink:0, display:'flex', alignItems:'center', justifyContent:'center', background: active ? TEAL_BG : 'rgba(61,43,31,0.05)', border: active ? `1px solid ${TEAL_BORDER}` : '1px solid rgba(61,43,31,0.1)' }}>
                    {NavIcons[item.icon]}
                  </span>
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div style={{ padding:16, borderTop:'1px solid rgba(61,43,31,0.1)', position:'relative', zIndex:2 }}>
            <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:12, padding:'8px 10px', borderRadius:12, background:'rgba(255,255,255,0.5)' }}>
              <div style={{ width:36, height:36, borderRadius:'50%', background:TEAL_BG, display:'flex', alignItems:'center', justifyContent:'center', fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:13, color:TEAL, flexShrink:0 }}>{user.initials}</div>
              <div>
                <div style={{ fontSize:13, fontWeight:500, color:'#3D2B1F' }}>{user.name}</div>
                <div style={{ fontSize:11, color:'#6B4A3A', fontStyle:'italic' }}>{user.sub}</div>
              </div>
            </div>
            <button onClick={() => { navigate('landing'); setOpen(false); }} style={{ width:'100%', padding:9, borderRadius:10, border:'1px solid rgba(61,43,31,0.2)', background:'transparent', fontFamily:"'Lora',serif", fontSize:13, color:'#6B4A3A', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}>
              {NavIcons.logout} Log out
            </button>
          </div>
        </aside>
      </>}

      {/* MAIN CONTENT — z-index 5, above petals */}
      <main style={{ position:'relative', zIndex:5, padding:'28px 32px', maxWidth:1280, margin:'0 auto' }}>
        {children}
      </main>
    </div>
  );
}

// ── PLACEHOLDER PAGE ───────────────────────────────────────────────────────
function PlaceholderPage({ title, role, navigate, currentPage }) {
  return (
    <DashboardShell subtitle={title} role={role} navigate={navigate} currentPage={currentPage}>
      <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:400, gap:24, textAlign:'center', position:'relative', zIndex:5 }}>
        <BlossomTree style={{ width:130, height:170, opacity:0.22, margin:'0 auto' }}/>
        <div>
          <h2 style={{ fontFamily:"'Shippori Mincho',serif", fontSize:'1.8rem', fontWeight:700, color:'#3D2B1F', marginBottom:8 }}>{title}</h2>
          <p style={{ color:'#6B4A3A', fontStyle:'italic', fontSize:'0.95rem' }}>This page is still growing — check back soon.</p>
        </div>
      </div>
    </DashboardShell>
  );
}

Object.assign(window, {
  BlossomTree, PetalLayer, NavIcons,
  DashboardShell, PlaceholderPage,
  BlossomCard, SectionLabel, SectionTitle, masteryColor,
  TEAL, TEAL_BG, TEAL_BORDER,
});
