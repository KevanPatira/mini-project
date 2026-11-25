import React, { useState, useEffect, useRef } from 'react';
import {
  Mountain, Leaf, Users, Route, Compass, GitCompare,
  MapPin, Calendar, BarChart3, ChevronRight, ChevronDown,
  Wind, Sun, Shield, TreePine, ArrowRight, Menu, X
} from 'lucide-react';
import '../styles/landing.css';

import heroImg from '../assets/hero-rajasthan.jpg';
import jaipurImg from '../assets/jaipur-hawa-mahal.jpg';
import udaipurImg from '../assets/udaipur-lake.jpg';
import jaisalmerImg from '../assets/jaisalmer-fort.jpg';
import jodhpurImg from '../assets/jodhpur-blue.jpg';
import pushkarImg from '../assets/pushkar-lake.jpg';
import desertImg from '../assets/desert-dunes.jpg';

const CURRENT_YEAR = new Date().getFullYear();

const DESTINATIONS = [
  {
    name: 'Jaipur',
    tagline: 'The Pink City',
    desc: 'Royal palaces, vibrant bazaars, and Mughal-Rajput architectural marvels in the heart of Rajasthan.',
    img: jaipurImg,
    fallback: 'linear-gradient(135deg, #C56B45 0%, #8A3D1E 100%)',
  },
  {
    name: 'Udaipur',
    tagline: 'City of Lakes',
    desc: 'Lakeside palaces and romantic vistas where water mirrors the sky.',
    img: udaipurImg,
    fallback: 'linear-gradient(135deg, #315C4C 0%, #1F3A32 100%)',
  },
  {
    name: 'Jaisalmer',
    tagline: 'The Golden City',
    desc: 'A living desert citadel rising from the Thar sands.',
    img: jaisalmerImg,
    fallback: 'linear-gradient(135deg, #B87333 0%, #8A3D1E 100%)',
  },
  {
    name: 'Jodhpur',
    tagline: 'The Blue City',
    desc: 'Indigo-washed lanes crowned by the mighty Mehrangarh Fort.',
    img: jodhpurImg,
    fallback: 'linear-gradient(135deg, #3B6FA0 0%, #1F3A32 100%)',
  },
  {
    name: 'Pushkar',
    tagline: 'Sacred Lake Town',
    desc: 'Pilgrimage ghats, a holy lake, and one of India\'s oldest temple towns.',
    img: pushkarImg,
    fallback: 'linear-gradient(135deg, #A8B5A0 0%, #586B52 100%)',
  },
  {
    name: 'Thar Desert',
    tagline: 'Great Indian Desert',
    desc: 'Endless golden dunes, camel trails, and star-filled desert nights.',
    img: desertImg,
    fallback: 'linear-gradient(135deg, #C9A96E 0%, #8A3D1E 100%)',
  },
];

const SUSTAIN_PILLARS = [
  {
    icon: Wind,
    colorClass: 'green',
    title: 'Carbon-Aware Transit',
    text: 'Route recommendations factor in transport-mode CO₂ emissions, favoring lower-carbon options like rail and bus over private vehicles.',
  },
  {
    icon: Users,
    colorClass: 'amber',
    title: 'Crowd Dispersion',
    text: 'District-level visitor density analysis distributes tourism demand beyond over-visited hotspots to underexplored destinations.',
  },
  {
    icon: Sun,
    colorClass: 'teal',
    title: 'Seasonal Awareness',
    text: 'Temporal visit patterns and seasonal suitability ratings ensure recommendations align with optimal travel windows.',
  },
  {
    icon: TreePine,
    colorClass: 'blue',
    title: 'Optimized Itineraries',
    text: 'Deep Q-Network routing with 2-Opt refinement minimizes total travel distance, reducing environmental impact per trip.',
  },
];

