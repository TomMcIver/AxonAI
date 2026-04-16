import React, { useEffect } from 'react';
import { ArrowRight } from 'lucide-react';

const sections = [
  { id: 'features', label: 'Features' },
  { id: 'about', label: 'About' },
  { id: 'schools', label: 'For Schools' },
];

const featureRows = [
  'Socratic AI tutor that guides thinking instead of giving answers',
  'Six predictive models tracking mastery, risk, engagement, and momentum',
  'Teacher-first alerts designed for action in under 60 seconds',
  'Parent visibility without adding admin burden to staff',
];

function isInViewport(el) {
  const rect = el.getBoundingClientRect();
  const vh = window.innerHeight || document.documentElement.clientHeight;
  return rect.top < vh && rect.bottom > 0;
}

export default function Landing() {
  useEffect(() => {
    const nodes = document.querySelectorAll('[data-lp2-reveal]');
    const reveal = el => {
      el.classList.add('is-visible');
    };

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          reveal(entry.target);
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.05, rootMargin: '0px 0px -5% 0px' }
    );

    const runFallback = () => {
      document.querySelectorAll('[data-lp2-reveal]').forEach(n => {
        if (n.classList.contains('is-visible')) return;
        if (isInViewport(n)) {
          reveal(n);
          try {
            observer.unobserve(n);
          } catch {
            /* ignore */
          }
        }
      });
    };

    nodes.forEach(n => observer.observe(n));

    // Fix blank page on browser back / bfcache: IO sometimes skips already-visible nodes.
    requestAnimationFrame(() => {
      requestAnimationFrame(runFallback);
    });
    const t = window.setTimeout(runFallback, 120);

    const onPageShow = e => {
      if (e.persisted) {
        document.querySelectorAll('[data-lp2-reveal]').forEach(n => n.classList.add('is-visible'));
      } else {
        runFallback();
      }
    };
    window.addEventListener('pageshow', onPageShow);

    return () => {
      window.clearTimeout(t);
      window.removeEventListener('pageshow', onPageShow);
      observer.disconnect();
    };
  }, []);

  const scrollTo = id => {
    const node = document.getElementById(id);
    if (node) node.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="lp2-root app-shell ux-auth-surface min-h-screen">
      <header className="lp2-nav">
        <div className="lp2-wrap lp2-nav-inner">
          <button className="lp2-brand" onClick={() => scrollTo('top')} aria-label="AxonAI home">
            <span className="lp2-badge">A</span>
            <span className="lp2-word">AXONAI</span>
          </button>

          <nav className="lp2-links" aria-label="Primary">
            {sections.map(link => (
              <button key={link.id} onClick={() => scrollTo(link.id)}>
                {link.label}
              </button>
            ))}
          </nav>

          <div className="lp2-actions">
            <a className="axon-btn axon-btn-primary lp2-hide-mobile" href="/login">
              See Demo
            </a>
          </div>
        </div>
      </header>

      <main id="top" className="lp2-main">
        <section className="lp2-wrap lp2-hero">
          <div className="lp2-orb lp2-orb-a" aria-hidden="true" />
          <div className="lp2-orb lp2-orb-b" aria-hidden="true" />
          <div className="lp2-grid-sweep" aria-hidden="true" />
          <span className="lp2-pill lp2-reveal-up" data-lp2-reveal>
            Built for New Zealand secondary schools
          </span>
          <h1 className="lp2-title lp2-reveal-up" data-lp2-reveal>
            The intelligence layer your school is missing.
          </h1>
          <p className="lp2-copy lp2-reveal-up" data-lp2-reveal>
            AxonAI gives teachers predictive insight, students a Socratic AI tutor, and parents real-time visibility —
            grounded in the NCEA curriculum.
          </p>
          <div className="lp2-cta lp2-reveal-up" data-lp2-reveal>
            <a className="axon-btn axon-btn-primary lp2-cta-pulse" href="/login">
              See Demo <ArrowRight size={14} />
            </a>
          </div>
        </section>

        <section className="lp2-wrap lp2-section lp2-reveal-up" id="features" data-lp2-reveal>
          <p className="lp2-kicker">Built Different</p>
          <h2>Why schools pick AxonAI</h2>
          <div className="lp2-panel">
            {featureRows.map(item => (
              <p key={item}>• {item}</p>
            ))}
          </div>
        </section>

        <section className="lp2-wrap lp2-section lp2-reveal-up" id="schools" data-lp2-reveal>
          <p className="lp2-kicker">For Schools</p>
          <h2>Learning failure is a detection problem.</h2>
          <p className="lp2-copy">
            By the time a teacher notices a student is lost, weeks have passed. AxonAI detects risk in-session and
            turns it into clear next actions for teachers and whānau.
          </p>
        </section>

        <section className="lp2-wrap lp2-section lp2-reveal-up" id="about" data-lp2-reveal>
          <p className="lp2-kicker">Built in Auckland</p>
          <h2>Teacher-first, NCEA-aligned, research-backed.</h2>
          <p className="lp2-copy">
            We build with New Zealand schools, inside the NCEA framework, in partnership with University of Auckland
            researchers. AxonAI augments teachers — it does not replace them.
          </p>
        </section>
      </main>
    </div>
  );
}
