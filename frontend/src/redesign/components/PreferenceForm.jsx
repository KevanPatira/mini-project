import React from 'react';
import { 
  Sliders, Train, Car, Plane, Bus, Sparkles, MapPin, Calendar, 
  Leaf, Landmark, Castle, Trees, Bird, Palette, Sun, Compass, Utensils, 
  ShoppingBag, Feather, RefreshCw 
} from 'lucide-react';

const CATEGORY_ICONS = {
  history: Landmark,
  architecture: Castle,
  nature: Trees,
  wildlife: Bird,
  culture: Palette,
  religion: Sun,
  adventure: Compass,
  food: Utensils,
  shopping: ShoppingBag,
  relaxation: Feather,
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

  const getPriorityExplanation = (val) => {
    if (val === 0) return 'Baseline Profile: Ranks strictly by your interest categories with zero carbon or crowd penalties.';
    if (val < 0.35) return 'Low Sustainability Focus: Preference-weighted with minimal distance penalty.';
    if (val < 0.7) return 'Balanced Multi-Criteria: Standard Pareto compromise between personal interest, transport emissions, and site crowding.';
    if (val < 0.9) return 'High Sustainability Focus: Heavily prioritizes lower carbon transit and off-peak dispersion.';
    return 'Maximum Eco-Priority: Strong modal shift toward electric rail transit and off-the-beaten-path heritage sites.';
  };

  const getSeasonBadge = (month) => {
    if ([11, 12, 1, 2].includes(month)) {
      return { text: 'Peak Winter Season (Pleasant desert weather, higher tourist volume)', class: 'at-badge-amber' };
    }
    if ([3, 9, 10].includes(month)) {
      return { text: 'Moderate Shoulder Season (Balanced climate & steady visitor traffic)', class: 'at-badge-sustain' };
    }
    return { text: 'Off-Peak Summer (Low crowd congestion, warm temperatures)', class: 'at-badge-neutral' };
  };

  const seasonInfo = getSeasonBadge(preferences.travel_month);

  const transportOptions = [
    { id: null, label: 'Optimal Route', icon: null, badge: 'Any mode' },
    { id: 'train', label: 'Indian Railways', icon: Train, badge: '17g CO₂' },
    { id: 'bus', label: 'State Bus', icon: Bus, badge: '40g CO₂' },
    { id: 'car', label: 'Private Car', icon: Car, badge: '150g CO₂' },
    { id: 'flight', label: 'Domestic Air', icon: Plane, badge: '130g CO₂' },
  ];

  const stepBadgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 32,
    height: 32,
    borderRadius: 'var(--radius-sm)',
    backgroundColor: 'var(--c-accent-soft)',
    color: 'var(--c-accent)',
    fontFamily: 'var(--font-serif)',
    fontSize: '0.85rem',
    fontWeight: 700,
    flexShrink: 0,
  };

  return (
    <div className="at-studio-panel">
      {/* Studio Header & Main CTA */}
      <div className="at-studio-header">
        <div>
          <div className="at-page-tagline">
            <Sparkles size={14} color="var(--c-accent)" />
            <span>Interactive Travel Recommender Studio</span>
          </div>
          <h2 style={{ fontSize: '1.85rem', color: 'var(--c-primary)', marginBottom: 4 }}>
            Tailor Your Rajasthan Itinerary
          </h2>
          <p style={{ fontSize: '0.92rem', color: 'var(--c-text-secondary)', maxWidth: 650 }}>
            Configure your gateway origin, travel timing, modal carbon priority, and cultural interests to generate Pareto-optimal recommendations.
          </p>
        </div>
      </div>

      {/* Main Configuration Grid */}
      <div className="at-studio-grid">
        {/* Column 1: Travel Logistics */}
        <div className="at-studio-card">
          <div className="at-studio-card-title">
            <div style={stepBadgeStyle}>01</div>
            <MapPin size={16} color="var(--c-accent)" />
            <span>Travel Logistics & Timing</span>
          </div>

          {/* Starting Origin */}
          <div className="at-form-field">
            <label className="at-form-label" htmlFor="select-origin-city">
              <span>Departure Gateway Origin</span>
            </label>
            <select
              id="select-origin-city"
              className="at-select"
              value={preferences.origin_city}
              onChange={(e) => setPreferences({ ...preferences, origin_city: e.target.value })}
            >
              {Object.entries(origins).map(([key, info]) => (
                <option key={key} value={key}>
                  {info.name} ({info.lat.toFixed(2)}°N, {info.lon.toFixed(2)}°E)
                </option>
              ))}
            </select>
          </div>

          {/* Travel Month */}
          <div className="at-form-field">
            <div className="at-form-label">
              <span>Calendar Month of Visit</span>
              <strong style={{ color: 'var(--c-primary)', fontSize: '0.94rem' }}>
                {MONTH_NAMES[preferences.travel_month - 1]}
              </strong>
            </div>
            <input
              id="slider-travel-month"
              type="range"
              min="1"
              max="12"
              step="1"
              className="at-slider"
              value={preferences.travel_month}
              onChange={(e) => setPreferences({ ...preferences, travel_month: parseInt(e.target.value) })}
            />
            <div style={{ marginTop: 8 }}>
              <span className={`at-badge ${seasonInfo.class}`} style={{ fontSize: '0.72rem' }}>
                {seasonInfo.text}
              </span>
            </div>
          </div>
        </div>

        {/* Column 2: Sustainability Weight & Transit */}
        <div className="at-studio-card">
          <div className="at-studio-card-title">
            <div style={stepBadgeStyle}>02</div>
            <Leaf size={16} color="var(--c-primary)" />
            <span>Sustainability Weight & Transit</span>
          </div>

          {/* Sustainability Priority Slider */}
          <div className="at-form-field">
            <div className="at-form-label">
              <span>Sustainability Weight (λ)</span>
              <span className="at-badge at-badge-sustain" style={{ fontSize: '0.8rem', fontWeight: 800 }}>
                {(preferences.sustainability_priority * 100).toFixed(0)}%
              </span>
            </div>
            <input
              id="slider-sustainability-priority"
              type="range"
              min="0"
              max="1"
              step="0.05"
              className="at-slider"
              value={preferences.sustainability_priority}
              onChange={(e) => setPreferences({ ...preferences, sustainability_priority: parseFloat(e.target.value) })}
            />
            <p style={{ fontSize: '0.78rem', color: 'var(--c-text-secondary)', marginTop: 8, lineHeight: 1.45 }}>
              {getPriorityExplanation(preferences.sustainability_priority)}
            </p>
          </div>

          {/* Transit Modal Preference */}
          <div className="at-form-field" style={{ marginTop: 14 }}>
            <label className="at-form-label">
              <span>Modal Carbon Footprint Preference</span>
            </label>
            <div className="at-transport-modes">
              {transportOptions.map((mode) => {
                const isSelected = preferences.preferred_transport === mode.id;
                const Icon = mode.icon;
                return (
                  <button
                    key={mode.label}
                    id={`btn-transport-${mode.id || 'any'}`}
                    type="button"
                    onClick={() => setPreferences({ ...preferences, preferred_transport: mode.id })}
                    className={`at-mode-chip ${isSelected ? 'active' : ''}`}
                  >
                    {Icon && <Icon size={14} />}
                    <span>{mode.label}</span>
                    <span style={{ fontSize: '0.68rem', opacity: isSelected ? 0.9 : 0.6, marginLeft: 2 }}>
                      ({mode.badge})
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Travel Interests Chips */}
      <div className="at-interest-area">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={stepBadgeStyle}>03</div>
            <div>
              <h4 style={{ fontSize: '1.05rem', color: 'var(--c-primary)' }}>
                Traveler Interest Categories
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--c-text-secondary)' }}>
                Select all cultural and landscape themes you would like the recommendation model to prioritize.
              </p>
            </div>
          </div>
          <span className="at-badge at-badge-neutral">
            {preferences.interests.length} selected
          </span>
        </div>

        <div className="at-interest-chips">
          {categories.map((cat) => {
            const isSelected = preferences.interests.includes(cat);
            const Icon = CATEGORY_ICONS[cat] || Compass;
            return (
              <button
                key={cat}
                id={`chip-interest-${cat}`}
                type="button"
                onClick={() => toggleInterest(cat)}
                className={`at-interest-chip ${isSelected ? 'active' : ''}`}
              >
                <Icon size={15} color={isSelected ? 'var(--c-accent)' : 'var(--c-text-muted)'} />
                <span style={{ textTransform: 'capitalize' }}>{cat}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Centered Submit Button Area */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        paddingTop: 24,
        paddingBottom: 8,
        borderTop: '1px solid var(--c-border-subtle)',
        marginTop: 8,
      }}>
        <button
          id="btn-run-recommendation"
          onClick={onRecommend}
          disabled={loading}
          className="at-btn-primary"
          type="button"
          style={{ padding: '14px 40px', fontSize: '1rem', minWidth: 240 }}
        >
          {loading ? (
            <>
              <RefreshCw size={18} className="at-spin" />
              <span>Evaluating Model...</span>
            </>
          ) : (
            <>
              <Sparkles size={18} />
              <span>Generate Recommendations</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
