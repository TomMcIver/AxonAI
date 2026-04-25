import React, { useEffect, useState } from 'react';
import { ArrowRight, Menu, X } from 'lucide-react';
import BlossomDecor from '../components/BlossomDecor';

const sections = [
  { id: 'features', label: 'Features' },
  { id: 'adaptive-engine', label: 'Adaptive Engine' },
  { id: 'model-stack', label: 'Model Stack' },
  { id: 'about', label: 'About' },
  { id: 'schools', label: 'For Schools' },
];

const featureRows = [
  'Students reach mastery in 67 attempts vs 94 for unguided practice — 29% faster, p less than 0.01',
  'Knowledge retained after 30 days: 26.5% with AxonAI vs 23.8% without — validated on 500 simulated students across a 12-week term',
  'Misconception detection — when a student gets something wrong the system identifies which specific misconception caused it, not just that they failed',
  'Teacher dashboard showing which students are at risk, which concepts the class is losing, and recommended next actions',
];

const adaptiveRows = [
  'AxonAI regenerates questions and learning material per student profile, not a fixed worksheet loop.',
  'When a learner gets stuck, the tutor rewrites explanation style, adjusts difficulty, and changes the next task path.',
  'The system learns from each response, so students do not keep seeing the same repetitive five-question cycle.',
  'Each child receives an evolving route tuned to pace, misconceptions, confidence, and engagement.',
];

const modelRows = [
  'Tutor model: Socratic conversational guidance tailored to student profile and context.',
  'Mastery modelling: concept-level tracking that updates after each interaction.',
  'Psychometric layer: BKT / IRT style performance signals for stronger progression logic.',
  'Misconception pipeline: detect → retrieve likely gaps → rerank best intervention path.',
  'Global coordinator: cross-student pattern analysis to push better strategies back to tutors.',
  'Teacher insights engine: turns model signals into practical next actions and intervention prompts.',
];

