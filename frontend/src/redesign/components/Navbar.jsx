import React from 'react';
import { 
  Compass, GitCompare, MapPin, Calendar, BarChart3, Users, 
  Mountain, Sparkles, X, ChevronRight, Globe, Shield, Home 
} from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  backendStatus,
  totalAttractions,
  onToggleLegacy,
  isRedesignActive,
  mobileOpen,
  setMobileOpen,
  onGoHome,
}) {
  const tabs = [
    { id: 'recommendations', label: 'Recommendations', desc: 'Destination Discovery', icon: Compass },
    { id: 'comparison', label: 'C1 vs C5 Compare', desc: 'Ablation Analysis', icon: GitCompare },
    { id: 'map', label: 'Interactive Map', desc: 'Spatial Exploration', icon: MapPin },
    { id: 'itinerary', label: 'Smart Itinerary', desc: 'Sequential Route', icon: Calendar },
    { id: 'research', label: 'Research & Metrics', desc: 'Empirical Benchmark', icon: BarChart3 },
    { id: 'user-study', label: 'User Study Survey', desc: 'Academic Evaluation', icon: Users },
  ];

  const isOnline = backendStatus === 'online';

  const handleTabClick = (tabId) => {
    setActiveTab(tabId);
    if (setMobileOpen) setMobileOpen(false);
  };

  const sidebarLinkStyle = {
    transition: 'transform 200ms ease, background-color 200ms ease',
  };

  const sidebarLinkHoverHandlers = (isActive) => ({
    onMouseEnter: (e) => {
      if (!isActive) e.currentTarget.style.transform = 'translateX(2px)';
    },
    onMouseLeave: (e) => {
      e.currentTarget.style.transform = 'translateX(0)';
    },
  });

  return (
    <aside className={`at-sidebar ${mobileOpen ? 'open' : ''}`}>
      <div className="at-sidebar-top">
        {/* Brand Header */}
        <div className="at-sidebar-brand" onClick={() => onGoHome ? onGoHome() : handleTabClick('recommendations')}>
          <div className="at-sidebar-logo-icon">
            <Mountain size={24} strokeWidth={2.2} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className="at-sidebar-brand-name">AuraTour</span>
            </div>
            <p className="at-sidebar-brand-sub">
              Sustainable Tourism • Rajasthan
            </p>
          </div>

          {setMobileOpen && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setMobileOpen(false);
              }}
              style={{
                marginLeft: 'auto',
                background: 'transparent',
                border: 'none',
                color: '#fff',
                cursor: 'pointer',
                display: mobileOpen ? 'block' : 'none',
              }}
              type="button"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Decorative Home Link */}
        {onGoHome && (
          <button
            onClick={onGoHome}
            type="button"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              width: '100%',
              padding: '9px 16px',
              margin: '0 0 4px 0',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--c-text-inverse-muted)',
              fontSize: '0.78rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'background 200ms ease, color 200ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
              e.currentTarget.style.color = '#fff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
              e.currentTarget.style.color = 'var(--c-text-inverse-muted)';
            }}
          >
            <Home size={14} strokeWidth={2} />
            <span>Back to Home</span>
          </button>
        )}

        {/* Section Label */}
        <div className="at-sidebar-nav-label">
          Navigation Studio
        </div>

        {/* Navigation Items */}
        <nav className="at-sidebar-menu" aria-label="Primary Navigation">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`nav-tab-${tab.id}`}
                onClick={() => handleTabClick(tab.id)}
                className={`at-sidebar-link ${isActive ? 'active' : ''}`}
                type="button"
                style={sidebarLinkStyle}
                {...sidebarLinkHoverHandlers(isActive)}
              >
                <Icon size={18} strokeWidth={isActive ? 2.4 : 1.8} color={isActive ? 'var(--c-accent)' : 'currentColor'} />
                <div style={{ flex: 1 }}>
                  <div>{tab.label}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--c-text-muted)', fontWeight: 400 }}>
                    {tab.desc}
                  </div>
                </div>
                {isActive && (
                  <ChevronRight size={14} color="var(--c-accent)" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Sidebar Bottom / Health & Version Toggle */}
      <div className="at-sidebar-bottom">
        {/* Divider line before bottom section */}
        <div style={{
          height: 1,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
          marginBottom: 16,
        }} />

        <div className="at-sidebar-status-box">
          <span className={`at-beacon-dot ${isOnline ? 'online' : 'offline'}`} />
          <span style={{ fontWeight: 600 }}>
            {isOnline ? `FastAPI Live (${totalAttractions || 45} POIs)` : 'API Offline'}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="at-badge at-badge-sustain" style={{ fontSize: '0.64rem', padding: '2px 8px' }}>
            Research Edition
          </span>

          {onToggleLegacy && (
            <button
              onClick={onToggleLegacy}
              className="at-sidebar-toggle-btn"
              title="Switch to original classic UI"
              type="button"
            >
              {isRedesignActive ? 'Classic View' : 'Redesign View'}
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
