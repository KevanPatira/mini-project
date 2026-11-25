import React, { useState } from 'react';
import { 
  Clock, MapPin, Navigation, Leaf, Trash2, 
  AlertTriangle, Train, Bus, Car, Plane, Wallet, ShieldCheck, Sparkles, Calendar 
} from 'lucide-react';

export default function ItineraryView({
  selectedAttractionIds,
  onRemoveFromItinerary,
  onGenerateItinerary,
  itinerary,
  loading,
  allAttractions,
  preferences,
}) {
  const [strategy, setStrategy] = useState('drl');
  const [optimizeFor, setOptimizeFor] = useState('balanced');
  const [tripDays, setTripDays] = useState(preferences?.trip_duration_days || 4);

  const selectedAttractions = selectedAttractionIds
    .map((id) => allAttractions.find((a) => a.id === id))
    .filter(Boolean);

  const handleGenerate = () => {
    onGenerateItinerary({
      optimize_for: optimizeFor,
      trip_duration_days: tripDays,
      strategy: strategy,
    });
  };

  const isDrl = strategy === 'drl';

  const getTransportIcon = (mode) => {
    if (!mode) return Navigation;
    const m = mode.toLowerCase();
    if (m.includes('train') || m.includes('rail')) return Train;
    if (m.includes('bus')) return Bus;
    if (m.includes('car')) return Car;
    if (m.includes('flight') || m.includes('plane')) return Plane;
    return Navigation;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Configuration Header Card */}
      <div className="at-card" style={{ padding: 32 }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 20,
          marginBottom: 24,
          borderBottom: '1px solid var(--c-border-subtle)',
          paddingBottom: 20,
        }}>
          <div>
            <div className="at-page-tagline" style={{ marginBottom: 8 }}>
              <Calendar size={13} color="var(--c-accent)" />
              <span>Sequential Optimization Studio</span>
            </div>
            <h2 style={{ fontSize: '1.95rem', color: 'var(--c-primary)' }}>
              {isDrl ? 'Deep RL Sustainability-Aware Itinerary' : 'Smart Carbon-Aware Travel Itinerary'}
            </h2>
            <p style={{ fontSize: '0.92rem', color: 'var(--c-text-secondary)', maxWidth: 740, lineHeight: 1.6 }}>
              {isDrl
                ? 'Autonomous sequential recommendation policy optimizing traveler utility, strict daily time limits, and budget ceilings without constraint violations.'
                : 'Sequences user-selected destinations to minimize deadhead travel, eliminate route backtracking, and curb transit carbon.'}
            </p>
          </div>

          <button
            id="btn-build-itinerary"
            onClick={handleGenerate}
            disabled={loading || (!isDrl && selectedAttractionIds.length === 0)}
            className="at-btn-primary"
            type="button"
            style={{ padding: '13px 26px', fontSize: '0.94rem' }}
          >
            <Navigation size={17} />
            <span>
              {loading
                ? (isDrl ? 'Agent Synthesizing Route...' : 'Optimizing Route...')
                : (isDrl 
                    ? (selectedAttractions.length === 0 ? 'Synthesize Itinerary via DRL' : 'Plan with DRL Agent') 
                    : 'Build 2-Opt Itinerary')}
            </span>
          </button>
        </div>

        {/* Selected Stops Bucket */}
        <div style={{ marginBottom: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--c-primary)' }}>
              Selected Destination Bucket ({selectedAttractions.length} destinations ready to sequence)
            </span>
            {selectedAttractions.length === 0 && (
              <span style={{ fontSize: '0.82rem', color: isDrl ? 'var(--c-primary)' : 'var(--c-amber)', fontWeight: 600 }}>
                {isDrl
                  ? 'Tip: In DRL mode, the agent can autonomously discover optimal attractions across all Rajasthan districts!'
                  : 'Select attractions from the Recommendations tab first.'}
              </span>
            )}
          </div>

          {selectedAttractions.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {selectedAttractions.map((att) => (
                <div
                  key={att.id}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    backgroundColor: 'var(--c-bg-page)',
                    border: '1.5px solid var(--c-border)',
                    padding: '7px 14px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.84rem',
                    color: 'var(--c-primary)',
                    fontWeight: 600,
                  }}
                >
                  <MapPin size={14} color="var(--c-accent)" />
                  <span>{att.name} ({att.city})</span>
                  <button
                    type="button"
                    onClick={() => onRemoveFromItinerary(att.id)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--c-text-muted)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      padding: 2,
                    }}
                    title="Remove stop"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Controls Row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
          gap: 18,
          backgroundColor: 'var(--c-bg-page)',
          border: '1px solid var(--c-border)',
          padding: 18,
          borderRadius: 'var(--radius-lg)',
        }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--c-primary)', marginBottom: 6 }}>
              Planning Algorithm
            </label>
            <select
              className="at-select"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="drl">Deep RL Policy (Mode B DQN Agent)</option>
              <option value="2opt">Classical Greedy + 2-Opt TSP (Heuristic)</option>
            </select>
          </div>

          {!isDrl && (
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--c-primary)', marginBottom: 6 }}>
                Optimization Goal
              </label>
              <select
                className="at-select"
                value={optimizeFor}
                onChange={(e) => setOptimizeFor(e.target.value)}
              >
                <option value="balanced">Balanced (Travel Time & Emissions)</option>
                <option value="time">Fastest Travel Time</option>
                <option value="emissions">Lowest Carbon Footprint</option>
              </select>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--c-primary)', marginBottom: 6 }}>
              Target Trip Duration
            </label>
            <input
              type="number"
              min="1"
              max="14"
              className="at-input"
              value={tripDays}
              onChange={(e) => setTripDays(parseInt(e.target.value) || 1)}
            />
          </div>
        </div>
      </div>

      {/* Generated Itinerary Output */}
      {itinerary && (
        <div className="at-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 26 }}>
          {/* Carbon Savings Summary Card */}
          <div className="at-card" style={{ padding: 28, borderLeft: '6px solid var(--c-primary)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 18 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{
                  width: 52,
                  height: 52,
                  borderRadius: 'var(--radius-lg)',
                  backgroundColor: 'var(--c-sage-soft)',
                  color: 'var(--c-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <Leaf size={26} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.45rem', color: 'var(--c-primary)' }}>
                    {itinerary.co2_savings_kg > 0
                      ? `${itinerary.co2_savings_kg} kg CO₂e Carbon Prevented!`
                      : 'Low Carbon Optimized Route'}
                  </h3>
                  <p style={{ fontSize: '0.84rem', color: 'var(--c-secondary)', fontWeight: 600 }}>
                    Compared to uncoordinated private car travel ({itinerary.baseline_car_emissions_kg} kg baseline)
                  </p>
                </div>
              </div>

              {/* Metric Tiles */}
              <div className="at-metric-cards-strip" style={{ margin: 0 }}>
                <div className="at-metric-tile-card" style={{ borderTop: '3px solid var(--c-primary)' }}>
                  <div className="at-metric-tile-title">Total Distance</div>
                  <div className="at-metric-tile-number">{itinerary.total_distance_km} km</div>
                </div>
                <div className="at-metric-tile-card" style={{ borderTop: '3px solid var(--c-accent)' }}>
                  <div className="at-metric-tile-title">Transit Hours</div>
                  <div className="at-metric-tile-number">{itinerary.total_travel_hours}h</div>
                </div>
                <div className="at-metric-tile-card" style={{ borderTop: '3px solid var(--c-sage)' }}>
                  <div className="at-metric-tile-title">Duration</div>
                  <div className="at-metric-tile-number">{itinerary.total_days} Days</div>
                </div>
                {itinerary.total_cost_inr !== undefined && (
                  <div className="at-metric-tile-card" style={{ borderTop: '3px solid var(--c-gold)' }}>
                    <div className="at-metric-tile-title">Estimated Cost</div>
                    <div className="at-metric-tile-number" style={{ color: 'var(--c-accent)' }}>
                      ₹{itinerary.total_cost_inr}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* DRL Budget and Action-Masking Stats */}
            {itinerary.strategy_used === 'drl' && (
              <div style={{
                marginTop: 20,
                padding: '14px 18px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--c-bg-page)',
                border: '1px solid var(--c-border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 12,
                fontSize: '0.84rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span className="at-badge at-badge-sustain">
                    {itinerary.provenance_mode || 'Mode B (Simulator-Trained DQN)'}
                  </span>
                  <span style={{ color: 'var(--c-text-primary)' }}>
                    Transit Fare: <strong>₹{itinerary.total_fare_inr || 0}</strong> • Monument Fees: <strong>₹{itinerary.total_entry_fees_inr || 0}</strong> • Remaining Budget: <strong>₹{itinerary.remaining_budget_inr || 0}</strong>
                  </span>
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--c-primary)', fontWeight: 700 }}>
                  ✓ Hard action-masking: 0% budget & time limit violations
                </span>
              </div>
            )}

            {/* Warnings callout */}
            {itinerary.warnings?.length > 0 && (
              <div style={{
                marginTop: 16,
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--c-amber-soft)',
                border: '1px solid var(--c-amber)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                fontSize: '0.84rem',
                color: 'var(--c-amber)',
              }}>
                <AlertTriangle size={16} />
                <span>{itinerary.warnings.join(' • ')}</span>
              </div>
            )}
          </div>

          {/* Sequential Timeline Card */}
          <div className="at-card" style={{ padding: 32 }}>
            <h3 style={{ fontSize: '1.4rem', color: 'var(--c-primary)', marginBottom: 20 }}>
              Sequential Daily Journey Timeline
            </h3>

            <div className="at-timeline-stream">
              {itinerary.stops?.map((stop, idx) => {
                const TransportIcon = getTransportIcon(stop.transport_mode);
                const isLast = idx === itinerary.stops.length - 1;
                return (
                  <div key={stop.order} className="at-timeline-item">
                    {/* Gutter with Step Circle and Spine Line */}
                    <div className="at-timeline-gutter">
                      <div className="at-timeline-badge">
                        {stop.order}
                      </div>
                      {!isLast && (
                        <div
                          className="at-timeline-spine"
                          style={{
                            background: 'linear-gradient(to bottom, var(--c-accent), var(--c-primary))',
                            transition: 'opacity 400ms ease',
                          }}
                        />
                      )}
                    </div>

                    {/* Timeline Card */}
                    <div className="at-timeline-card">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 14 }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                            <span className="at-badge at-badge-accent">
                              Day {stop.day}
                            </span>
                            <span style={{ fontSize: '0.82rem', color: 'var(--c-text-muted)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                              <Clock size={13} />
                              Arrival: {stop.arrival_time} • Departure: {stop.departure_time}
                            </span>
                          </div>
                          <h4 style={{ fontSize: '1.25rem', color: 'var(--c-primary)', margin: '4px 0 2px' }}>
                            {stop.attraction.name}
                          </h4>
                          <p style={{ fontSize: '0.84rem', color: 'var(--c-text-secondary)' }}>
                            {stop.attraction.city}, {stop.attraction.district} District • Visit Duration: {stop.visit_duration_hours}h
                          </p>
                        </div>

                        {/* Leg Transit Details */}
                        <div style={{
                          textAlign: 'right',
                          fontSize: '0.82rem',
                          color: 'var(--c-text-secondary)',
                          backgroundColor: 'var(--c-bg-subtle)',
                          padding: '10px 16px',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--c-border-subtle)',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end', fontWeight: 600 }}>
                            <TransportIcon size={15} color="var(--c-accent)" />
                            <span>{stop.travel_from_previous_km} km via {stop.transport_mode}</span>
                          </div>
                          <div style={{ color: 'var(--c-primary)', fontWeight: 700, marginTop: 2 }}>
                            Leg CO₂e: {stop.leg_emissions_kg} kg
                          </div>
                          {stop.entry_fee_inr !== undefined && (
                            <div style={{ fontSize: '0.74rem', color: 'var(--c-text-muted)', marginTop: 2 }}>
                              Transit Fare: ₹{stop.transit_fare_inr} • Entry Fee: ₹{stop.entry_fee_inr}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Provenance Notice */}
            <div style={{
              marginTop: 32,
              padding: '16px 20px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--c-bg-page)',
              border: '1px solid var(--c-border)',
              fontSize: '0.8rem',
              color: 'var(--c-text-muted)',
              lineHeight: 1.55,
            }}>
              <strong>Data Provenance Notice:</strong> Coordinates & attractions are <em>observed</em> (OpenStreetMap). Monument entry fees and durations are <em>sourced</em> (Ministry of Tourism / cleaned Kaggle dataset). Transit distances are <em>calculated</em> (Haversine × 1.30 detour heuristic). Emissions are <em>estimated</em> (WRI India emission factors). Route generation uses <em>{itinerary.strategy_used === 'drl' ? 'Mode B Simulated Deep Q-Network' : 'Heuristic 2-Opt TSP'}</em> sequential planning.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
