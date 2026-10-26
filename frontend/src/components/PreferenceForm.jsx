import React from 'react';
import { Sliders, Train, Car, Plane, Bus, Sparkles, MapPin, Calendar, Wallet } from 'lucide-react';

const CATEGORY_ICONS = {
  history: '🏛️',
  architecture: '🏰',
  nature: '🌿',
  wildlife: '🐅',
  culture: '🎨',
  religion: '🕉️',
  adventure: '🧗',
  food: '🍲',
  shopping: '🛍️',
  relaxation: '🧘',
};

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export default function PreferenceForm({
  preferences,
  setPreferences,
  origins,
  categories,
  onRecommend,
  loading,
}) {
  const toggleInterest = (categoryKey) => {
    const current = [...preferences.interests];
    const index = current.indexOf(categoryKey);
    if (index > -1) {
      if (current.length > 1) {
        current.splice(index, 1);
      }
    } else {
      current.push(categoryKey);
    }
    setPreferences({ ...preferences, interests: current });
  };

  const getPriorityLabel = (val) => {
    if (val === 0) return 'C1 Baseline (Preferences Only)';
    if (val < 0.35) return 'Low Sustainability Weight';
    if (val < 0.7) return 'Balanced Multi-Criteria (Standard)';
    if (val < 0.9) return 'High Carbon & Crowd Reduction';
    return 'Max Eco-Priority (Off-Peak & Low Carbon)';
  };

  const getSeasonBadge = (month) => {
    if ([11, 12, 1, 2].includes(month)) {
      return { text: 'Peak Season (Pleasant weather, higher crowds)', class: 'badge-amber' };
    }
    if ([3, 9, 10].includes(month)) {
      return { text: 'Moderate Shoulder Season (Balanced)', class: 'badge-emerald' };
    }
    return { text: 'Off-Peak / Summer (Low crowds, hot climate)', class: 'badge-purple' };
  };

  const seasonInfo = getSeasonBadge(preferences.travel_month);

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: 24 }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 20,
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34,
            height: 34,
            borderRadius: 8,
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--emerald-400)',
          }}>
            <Sliders size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.15rem' }}>Traveller Preferences & Sustainability Controls</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Tune trade-offs between your travel interests and sustainability indicators
            </p>
          </div>
        </div>

        <button
          id="btn-run-recommendation"
          onClick={onRecommend}
          disabled={loading}
          className="btn-primary"
          style={{ opacity: loading ? 0.7 : 1 }}
        >
          <Sparkles size={16} />
          <span>{loading ? 'Evaluating Model...' : 'Generate Recommendations'}</span>
        </button>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 20,
      }}>
        {/* Origin City */}
        <div>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: '0.85rem',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            marginBottom: 8,
          }}>
            <MapPin size={15} color="var(--sapphire-400)" />
            Starting Origin City
          </label>
          <select
            id="select-origin-city"
            className="select-control"
            value={preferences.origin_city}
            onChange={(e) => setPreferences({ ...preferences, origin_city: e.target.value })}
          >
            {Object.entries(origins).map(([key, info]) => (
              <option key={key} value={key} style={{ background: '#121826' }}>
                {info.name} ({info.lat.toFixed(2)}°N, {info.lon.toFixed(2)}°E)
              </option>
            ))}
          </select>
        </div>

        {/* Travel Month */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: '0.85rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
            }}>
              <Calendar size={15} color="var(--amber-400)" />
              Travel Month
            </label>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--emerald-400)' }}>
              {MONTH_NAMES[preferences.travel_month - 1]}
            </span>
          </div>
          <input
            id="slider-travel-month"
            type="range"
            min="1"
            max="12"
            step="1"
            className="range-slider"
            value={preferences.travel_month}
            onChange={(e) => setPreferences({ ...preferences, travel_month: parseInt(e.target.value) })}
          />
          <div style={{ marginTop: 8 }}>
            <span className={`badge ${seasonInfo.class}`} style={{ fontSize: '0.7rem' }}>
              {seasonInfo.text}
            </span>
          </div>
        </div>

        {/* Sustainability Priority Slider */}
        <div style={{ gridColumn: 'span 1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: '0.85rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
            }}>
              <span style={{ color: 'var(--emerald-400)' }}>λ</span> Sustainability Priority:
            </label>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--emerald-400)' }}>
              {(preferences.sustainability_priority * 100).toFixed(0)}%
            </span>
          </div>
          <input
            id="slider-sustainability-priority"
            type="range"
            min="0"
            max="1"
            step="0.05"
            className="range-slider"
            value={preferences.sustainability_priority}
            onChange={(e) => setPreferences({ ...preferences, sustainability_priority: parseFloat(e.target.value) })}
          />
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>
            {getPriorityLabel(preferences.sustainability_priority)}
          </p>
        </div>

        {/* Preferred Transport Mode */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.85rem',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            marginBottom: 8,
          }}>
            Transport Preference (Emissions Factor)
          </label>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {[
              { id: null, label: 'Optimal / Any', icon: null },
              { id: 'train', label: 'Train (17g)', icon: Train },
              { id: 'bus', label: 'Bus (40g)', icon: Bus },
              { id: 'car', label: 'Car (150g)', icon: Car },
              { id: 'flight', label: 'Flight (130g)', icon: Plane },
            ].map((mode) => {
              const isSelected = preferences.preferred_transport === mode.id;
              const Icon = mode.icon;
              return (
                <button
                  key={mode.label}
                  id={`btn-transport-${mode.id || 'any'}`}
                  type="button"
                  onClick={() => setPreferences({ ...preferences, preferred_transport: mode.id })}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 8,
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                    border: isSelected ? '1px solid var(--emerald-500)' : '1px solid var(--border-subtle)',
                    background: isSelected ? 'rgba(16, 185, 129, 0.18)' : 'rgba(255, 255, 255, 0.04)',
                    color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {Icon && <Icon size={13} />}
                  <span>{mode.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Category Selection Chips */}
      <div style={{ marginTop: 22, paddingTop: 18, borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Interest Categories ({preferences.interests.length} selected)
          </label>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Click tags to toggle your preferences
          </span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {categories.map((cat) => {
            const isSelected = preferences.interests.includes(cat);
            return (
              <button
                key={cat}
                id={`chip-interest-${cat}`}
                type="button"
                onClick={() => toggleInterest(cat)}
                style={{
                  padding: '7px 14px',
                  borderRadius: 20,
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  border: isSelected
                    ? '1px solid rgba(16, 185, 129, 0.5)'
                    : '1px solid var(--border-subtle)',
                  background: isSelected
                    ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(5, 150, 105, 0.25))'
                    : 'rgba(255, 255, 255, 0.03)',
                  color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  boxShadow: isSelected ? '0 2px 10px rgba(16, 185, 129, 0.2)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                <span>{CATEGORY_ICONS[cat] || '📍'}</span>
                <span style={{ textTransform: 'capitalize' }}>{cat}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