const STEPS = [
  {
    icon: Compass,
    title: 'Set Preferences',
    desc: 'Choose your origin city, interests, transport modes, and sustainability priorities.',
  },
  {
    icon: MapPin,
    title: 'Discover',
    desc: 'Receive Pareto-optimal destination recommendations ranked by a multi-criteria composite score.',
  },
  {
    icon: GitCompare,
    title: 'Compare',
    desc: 'Analyse how each algorithmic criterion (C1–C5) influences your results through ablation views.',
  },
  {
    icon: Route,
    title: 'Build Itinerary',
    desc: 'Generate a sequential, distance-optimized travel plan using deep reinforcement learning.',
  },
];

const FEATURES = [
  {
    icon: Compass,
    tab: 'recommendations',
    title: 'Smart Recommendations',
    desc: 'Multi-criteria composite scoring ranks destinations by interest match, sustainability, crowd levels, and accessibility.',
  },
  {
    icon: GitCompare,
    tab: 'comparison',
    title: 'Ablation Comparison',
    desc: 'Side-by-side C1 baseline vs. C5 full-model comparison reveals each criterion\'s contribution to final rankings.',
  },
  {
    icon: MapPin,
    tab: 'map',
    title: 'Interactive Map',
    desc: 'Geospatial visualization of recommendations, itinerary routes, and district-level attraction density across Rajasthan.',
  },
  {
    icon: Calendar,
    tab: 'itinerary',
    title: 'DRL Itinerary Planner',
    desc: 'Deep Q-Network with hard action-masking and 2-Opt local search produces optimized sequential travel routes.',
  },
  {
    icon: BarChart3,
    tab: 'research',
    title: 'Research Dashboard',
    desc: 'Empirical ablation metrics, RL training curves, benchmark comparisons, and model performance statistics.',
  },
  {
    icon: Users,
    tab: 'user-study',
    title: 'User Study Survey',
    desc: 'Double-blinded A/B Likert evaluation comparing the AuraTour system against a baseline interest-only recommender.',
  },
];

