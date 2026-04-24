import React from 'react';
import { ArrowRight } from 'lucide-react';
import BlossomDecor from '../components/BlossomDecor';

const sections = [
  { id: 'features', label: 'Features' },
  { id: 'adaptive-engine', label: 'Adaptive Engine' },
  { id: 'model-stack', label: 'Model Stack' },
  { id: 'about', label: 'About' },
  { id: 'schools', label: 'For Schools' },
];

const featureRows = [
  'Socratic AI tutor that guides thinking instead of giving answers',
  'Six predictive models tracking mastery, risk, engagement, and momentum in real time',
  'Teacher-first alerts designed for action in under 60 seconds',
  'Parent visibility without adding admin burden to staff',
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
  const scrollTo = (id) => {
    const node = document.getElementById(id);
    if (node) node.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div style={{ minHeight: '100vh', background: '#FDF6EE', position: 'relative', color: '#3D2B1F', fontFamily: "'Lora', serif" }}>
      <BlossomDecor petals={58} />
      <header style={{ position: 'sticky', top: 0, zIndex: 200, borderBottom: '1px solid rgba(61,43,31,0.12)', backdropFilter: 'blur(10px)', background: 'rgba(253,246,238,0.9)' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto', padding: '14px 26px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <button onClick={() => scrollTo('top')} aria-label="AxonAI home" style={{ border: 'none', background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ width: 34, height: 34, borderRadius: '50% 50% 50% 12px', background: '#3D2B1F', color: '#FDF6EE', display: 'grid', placeItems: 'center', fontFamily: "'Shippori Mincho', serif", fontWeight: 700 }}>A</span>
            <span style={{ fontFamily: "'Shippori Mincho', serif", fontSize: 22, fontWeight: 700, color: '#3D2B1F' }}>AxonAI</span>
          </button>
          <nav aria-label="Primary" style={{ display: 'flex', gap: 18 }}>
            {sections.map((link) => (
              <button key={link.id} onClick={() => scrollTo(link.id)} style={{ border: 'none', background: 'transparent', color: '#6B4A3A', fontStyle: 'italic', cursor: 'pointer' }}>
                {link.label}
              </button>
            ))}
          </nav>
          <a href="/login" className="axon-btn" style={{ background: '#3D2B1F', color: '#FDF6EE', borderRadius: 999 }}>See Demo</a>
        </div>
      </header>
      <main id="top" style={{ maxWidth: 1180, margin: '0 auto', padding: '58px 26px', position: 'relative', zIndex: 5 }}>
        <section style={{ minHeight: '70vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 18 }}>
          <span style={{ fontSize: 12, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#2D7D6F', fontStyle: 'italic' }}>Built for New Zealand secondary schools</span>
          <h1 style={{ margin: 0, fontFamily: "'Shippori Mincho', serif", fontSize: 'clamp(2.4rem, 6vw, 4.8rem)', lineHeight: 1.05, letterSpacing: '-0.03em' }}>
            Where every <em style={{ color: '#5C8F7A' }}>mind blossoms</em>.
          </h1>
          <p style={{ maxWidth: 620, margin: 0, color: '#6B4A3A', fontSize: 18, lineHeight: 1.7 }}>
            AxonAI gives teachers predictive insight, students a Socratic AI tutor, and parents real-time visibility, grounded in the NCEA curriculum.
          </p>
          <div>
            <a className="axon-btn" href="/login" style={{ background: '#3D2B1F', color: '#FDF6EE', borderRadius: 999 }}>
              See Demo <ArrowRight size={14} />
            </a>
          </div>
        </section>

        <section id="features" style={{ padding: '40px 0' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>Built Different</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: 34, marginTop: 8 }}>Why schools pick AxonAI</h2>
          <div style={{ display: 'grid', gap: 10, background: 'white', border: '1px solid rgba(61,43,31,0.1)', borderRadius: 16, padding: 22 }}>
            {featureRows.map((item) => (
              <p key={item} style={{ margin: 0, color: '#6B4A3A' }}>• {item}</p>
            ))}
          </div>
        </section>

        <section id="adaptive-engine" style={{ padding: '24px 0' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>Adaptive Engine</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: 34, marginTop: 8 }}>No more repetitive question loops</h2>
          <div style={{ display: 'grid', gap: 10, background: 'rgba(255,255,255,0.92)', border: '1px solid rgba(61,43,31,0.1)', borderRadius: 16, padding: 22 }}>
            {adaptiveRows.map((item) => (
              <p key={item} style={{ margin: 0, color: '#6B4A3A', lineHeight: 1.65 }}>• {item}</p>
            ))}
          </div>
        </section>

        <section id="model-stack" style={{ padding: '24px 0' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>Model Stack</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: 34, marginTop: 8 }}>How AxonAI intelligence works</h2>
          <div style={{ display: 'grid', gap: 10, background: 'white', border: '1px solid rgba(61,43,31,0.1)', borderRadius: 16, padding: 22 }}>
            {modelRows.map((item) => (
              <p key={item} style={{ margin: 0, color: '#6B4A3A', lineHeight: 1.65 }}>• {item}</p>
            ))}
          </div>
        </section>

        <section id="schools" style={{ padding: '24px 0' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>For Schools</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: 34, marginTop: 8 }}>Built for real classrooms, not demos</h2>
          <p style={{ maxWidth: 850, color: '#6B4A3A', lineHeight: 1.8, marginTop: 10 }}>
            Teachers get fast intervention signals, students get adaptive support that changes with their learning, and families
            get clear progress visibility. AxonAI is designed to strengthen teacher decisions, not replace them.
          </p>
        </section>

        <section id="about" style={{ padding: '24px 0 40px' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.16em', color: '#2D7D6F', fontStyle: 'italic' }}>About</p>
          <h2 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: 34, marginTop: 8 }}>Personalised learning that truly adapts</h2>
          <p style={{ maxWidth: 850, color: '#6B4A3A', lineHeight: 1.8, marginTop: 10 }}>
            Most software repeats static practice sets. AxonAI continuously updates what each learner sees next — questions,
            explanations, and support strategy — based on how they are performing right now.
          </p>
        </section>
      </main>
    </div>
  );
}
