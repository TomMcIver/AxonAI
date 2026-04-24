
const { useState } = React;

// Updated login — teal accents, no pink UI (pink only on blossom flowers)
function LoginPage({ onLogin }) {
  const [hovered, setHovered] = useState(null);

  const cards = [
    {
      role: 'teacher', dest: 'teacher-dashboard',
      label: 'Teacher', desc: 'Manage classes, track mastery & guide students',
      icon: (
        <svg width="38" height="38" viewBox="0 0 38 38" fill="none">
          <rect x="4" y="6" width="30" height="22" rx="3" stroke="#2D7D6F" strokeWidth="2"/>
          <path d="M14 28v4M24 28v4M10 32h18" stroke="#2D7D6F" strokeWidth="2" strokeLinecap="round"/>
          <path d="M10 15h18M10 19.5h12" stroke="#2D7D6F" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      ),
    },
    {
      role: 'student', dest: 'student-dashboard',
      label: 'Student', desc: 'Learn with your personal AI tutor & track growth',
      icon: (
        <svg width="38" height="38" viewBox="0 0 38 38" fill="none">
          <path d="M19 4L4 13l15 9 15-9-15-9z" stroke="#2D7D6F" strokeWidth="2" strokeLinejoin="round"/>
          <path d="M4 13v11l15 9 15-11V13" stroke="#2D7D6F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M19 22v12" stroke="#2D7D6F" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      ),
    },
    {
      role: 'parent', dest: 'parent-dashboard',
      label: 'Parent', desc: "Stay connected to your child's learning journey",
      icon: (
        <svg width="38" height="38" viewBox="0 0 38 38" fill="none">
          <circle cx="14" cy="12" r="5" stroke="#2D7D6F" strokeWidth="2"/>
          <circle cx="26" cy="11" r="4" stroke="#2D7D6F" strokeWidth="2"/>
          <path d="M4 31c0-5.5 4.5-10 10-10s10 4.5 10 10" stroke="#2D7D6F" strokeWidth="2" strokeLinecap="round"/>
          <path d="M26 17c4 .8 6 4 6 7.5" stroke="#2D7D6F" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      ),
    },
  ];

  return (
    <div style={{ minHeight:'100vh', background:'#FDF6EE', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', overflow:'hidden', position:'relative', fontFamily:"'Lora',serif" }}>

      {/* Lush blossom tree — prominently visible */}
      <BlossomTree style={{ position:'fixed', right:-60, top:-40, width:500, height:700, opacity:0.2, pointerEvents:'none', zIndex:0 }}/>
      <BlossomTree style={{ position:'fixed', left:-120, bottom:-80, width:340, height:460, opacity:0.1, pointerEvents:'none', zIndex:0, transform:'scaleX(-1)' }}/>

      {/* Always-on petals */}
      <PetalLayer count={45}/>

      {/* Back to landing */}
      <button onClick={() => onLogin('landing', null)} style={{ position:'fixed', top:24, left:28, display:'flex', alignItems:'center', gap:8, background:'transparent', border:'none', cursor:'pointer', color:'#6B4A3A', fontFamily:"'Lora',serif", fontSize:13, fontStyle:'italic', zIndex:10 }}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8l4 4" stroke="#6B4A3A" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
        Back to home
      </button>

      {/* Logo */}
      <div style={{ textAlign:'center', marginBottom:52, position:'relative', zIndex:1, animation:'loginFade 0.8s ease both' }}>
        <style>{`@keyframes loginFade{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}`}</style>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:14, marginBottom:18 }}>
          <div style={{ width:54, height:54, borderRadius:'50% 50% 50% 14px', background:'#3D2B1F', display:'flex', alignItems:'center', justifyContent:'center', boxShadow:'0 8px 32px rgba(61,43,31,0.25)' }}>
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <path d="M14 3C14 3 7 7.5 7 14C7 17.6 10.1 20.5 14 20.5C17.9 20.5 21 17.6 21 14C21 10.8 18.8 8.6 17 7.5" stroke="#FDF6EE" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="14" cy="14" r="3" fill="#FDF6EE"/>
            </svg>
          </div>
          <h1 style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:800, fontSize:'3rem', color:'#3D2B1F', letterSpacing:'-0.04em', margin:0 }}>AxonAI</h1>
        </div>
        <p style={{ color:'#6B4A3A', fontStyle:'italic', fontSize:'1rem', margin:0 }}>Who are you learning with today?</p>
        <div style={{ width:36, height:2, background:'#2D7D6F', margin:'14px auto 0', borderRadius:2 }}/>
      </div>

      {/* Role cards */}
      <div style={{ display:'flex', gap:20, flexWrap:'wrap', justifyContent:'center', position:'relative', zIndex:1, padding:'0 24px' }}>
        {cards.map((card, i) => {
          const isHov = hovered === card.role;
          return (
            <button key={card.role}
              onMouseEnter={() => setHovered(card.role)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => onLogin(card.dest, card.role)}
              style={{
                background: isHov ? 'white' : 'rgba(255,255,255,0.72)',
                border: isHov ? '2px solid #2D7D6F' : '1.5px solid rgba(61,43,31,0.12)',
                borderRadius:24, padding:'36px 28px',
                cursor:'pointer', textAlign:'center', width:210,
                boxShadow: isHov ? '0 16px 48px rgba(45,125,111,0.14)' : '0 4px 20px rgba(61,43,31,0.06)',
                transform: isHov ? 'translateY(-6px)' : 'translateY(0)',
                transition:'all 0.25s ease',
                fontFamily:"'Lora',serif",
                display:'flex', flexDirection:'column', alignItems:'center', gap:16,
                animation:`loginFade 0.8s ${0.1 + i * 0.1}s ease both`,
              }}
            >
              <div style={{ width:68, height:68, borderRadius:20, background:isHov?'rgba(45,125,111,0.08)':'rgba(45,125,111,0.05)', display:'flex', alignItems:'center', justifyContent:'center', border:`1px solid ${isHov?'rgba(45,125,111,0.25)':'rgba(45,125,111,0.12)'}`, transition:'all 0.25s' }}>
                {card.icon}
              </div>
              <div>
                <div style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:'1.2rem', color:'#3D2B1F', marginBottom:8 }}>{card.label}</div>
                <div style={{ fontSize:'0.8rem', color:'#6B4A3A', lineHeight:1.65 }}>{card.desc}</div>
              </div>
              <div style={{ display:'flex', alignItems:'center', gap:6, fontSize:'0.8rem', color:isHov?'#2D7D6F':'#6B4A3A', fontStyle:'italic', marginTop:4, transition:'color 0.2s' }}>
                Enter as {card.label}
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 7h8M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </div>
            </button>
          );
        })}
      </div>

      {/* Bottom blossom deco */}
      <div style={{ marginTop:52, position:'relative', zIndex:1, textAlign:'center', animation:'loginFade 1s 0.5s ease both' }}>
        <BlossomTree style={{ width:100, height:130, opacity:0.2, margin:'0 auto' }}/>
        <p style={{ fontSize:'0.72rem', color:'#6B4A3A', fontStyle:'italic', marginTop:6 }}>Where every mind blossoms</p>
      </div>
    </div>
  );
}

Object.assign(window, { LoginPage });