export default function Landing() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [isCompact, setIsCompact] = useState(() => window.innerWidth < 960);
  const [isPhone, setIsPhone] = useState(() => window.innerWidth < 768);
  const [isTablet, setIsTablet] = useState(() => window.innerWidth >= 768 && window.innerWidth < 1200);

  useEffect(() => {
    const onResize = () => {
      const w = window.innerWidth;
      setIsCompact(w < 960);
      setIsPhone(w < 768);
      setIsTablet(w >= 768 && w < 1200);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    if (!isCompact) setMenuOpen(false);
  }, [isCompact]);

  const scrollTo = (id) => {
    const node = document.getElementById(id);
    if (node) node.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setMenuOpen(false);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#FDF6EE', position: 'relative', color: '#3D2B1F', fontFamily: "'Lora', serif" }}>
      <BlossomDecor petals={isCompact ? 28 : 58} compact={isCompact} singleTree={isPhone} />
      <header style={{ position: 'sticky', top: 0, zIndex: 200, borderBottom: '1px solid rgba(61,43,31,0.12)', backdropFilter: 'blur(10px)', background: 'rgba(253,246,238,0.9)' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto', padding: isCompact ? '10px 16px' : '14px 26px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
          <button onClick={() => scrollTo('top')} aria-label="AxonAI home" style={{ border: 'none', background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ width: isCompact ? 30 : 34, height: isCompact ? 30 : 34, borderRadius: '50% 50% 50% 12px', background: '#3D2B1F', color: '#FDF6EE', display: 'grid', placeItems: 'center', fontFamily: "'Shippori Mincho', serif", fontWeight: 700 }}>A</span>
            <span style={{ fontFamily: "'Shippori Mincho', serif", fontSize: isCompact ? 38 / 2 : 22, fontWeight: 700, color: '#3D2B1F' }}>AxonAI</span>
          </button>
          {!isCompact && <nav aria-label="Primary" style={{ display: 'flex', gap: 18 }}>
            {sections.map((link) => (
              <button key={link.id} onClick={() => scrollTo(link.id)} style={{ border: 'none', background: 'transparent', color: '#6B4A3A', fontStyle: 'italic', cursor: 'pointer' }}>
                {link.label}
              </button>
            ))}
          </nav>}
          {!isCompact && <a href="/login" className="axon-btn" style={{ background: '#3D2B1F', color: '#FDF6EE', borderRadius: 999 }}>See Demo</a>}
          {isCompact && (
            <button
              type="button"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label="Toggle menu"
              style={{
                border: '1px solid rgba(61,43,31,0.2)',
                background: 'rgba(255,255,255,0.7)',
                borderRadius: 10,
                width: 36,
                height: 36,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#3D2B1F',
              }}
            >
              {menuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          )}
        </div>
        {isCompact && menuOpen && (
          <nav aria-label="Primary mobile" style={{ borderTop: '1px solid rgba(61,43,31,0.12)', padding: '8px 12px 12px', display: 'grid', gap: 6 }}>
            {sections.map((link) => (
              <button
                key={link.id}
                onClick={() => scrollTo(link.id)}
                style={{ border: '1px solid rgba(61,43,31,0.14)', borderRadius: 10, background: 'rgba(255,255,255,0.66)', color: '#6B4A3A', fontStyle: 'italic', cursor: 'pointer', textAlign: 'left', padding: '8px 10px' }}
              >
                {link.label}
              </button>
            ))}
            <a href="/login" className="axon-btn" style={{ width: '100%', justifyContent: 'center', background: '#3D2B1F', color: '#FDF6EE', borderRadius: 999 }}>
              See Demo
            </a>
          </nav>
        )}
      </header>
      <main id="top" style={{ maxWidth: 1180, margin: '0 auto', padding: isCompact ? '26px 16px' : '58px 26px', position: 'relative', zIndex: 5 }}>
        <section
          style={{
            minHeight: isPhone || isTablet ? 'auto' : '52vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            gap: isCompact ? 14 : 18,
            paddingBottom: isCompact ? 2 : 0,
          }}
        >
          <span style={{ fontSize: 12, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#2D7D6F', fontStyle: 'italic' }}>NZ pilot open — Years 9–11 mathematics 2026.</span>
          <h1 style={{ margin: 0, fontFamily: "'Shippori Mincho', serif", fontSize: isCompact ? 'clamp(2rem, 9vw, 3.2rem)' : 'clamp(2.4rem, 6vw, 4.8rem)', lineHeight: 1.12, letterSpacing: '-0.03em', maxWidth: isCompact ? 460 : 'none' }}>
            Your students are in the wrong questions. We fix that.
          </h1>
          <p style={{ maxWidth: isCompact ? 520 : 620, margin: 0, color: '#6B4A3A', fontSize: isCompact ? 16 : 18, lineHeight: 1.7 }}>
            AxonAI's adaptive engine finds the zone where each student learns fastest — not too easy, not too hard — and keeps them there. Our validation study shows students reach mastery 29% faster and retain more of what they learn. Built for NZ secondary schools, grounded in NCEA, validated on 2.4 million real student responses.
          </p>
          <div>
            <a className="axon-btn" href="/login" style={{ background: '#3D2B1F', color: '#FDF6EE', borderRadius: 999 }}>
              See Demo <ArrowRight size={14} />
            </a>
          </div>
        </section>

        <section id="features" style={{ padding: isCompact ? '18px 0' : '40px 0' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>Built Different</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: isCompact ? 26 : 34, marginTop: 8 }}>What the data shows.</h2>
          <p style={{ maxWidth: 850, color: '#6B4A3A', lineHeight: 1.8, marginTop: 10 }}>
            These numbers come from a controlled simulation study — 500 students, 12 weeks, adaptive engine vs random practice. All results statistically significant at p less than 0.01. NZ school pilot starting 2026 to validate against real NCEA exam outcomes.
          </p>
          <div style={{ display: 'grid', gap: 10, background: 'white', border: '1px solid rgba(61,43,31,0.1)', borderRadius: 16, padding: isCompact ? 16 : 22 }}>
            {featureRows.map((item) => (
              <p key={item} style={{ margin: 0, color: '#6B4A3A' }}>• {item}</p>
            ))}
          </div>
        </section>

        <section id="adaptive-engine" style={{ padding: isCompact ? '14px 0' : '24px 0' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>Adaptive Engine</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: isCompact ? 26 : 34, marginTop: 8 }}>No more repetitive question loops</h2>
          <div style={{ display: 'grid', gap: 10, background: 'rgba(255,255,255,0.92)', border: '1px solid rgba(61,43,31,0.1)', borderRadius: 16, padding: isCompact ? 16 : 22 }}>
            {adaptiveRows.map((item) => (
              <p key={item} style={{ margin: 0, color: '#6B4A3A', lineHeight: 1.65 }}>• {item}</p>
            ))}
          </div>
        </section>

        <section id="model-stack" style={{ padding: isCompact ? '14px 0' : '24px 0' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>Model Stack</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: isCompact ? 26 : 34, marginTop: 8 }}>How AxonAI intelligence works</h2>
          <div style={{ display: 'grid', gap: 10, background: 'white', border: '1px solid rgba(61,43,31,0.1)', borderRadius: 16, padding: isCompact ? 16 : 22 }}>
            {modelRows.map((item) => (
              <p key={item} style={{ margin: 0, color: '#6B4A3A', lineHeight: 1.65 }}>• {item}</p>
            ))}
          </div>
        </section>

        <section id="schools" style={{ padding: isCompact ? '14px 0' : '24px 0' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>For Schools</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: isCompact ? 26 : 34, marginTop: 8 }}>By the time a teacher notices, weeks have passed.</h2>
          <p style={{ maxWidth: 850, color: '#6B4A3A', lineHeight: 1.8, marginTop: 10 }}>
            AxonAI detects in-session — not at the end of term. When a student starts struggling, the engine flags it immediately, adjusts the next question, and surfaces it on the teacher dashboard before the gap compounds. No extra admin. No new workflow.
          </p>
        </section>

        <section id="about" style={{ padding: isCompact ? '14px 0 26px' : '24px 0 40px' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>About</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: isCompact ? 26 : 34, marginTop: 8 }}>Research-backed, NCEA-aligned, built in Auckland.</h2>
          <p style={{ maxWidth: 850, color: '#6B4A3A', lineHeight: 1.8, marginTop: 10 }}>
            Built with academic advisors from the University of Auckland. Calibrated on 2.4 million real student responses across 6,799 math problems. The adaptive engine is validated — the NZ pilot starting Term 3 2026 will measure the lift in actual NCEA exam scores. Target is 5% or more improvement vs control. AxonAI gives teachers better information — it does not replace them.
          </p>
        </section>
      </main>
    </div>
  );
}