export default function LandingPage({ onEnterApp, setActiveTab }) {
  const [navScrolled, setNavScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const revealRefs = useRef([]);

  useEffect(() => {
    const handleScroll = () => {
      setNavScrolled(window.scrollY > 60);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Intersection Observer for scroll-reveal animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    const currentRefs = revealRefs.current;
    currentRefs.forEach((el) => {
      if (el) observer.observe(el);
    });

    return () => {
      currentRefs.forEach((el) => {
        if (el) observer.unobserve(el);
      });
    };
  }, []);

  const addRevealRef = (el) => {
    if (el && !revealRefs.current.includes(el)) {
      revealRefs.current.push(el);
    }
  };

  const scrollToSection = (sectionId) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setMobileMenuOpen(false);
    }
  };

  const handleEnterApp = (tab) => {
    if (tab) setActiveTab(tab);
    onEnterApp();
  };

  return (
    <div className="at-landing">
      {/* ========== NAVBAR ========== */}
      <nav className={`at-landing-nav ${navScrolled ? 'scrolled' : ''}`}>
        <div className="at-landing-nav-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="at-landing-nav-logo">
            <Mountain size={22} strokeWidth={2.2} />
          </div>
          <span className="at-landing-nav-title">AuraTour</span>
        </div>

        <button
          className="at-landing-nav-toggle"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          type="button"
          aria-label="Toggle navigation"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        <ul className={`at-landing-nav-links ${mobileMenuOpen ? 'mobile-open' : ''}`}>
          <li><a onClick={() => scrollToSection('destinations')}>Destinations</a></li>
          <li><a onClick={() => scrollToSection('sustainability')}>Sustainability</a></li>
          <li><a onClick={() => scrollToSection('how-it-works')}>How It Works</a></li>
          <li><a onClick={() => scrollToSection('features')}>Features</a></li>
          <li>
            <a className="at-landing-nav-cta" onClick={() => handleEnterApp('recommendations')}>
              Launch App
            </a>
          </li>
        </ul>
      </nav>

      {/* ========== HERO ========== */}
      <section className="at-hero">
        <div
          className="at-hero-bg"
          style={{
            backgroundImage: `url(${heroImg})`,
            backgroundColor: '#1F3A32',
          }}
        />
        <div className="at-hero-content">
          <div className="at-hero-label">
            <Leaf size={14} />
            Sustainable & Crowd-Aware Tourism
          </div>
          <h1 className="at-hero-heading">
            Discover <em>Rajasthan</em><br />
            Responsibly
          </h1>
          <p className="at-hero-sub">
            An intelligent tourism recommendation system that balances your travel
            interests with environmental sustainability, crowd distribution, and
            optimized itinerary planning across 18 districts of Rajasthan.
          </p>
          <div className="at-hero-actions">
            <button
              className="at-hero-btn-primary"
              onClick={() => handleEnterApp('recommendations')}
              type="button"
            >
              Explore Rajasthan
              <ArrowRight size={18} />
            </button>
            <button
              className="at-hero-btn-secondary"
              onClick={() => scrollToSection('sustainability')}
              type="button"
            >
              <Shield size={16} />
              Our Approach
            </button>
          </div>
        </div>
        <div className="at-hero-scroll-hint">
          <span>Scroll to explore</span>
          <ChevronDown size={18} />
        </div>
      </section>

      {/* ========== DESTINATION SHOWCASE ========== */}
      <section className="at-landing-section" id="destinations">
        <div ref={addRevealRef} className="at-reveal">
          <div className="at-landing-section-label">
            <MapPin size={13} />
            Explore Rajasthan
          </div>
          <h2 className="at-landing-section-title">
            Iconic Destinations, Intelligently Curated
          </h2>
          <p className="at-landing-section-desc">
            From the pink ramparts of Jaipur to the golden dunes of Thar, AuraTour
            covers 45+ verified points of interest across Rajasthan&apos;s most
            celebrated and underexplored destinations.
          </p>
        </div>

        <div ref={addRevealRef} className="at-reveal at-destinations-grid">
          {DESTINATIONS.map((dest) => (
            <div
              key={dest.name}
              className="at-destination-card"
              onClick={() => handleEnterApp('recommendations')}
            >
              <img
                className="at-destination-card-img"
                src={dest.img}
                alt={dest.name}
                loading="lazy"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentElement.style.background = dest.fallback;
                }}
              />
              <div className="at-destination-card-overlay">
                <div className="at-destination-card-badge">
                  <MapPin size={12} />
                  {dest.tagline}
                </div>
                <h3 className="at-destination-card-name">{dest.name}</h3>
                <p className="at-destination-card-desc">{dest.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ========== SUSTAINABILITY ========== */}
      <section className="at-sustainability-section" id="sustainability">
        <div className="at-sustainability-inner">
          <div ref={addRevealRef} className="at-reveal">
            <div className="at-landing-section-label">
              <Leaf size={13} />
              Responsible Travel
            </div>
            <h2 className="at-landing-section-title">
              Tourism That Respects the Land
            </h2>
            <p className="at-landing-section-desc">
              Every recommendation weighs environmental and social factors alongside
              your personal interests, producing a travel plan that is enjoyable
              and responsible.
            </p>
          </div>

          <div ref={addRevealRef} className="at-reveal at-sustain-grid">
            {SUSTAIN_PILLARS.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div key={pillar.title} className="at-sustain-card">
                  <div className={`at-sustain-card-icon ${pillar.colorClass}`}>
                    <Icon size={24} />
                  </div>
                  <h3 className="at-sustain-card-title">{pillar.title}</h3>
                  <p className="at-sustain-card-text">{pillar.text}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========== HOW IT WORKS ========== */}
      <section className="at-landing-section" id="how-it-works">
        <div ref={addRevealRef} className="at-reveal" style={{ textAlign: 'center' }}>
          <div className="at-landing-section-label" style={{ margin: '0 auto 16px' }}>
            <Route size={13} />
            How It Works
          </div>
          <h2 className="at-landing-section-title" style={{ margin: '0 auto 14px' }}>
            From Preferences to Itinerary
          </h2>
          <p className="at-landing-section-desc" style={{ margin: '0 auto' }}>
            Four steps to a personalized, sustainability-aware travel plan
            powered by multi-criteria optimization and deep reinforcement learning.
          </p>
        </div>

        <div ref={addRevealRef} className="at-reveal at-steps-track">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <div key={step.title} className="at-step-item">
                <div className="at-step-number">
                  <Icon size={28} color="var(--c-primary)" />
                </div>
                <h3 className="at-step-title">
                  <span style={{ color: 'var(--c-accent)', marginRight: 6 }}>0{i + 1}.</span>
                  {step.title}
                </h3>
                <p className="at-step-desc">{step.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ========== PLATFORM FEATURES ========== */}
      <section className="at-landing-section" id="features" style={{ background: 'var(--c-bg-subtle)', padding: '100px 48px', maxWidth: 'none' }}>
        <div style={{ maxWidth: 1320, margin: '0 auto' }}>
          <div ref={addRevealRef} className="at-reveal" style={{ textAlign: 'center' }}>
            <div className="at-landing-section-label" style={{ margin: '0 auto 16px' }}>
              <BarChart3 size={13} />
              Platform Capabilities
            </div>
            <h2 className="at-landing-section-title" style={{ margin: '0 auto 14px' }}>
              Six Integrated Research Modules
            </h2>
            <p className="at-landing-section-desc" style={{ margin: '0 auto' }}>
              Each module is built for academic rigor while remaining accessible
              to general users exploring Rajasthan tourism.
            </p>
          </div>

          <div ref={addRevealRef} className="at-reveal at-features-grid">
            {FEATURES.map((feat) => {
              const Icon = feat.icon;
              return (
                <div
                  key={feat.tab}
                  className="at-feature-card"
                  onClick={() => handleEnterApp(feat.tab)}
                >
                  <div className="at-feature-icon">
                    <Icon size={26} />
                  </div>
                  <h3 className="at-feature-title">{feat.title}</h3>
                  <p className="at-feature-desc">{feat.desc}</p>
                  <button
                    className="at-feature-link"
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEnterApp(feat.tab);
                    }}
                  >
                    Open Module <ChevronRight size={15} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========== FINAL CTA ========== */}
      <section className="at-cta-section">
        <div
          className="at-cta-bg"
          style={{
            backgroundImage: `url(${desertImg})`,
            backgroundColor: '#1F3A32',
          }}
        />
        <div ref={addRevealRef} className="at-reveal at-cta-content">
          <h2 className="at-cta-heading">
            Your Next Journey<br />Starts Here
          </h2>
          <p className="at-cta-sub">
            Explore Rajasthan through an intelligent lens that values sustainability,
            distributes tourism equitably, and builds optimized travel plans — all
            tailored to your unique preferences.
          </p>
          <button
            className="at-hero-btn-primary"
            onClick={() => handleEnterApp('recommendations')}
            type="button"
          >
            Start Exploring Rajasthan
            <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* ========== LANDING FOOTER ========== */}
      <footer className="at-landing-footer">
        <div className="at-landing-footer-inner">
          <div className="at-landing-footer-brand">
            <Mountain size={20} color="var(--c-accent)" />
            <span>AuraTour</span>
          </div>
          <p className="at-landing-footer-text">
            A multi-criteria sustainable tourism recommendation system for Rajasthan,
            India. Combining interest-category matching, carbon-aware transit modeling,
            crowd dispersion analysis, and deep reinforcement learning itinerary optimization.
          </p>
        </div>
        <div className="at-landing-footer-bottom">
          <span>AuraTour Research Prototype © {CURRENT_YEAR} • Academic Implementation</span>
          <span>1,225 Verified Rajasthan POIs • 18 Districts • Kaggle + OSM Data</span>
        </div>
      </footer>
    </div>
  );
}

