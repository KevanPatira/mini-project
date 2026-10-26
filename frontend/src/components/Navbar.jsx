import React from 'react';
import { Compass, GitCompare, MapPin, Calendar, BarChart3, Users, Leaf, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, backendStatus, totalAttractions }) {
  const tabs = [
    { id: 'recommendations', label: 'Recommendations', icon: Compass },
    { id: 'comparison', label: 'C1 vs C5 Compare', icon: GitCompare },
    { id: 'map', label: 'Interactive Map', icon: MapPin },
    { id: 'itinerary', label: 'Smart Itinerary', icon: Calendar },
    { id: 'research', label: 'Research & Metrics', icon: BarChart3 },
    { id: 'user-study', label: 'User Study Survey', icon: Users },
  ];

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      background: 'rgba(11, 15, 23, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '12px 24px',
    }}>
      <div style={{
        maxWidth: 1400,
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16,
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: 'linear-gradient(135deg, var(--emerald-500), #065f46)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px var(--emerald-glow)',
          }}>
            <Leaf size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.35rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                background: 'linear-gradient(to right, #ffffff, #a7f3d0)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                AuraTour
              </span>
              <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>Research Edition</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Sustainable & Crowd-Aware Tourism Recommender • Rajasthan
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'rgba(255, 255, 255, 0.03)',
          padding: 4,
          borderRadius: 14,
          border: '1px solid var(--border-subtle)',
          overflowX: 'auto',
          maxWidth: '100%',
        }}>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`nav-tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-tab ${isActive ? 'active' : ''}`}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Backend Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: backendStatus === 'online' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${backendStatus === 'online' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            padding: '5px 12px',
            borderRadius: 20,
            fontSize: '0.78rem',
            color: backendStatus === 'online' ? 'var(--emerald-400)' : 'var(--rose-400)',
          }}>
            <span style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              backgroundColor: backendStatus === 'online' ? 'var(--emerald-400)' : 'var(--rose-400)',
              boxShadow: backendStatus === 'online' ? '0 0 8px var(--emerald-400)' : 'none',
            }} />
            <span>{backendStatus === 'online' ? `FastAPI Live (${totalAttractions} POIs)` : 'API Offline'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
