
const { useState, useEffect } = React;

function LandingPage({ onDemo }) {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Intersection observer for scroll reveals
  useEffect(() => {
    const els = document.querySelectorAll('.land-reveal');
    const obs = new IntersectionObserver(entries => {
      entries.forEach((e, i) => {
        if (e.isIntersecting) {
          setTimeout(() => e.target.classList.add('land-visible'), i * 80);
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);

  const features = [
    {
      icon: (
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <circle cx="14" cy="14" r="10" stroke="#2D7D6F" strokeWidth="1.8" fill="none"/>
          <path d="M14 9v5l3 2" stroke="#2D7D6F" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
      ),
      title: 'Adaptive AI algorithms',
      body: "Axon maps each student's unique learning pattern and adjusts in real time — no child left behind or held back.",
      pills: ['Students', 'Parents'],
    },
    {
      icon: (
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <path d="M5 20l4-8 4 5 3-4 5 7" stroke="#2D7D6F" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          <circle cx="21" cy="7" r="3" stroke="#2D7D6F" strokeWidth="1.8"/>
        </svg>
      ),
      title: 'Real-time insights',
      body: 'Live dashboards reveal exactly where each student struggles, so teachers can intervene before gaps become problems.',
      pills: ['Teachers'],
    },
    {
      icon: (
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <path d="M8 13h12M8 9h9M8 17h6" stroke="#2D7D6F" strokeWidth="1.8" strokeLinecap="round"/>
          <rect x="4" y="4" width="20" height="20" rx="4" stroke="#2D7D6F" strokeWidth="1.8"/>
        </svg>
      ),
      title: 'Custom AI curriculum',
      body: 'Teachers build lesson plans in minutes. Axon fills every gap with AI-generated exercises tuned to each student.',
      pills: ['Teachers', 'Students'],
    },
    {
      icon: (
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <path d="M14 4l3 6 6.5 1-4.7 4.6 1.1 6.5L14 19l-5.9 3.1 1.1-6.5L4.5 11l6.5-1z" stroke="#2D7D6F" strokeWidth="1.8" strokeLinejoin="round"/>
        </svg>
      ),
      title: 'Progress parents can see',
      body: 'Weekly summaries and milestone moments keep families engaged — no more wondering how your child is really doing.',
      pills: ['Parents'],
    },
  ];

  const steps = [
    { num:'01', title:'Create your profile', body:'Teachers, parents, and students each get tailored onboarding. Set goals and subjects in minutes.' },
    { num:'02', title:'Axon maps the path', body:'Our algorithm builds a personalised learning journey based on each student\'s current knowledge and pace.' },
    { num:'03', title:'Watch the growth', body:'Students learn. Teachers guide. Parents celebrate. Weekly reports keep everyone connected to the journey.' },
  ];

  return (
    <div style={{ background:'#FDF6EE', fontFamily:"'Lora',serif", color:'#3D2B1F', overflowX:'hidden', position:'relative' }}>

      <style>{`
        .land-reveal { opacity:0; transform:translateY(28px); }
        .land-visible { opacity:1; transform:translateY(0); transition:opacity 0.8s ease, transform 0.8s ease; }
        @keyframes heroFadeUp { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
        @keyframes scrollPulse { 0%,100%{opacity:0.35;transform:scaleY(1)} 50%{opacity:1;transform:scaleY(1.15)} }
      `}</style>

      {/* Fixed blossom tree — large, prominent, right side */}
      <BlossomTree style={{
        position:'fixed', right:-80, top:-60,
        width:560, height:760, opacity:0.18,
        pointerEvents:'none', zIndex:0,
      }}/>

      {/* Always-on petals */}
      <PetalLayer count={55}/>

      {/* ── NAV ── */}
      <nav style={{
        position:'fixed', top:0, left:0, right:0, zIndex:300,
        display:'flex', alignItems:'center', justifyContent:'space-between',
        padding:'18px 56px',
        background:'rgba(253,246,238,0.88)', backdropFilter:'blur(14px)',
        borderBottom:'1px solid rgba(61,43,31,0.1)',
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:12, fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:'1.35rem', color:'#3D2B1F' }}>
          <div style={{ width:34, height:34, borderRadius:'50% 50% 50% 12px', background:'#3D2B1F', display:'flex', alignItems:'center', justifyContent:'center' }}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 2C9 2 5 5 5 9C5 11.2 6.8 13 9 13C11.2 13 13 11.2 13 9C13 6.8 11.2 5 9 5" stroke="#FDF6EE" strokeWidth="1.6" strokeLinecap="round"/>
              <circle cx="9" cy="9" r="1.8" fill="#FDF6EE"/>
            </svg>
          </div>
          AxonAI
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:32 }}>
          {['Features','How it works'].map(l => (
            <a key={l} href={`#${l.toLowerCase().replace(/ /g,'-')}`} style={{ fontSize:'0.9rem', color:'#6B4A3A', textDecoration:'none', fontStyle:'italic', transition:'color 0.2s' }}
              onMouseEnter={e => e.target.style.color='#2D7D6F'}
              onMouseLeave={e => e.target.style.color='#6B4A3A'}
            >{l}</a>
          ))}
          <button onClick={onDemo} style={{
            padding:'10px 26px', borderRadius:40, border:'none',
            background:'#3D2B1F', color:'#FDF6EE',
            fontFamily:"'Lora',serif", fontSize:'0.9rem', cursor:'pointer',
            transition:'background 0.2s, transform 0.2s',
            boxShadow:'0 4px 16px rgba(61,43,31,0.18)',
          }}
            onMouseEnter={e => { e.target.style.background='#2D7D6F'; e.target.style.transform='translateY(-1px)'; }}
            onMouseLeave={e => { e.target.style.background='#3D2B1F'; e.target.style.transform=''; }}
          >Go to demo →</button>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section style={{ minHeight:'100vh', display:'flex', flexDirection:'column', justifyContent:'center', padding:'120px 10vw 80px', position:'relative', zIndex:1 }}>
        <div style={{ animation:'heroFadeUp 0.9s 0.1s ease both', display:'flex', alignItems:'center', gap:10, marginBottom:28 }}>
          <div style={{ width:40, height:1.5, background:'#2D7D6F', borderRadius:2 }}/>
          <span style={{ fontSize:'0.78rem', letterSpacing:'0.14em', textTransform:'uppercase', color:'#2D7D6F', fontStyle:'italic' }}>AI-powered tutoring platform</span>
        </div>

        <h1 style={{ animation:'heroFadeUp 1s 0.3s ease both', fontFamily:"'Shippori Mincho',serif", fontWeight:800, fontSize:'clamp(3.2rem,8vw,7rem)', lineHeight:1.0, letterSpacing:'-0.03em', color:'#3D2B1F', maxWidth:680, margin:0 }}>
          Where every<br/><em style={{ fontStyle:'italic', color:'#5C8F7A' }}>mind blossoms.</em>
        </h1>

        <p style={{ animation:'heroFadeUp 1s 0.5s ease both', fontSize:'clamp(1rem,1.8vw,1.15rem)', color:'#6B4A3A', maxWidth:460, marginTop:28, lineHeight:1.8 }}>
          Axon AI brings together intelligent algorithms and thoughtful learning design — for students who dream, teachers who inspire, and parents who believe.
        </p>

        <div style={{ animation:'heroFadeUp 1s 0.7s ease both', display:'flex', alignItems:'center', gap:20, marginTop:44 }}>
          <button onClick={onDemo} style={{
            padding:'16px 44px', borderRadius:50, border:'none',
            background:'#3D2B1F', color:'#FDF6EE',
            fontFamily:"'Lora',serif", fontSize:'1rem', cursor:'pointer',
            boxShadow:'0 8px 32px rgba(61,43,31,0.22)',
            transition:'background 0.25s, transform 0.2s',
          }}
            onMouseEnter={e => { e.target.style.background='#2D7D6F'; e.target.style.transform='translateY(-2px)'; }}
            onMouseLeave={e => { e.target.style.background='#3D2B1F'; e.target.style.transform=''; }}
          >Try the demo</button>
          <a href="#how-it-works" style={{ color:'#6B4A3A', fontStyle:'italic', fontSize:'0.95rem', textDecoration:'none', borderBottom:'1px solid rgba(107,74,58,0.3)', paddingBottom:2 }}>See how it works →</a>
        </div>

        {/* Scroll hint */}
        <div style={{ animation:'heroFadeUp 1s 1.2s ease both', position:'absolute', bottom:40, left:'50%', transform:'translateX(-50%)', display:'flex', flexDirection:'column', alignItems:'center', gap:8 }}>
          <span style={{ fontSize:'0.68rem', letterSpacing:'0.2em', textTransform:'uppercase', color:'#6B4A3A' }}>Explore</span>
          <div style={{ width:1, height:38, background:'linear-gradient(to bottom, #2D7D6F, transparent)', animation:'scrollPulse 2s ease-in-out infinite' }}/>
        </div>
      </section>

      {/* ── TRUST BAR ── */}
      <div style={{ background:'#3D2B1F', padding:'32px 56px', display:'flex', alignItems:'center', justifyContent:'center', gap:56, flexWrap:'wrap', position:'relative', zIndex:1 }}>
        <span style={{ fontSize:'0.72rem', letterSpacing:'0.16em', textTransform:'uppercase', color:'rgba(253,246,238,0.35)' }}>Trusted by</span>
        {[['2,400+','students learning daily'],['380','teachers on the platform'],['94%','parent satisfaction rate'],['12 mo','avg. grade improvement']].map(([num,label]) => (
          <div key={label} style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:4 }}>
            <span style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:'1.7rem', color:'rgba(253,246,238,0.75)' }}>{num}</span>
            <span style={{ fontSize:'0.75rem', color:'rgba(253,246,238,0.38)', fontStyle:'italic' }}>{label}</span>
          </div>
        ))}
      </div>

      {/* ── FEATURES ── */}
      <section id="features" style={{ padding:'110px 8vw', maxWidth:1280, margin:'0 auto', position:'relative', zIndex:1 }}>
        <div style={{ textAlign:'center', marginBottom:70 }}>
          <div className="land-reveal" style={{ fontSize:'0.8rem', letterSpacing:'0.14em', textTransform:'uppercase', color:'#2D7D6F', fontStyle:'italic', marginBottom:12 }}>Built for everyone who matters</div>
          <h2 className="land-reveal" style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:'clamp(1.8rem,4vw,3rem)', color:'#3D2B1F', letterSpacing:'-0.02em', lineHeight:1.2 }}>
            Learning that grows<br/>with your child
          </h2>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))', gap:24 }}>
          {features.map((f, i) => (
            <div key={i} className="land-reveal" style={{
              background:'white', border:'1px solid rgba(45,125,111,0.15)',
              borderRadius:22, padding:'36px 30px',
              boxShadow:'0 2px 24px rgba(61,43,31,0.05)',
              transition:'transform 0.25s, box-shadow 0.25s',
              position:'relative', overflow:'hidden',
            }}
              onMouseEnter={e => { e.currentTarget.style.transform='translateY(-5px)'; e.currentTarget.style.boxShadow='0 16px 48px rgba(61,43,31,0.1)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform=''; e.currentTarget.style.boxShadow='0 2px 24px rgba(61,43,31,0.05)'; }}
            >
              <div style={{ position:'absolute', top:0, right:0, width:100, height:100, background:'radial-gradient(circle at top right, rgba(45,125,111,0.07), transparent 70%)', borderRadius:'0 22px 0 0' }}/>
              <div style={{ width:52, height:52, borderRadius:16, background:'rgba(45,125,111,0.07)', border:'1px solid rgba(45,125,111,0.18)', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:22 }}>
                {f.icon}
              </div>
              <h3 style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:600, fontSize:'1.15rem', color:'#3D2B1F', marginBottom:12, lineHeight:1.3 }}>{f.title}</h3>
              <p style={{ fontSize:'0.9rem', color:'#6B4A3A', lineHeight:1.75, marginBottom:18 }}>{f.body}</p>
              <div style={{ display:'flex', gap:6, flexWrap:'wrap' }}>
                {f.pills.map(p => (
                  <span key={p} style={{ padding:'3px 12px', borderRadius:20, border:'1px solid rgba(45,125,111,0.25)', color:'#2D7D6F', fontSize:'0.75rem', fontStyle:'italic' }}>{p}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how-it-works" style={{ background:'#3D2B1F', padding:'110px 8vw', position:'relative', zIndex:1, overflow:'hidden' }}>
        {/* Dark-bg blossom tree */}
        <BlossomTree style={{ position:'absolute', left:-80, top:-60, width:420, height:580, opacity:0.06, pointerEvents:'none' }}/>

        <div style={{ maxWidth:1100, margin:'0 auto', position:'relative' }}>
          <div style={{ textAlign:'center', marginBottom:72 }}>
            <div className="land-reveal" style={{ fontSize:'0.8rem', letterSpacing:'0.14em', textTransform:'uppercase', color:'rgba(253,246,238,0.4)', fontStyle:'italic', marginBottom:12 }}>Simple from the start</div>
            <h2 className="land-reveal" style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700, fontSize:'clamp(1.8rem,4vw,3rem)', color:'#FDF6EE', letterSpacing:'-0.02em', lineHeight:1.2 }}>
              Getting started takes<br/>less than a morning
            </h2>
          </div>

          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(260px,1fr))', gap:48 }}>
            {steps.map((s, i) => (
              <div key={i} className="land-reveal" style={{ display:'flex', flexDirection:'column', gap:18 }}>
                <span style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:800, fontSize:'4.5rem', color:'rgba(253,246,238,0.12)', lineHeight:1, letterSpacing:'-0.04em' }}>{s.num}</span>
                <div style={{ width:36, height:1.5, background:'#2D7D6F', borderRadius:2 }}/>
                <h3 style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:600, fontSize:'1.2rem', color:'#FDF6EE', lineHeight:1.3 }}>{s.title}</h3>
                <p style={{ fontSize:'0.9rem', color:'rgba(253,246,238,0.5)', lineHeight:1.8 }}>{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ padding:'120px 8vw', textAlign:'center', position:'relative', zIndex:1 }}>
        <h2 className="land-reveal" style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:800, fontSize:'clamp(2rem,5vw,3.6rem)', color:'#3D2B1F', lineHeight:1.15, letterSpacing:'-0.02em', maxWidth:640, margin:'0 auto 16px' }}>
          Ready to let every child <em style={{ color:'#5C8F7A' }}>bloom?</em>
        </h2>
        <p className="land-reveal" style={{ fontSize:'1rem', color:'#6B4A3A', fontStyle:'italic', marginBottom:44 }}>Explore the live demo — no sign-up needed.</p>
        <button className="land-reveal" onClick={onDemo} style={{
          padding:'18px 52px', borderRadius:50, border:'none',
          background:'#3D2B1F', color:'#FDF6EE',
          fontFamily:"'Shippori Mincho',serif", fontWeight:600, fontSize:'1.15rem', cursor:'pointer',
          boxShadow:'0 8px 40px rgba(61,43,31,0.2)',
          transition:'background 0.25s, transform 0.2s',
        }}
          onMouseEnter={e => { e.target.style.background='#2D7D6F'; e.target.style.transform='translateY(-2px)'; }}
          onMouseLeave={e => { e.target.style.background='#3D2B1F'; e.target.style.transform=''; }}
        >Go to demo →</button>

        {/* Small blossom tree deco */}
        <div style={{ marginTop:60, display:'flex', justifyContent:'center' }}>
          <BlossomTree style={{ width:160, height:200, opacity:0.18 }}/>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer style={{ padding:'28px 56px', borderTop:'1px solid rgba(61,43,31,0.1)', display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:12, position:'relative', zIndex:1 }}>
        <span style={{ fontFamily:"'Shippori Mincho',serif", fontWeight:700 }}>AxonAI</span>
        <span style={{ fontSize:'0.8rem', color:'#6B4A3A', fontStyle:'italic' }}>© 2026 AxonAI · Where every mind blossoms</span>
        <span style={{ fontSize:'0.8rem', color:'#6B4A3A', fontStyle:'italic' }}>hello@axonai.co</span>
      </footer>
    </div>
  );
}

Object.assign(window, { LandingPage });
