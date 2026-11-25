import React from 'react';
import { Mountain, ShieldCheck, Database, Award } from 'lucide-react';

const CURRENT_YEAR = new Date().getFullYear();

export default function Footer() {
  return (
    <footer className="at-editorial-footer" style={{ position: 'relative' }}>
      {/* Decorative top gradient line */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: 3,
        background: 'linear-gradient(90deg, var(--c-accent), var(--c-primary), var(--c-sage))',
        borderRadius: '3px 3px 0 0',
      }} />

      <div className="at-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Mountain size={22} color="var(--c-accent)" />
          <span style={{ fontFamily: 'var(--font-serif)', fontSize: '1.35rem', color: 'var(--c-primary)' }}>
            AuraTour • Rajasthan Sustainable Recommendation System
          </span>
        </div>

        <p style={{ fontSize: '0.9rem', color: 'var(--c-text-secondary)', maxWidth: 740, lineHeight: 1.65 }}>
          Sequential multi-criteria decision engine optimizing tourism interest categories, 
          modal transit decarbonization, and regional crowd dispersion across 18 districts of Rajasthan, India.
        </p>

        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 18,
          justifyContent: 'center',
          fontSize: '0.84rem',
          color: 'var(--c-text-muted)',
          margin: '6px 0',
        }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <Database size={14} color="var(--c-primary)" />
            1,225 matched Rajasthan records (Kaggle & OSM)
          </span>
          <span>•</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <ShieldCheck size={14} color="var(--c-primary)" />
            Deep Q-Network with hard action-masking
          </span>
          <span>•</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <Award size={14} color="var(--c-accent)" />
            Inspired by Dalla Vecchia et al. (2024), <em>IT & Tourism</em>
          </span>
        </div>

        <div style={{
          fontSize: '0.8rem',
          color: 'var(--c-text-light)',
          borderTop: '1px solid var(--c-border-subtle)',
          paddingTop: 14,
          width: '100%',
        }}>
          AuraTour Research Prototype © {CURRENT_YEAR} • Academic Implementation • Verified Rajasthan POI Catalog
        </div>
      </div>
    </footer>
  );
}
