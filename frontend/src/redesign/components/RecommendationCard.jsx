import React from 'react';
import { 
  Plus, Check, MapPin, Clock, Award, Leaf, Sparkles, Navigation, 
  ShieldCheck 
} from 'lucide-react';

export default function RecommendationCard({
  item,
  onAddToItinerary,
  isInItinerary,
  rank,
}) {
  const { attraction, final_score, score_breakdown, explanation } = item;
  const emissionsKg = item.estimated_emissions_kg;
  const distanceKm = item.distance_km;
  const travelHours = item.travel_hours;
  const transportMode = item.transport_mode;

  const scorePercent = Math.round(final_score * 100);
  const isTopPick = rank <= 3;

  return (
    <div
      className="at-discovery-card at-fade-in"
      style={{ position: 'relative', overflow: 'hidden' }}
      onMouseEnter={(e) => {
        const stripe = e.currentTarget.querySelector('.at-card-accent-stripe');
        if (stripe) stripe.style.opacity = '1';
      }}
      onMouseLeave={(e) => {
        const stripe = e.currentTarget.querySelector('.at-card-accent-stripe');
        if (stripe) stripe.style.opacity = '0';
      }}
    >
      {/* Subtle left-side accent stripe on hover */}
      <div
        className="at-card-accent-stripe"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 4,
          height: '100%',
          background: 'linear-gradient(to bottom, var(--c-primary), var(--c-accent))',
          opacity: 0,
          transition: 'opacity 240ms ease',
          zIndex: 2,
          borderRadius: '4px 0 0 4px',
        }}
      />

      {/* Visual Decorative Cover */}
      <div className="at-card-cover">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className={`at-card-rank-badge ${isTopPick ? 'top-pick' : ''}`}>
            {isTopPick ? `★ Rank #${rank}` : `Rank #${rank}`}
          </span>
          <span className="at-badge at-badge-neutral" style={{ fontSize: '0.72rem' }}>
            {attraction.district} District
          </span>
        </div>

        <div
          className="at-composite-score-badge"
          title="Multi-Criteria Composite Utility Index"
          style={{ transition: 'transform 200ms ease' }}
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.08)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          <Sparkles size={13} color="var(--c-accent)" />
          <span>{scorePercent}% Match</span>
        </div>
      </div>

      {/* Main Card Body */}
      <div className="at-card-content">
        {/* Title and Location */}
        <div>
          <h3 className="at-card-title">{attraction.name}</h3>
          <div className="at-card-location">
            <MapPin size={14} color="var(--c-accent)" />
            <span>{attraction.city}, Rajasthan</span>
          </div>
        </div>

        {/* Heritage Status & Categories */}
        <div className="at-card-tag-row">
          {attraction.heritage_status && (
            <span className="at-badge at-badge-amber">
              <Award size={12} />
              <span>{attraction.heritage_status}</span>
            </span>
          )}
          {attraction.categories?.map((cat) => (
            <span key={cat} className="at-badge at-badge-neutral" style={{ textTransform: 'capitalize' }}>
              {cat}
            </span>
          ))}
          {attraction.visitor_data_source === 'observed' && (
            <span className="at-badge at-badge-sustain">
              <ShieldCheck size={12} />
              <span>Verified ASI Site</span>
            </span>
          )}
        </div>

        {/* Description */}
        <p className="at-card-desc">
          {attraction.description}
        </p>

        {/* Multi-Criteria Balanced Meters */}
        <div className="at-criteria-box">
          <div className="at-criteria-label-row">
            Multi-Criteria Performance Dimensions
          </div>

          <div className="at-criteria-grid">
            {/* Interest Alignment */}
            <div>
              <div className="at-meter-header">
                <span>Interest Match</span>
                <strong style={{ color: 'var(--c-accent)' }}>
                  {(score_breakdown.preference_score * 100).toFixed(0)}%
                </strong>
              </div>
              <div className="at-meter-track">
                <div 
                  className="at-meter-fill" 
                  style={{ width: `${score_breakdown.preference_score * 100}%`, backgroundColor: 'var(--c-accent)' }} 
                />
              </div>
            </div>

            {/* Low Carbon */}
            <div>
              <div className="at-meter-header">
                <span>Low Carbon Transit</span>
                <strong style={{ color: 'var(--c-primary)' }}>
                  {(score_breakdown.emission_score * 100).toFixed(0)}%
                </strong>
              </div>
              <div className="at-meter-track">
                <div 
                  className="at-meter-fill" 
                  style={{ width: `${score_breakdown.emission_score * 100}%`, backgroundColor: 'var(--c-primary)' }} 
                />
              </div>
            </div>

            {/* Crowd Dispersion */}
            <div>
              <div className="at-meter-header">
                <span>Crowd Dispersion</span>
                <strong style={{ color: 'var(--c-secondary)' }}>
                  {(score_breakdown.popularity_score * 100).toFixed(0)}%
                </strong>
              </div>
              <div className="at-meter-track">
                <div 
                  className="at-meter-fill" 
                  style={{ width: `${score_breakdown.popularity_score * 100}%`, backgroundColor: 'var(--c-secondary)' }} 
                />
              </div>
            </div>

            {/* Seasonal Suitability */}
            <div>
              <div className="at-meter-header">
                <span>Seasonal Balance</span>
                <strong style={{ color: 'var(--c-sage-dark)' }}>
                  {(score_breakdown.seasonality_score * 100).toFixed(0)}%
                </strong>
              </div>
              <div className="at-meter-track">
                <div 
                  className="at-meter-fill" 
                  style={{ width: `${score_breakdown.seasonality_score * 100}%`, backgroundColor: 'var(--c-sage)' }} 
                />
              </div>
            </div>
          </div>
        </div>

        {/* Transit Distance & CO2 Summary */}
        {distanceKm !== undefined && (
          <div className="at-transit-strip">
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <Navigation size={14} color="var(--c-accent)" />
              {Math.round(distanceKm)} km via {transportMode || 'optimal route'}
            </span>
            {travelHours && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <Clock size={13} />
                ~{travelHours.toFixed(1)} hrs
              </span>
            )}
            {emissionsKg !== undefined && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: 'var(--c-primary)', fontWeight: 700 }}>
                <Leaf size={13} />
                {emissionsKg} kg CO₂e
              </span>
            )}
          </div>
        )}

        {/* Editorial Why Note */}
        <div className="at-editorial-quote">
          <strong>Curator's Note:</strong> {explanation}
        </div>
      </div>

      {/* Card Action Footer */}
      <div className="at-card-bottom-actions" style={{ padding: '16px 24px', backgroundColor: 'var(--c-bg-page)' }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--c-text-muted)' }}>
          {attraction.estimated_visit_duration_hours ? `Duration: ${attraction.estimated_visit_duration_hours}h` : 'Full-day site'}
          {attraction.entry_fee ? ` • Fee: ${attraction.entry_fee.split(',')[0]}` : ''}
        </div>

        <button
          id={`btn-add-itinerary-${attraction.id}`}
          type="button"
          onClick={() => onAddToItinerary(attraction.id)}
          className={isInItinerary ? 'at-btn-secondary' : 'at-btn-primary'}
          style={{
            padding: '8px 18px',
            fontSize: '0.84rem',
            ...(isInItinerary ? {
              backgroundColor: 'var(--c-sage-soft)',
              borderColor: 'var(--c-primary)',
              color: 'var(--c-primary)',
              fontWeight: 700,
            } : {})
          }}
        >
          {isInItinerary ? (
            <>
              <Check size={15} />
              <span>In Itinerary</span>
            </>
          ) : (
            <>
              <Plus size={15} />
              <span>Add to Route</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
