import React, { useState } from 'react';
import { Calendar, Clock, MapPin, Navigation, Leaf, Trash2, ArrowRight, ShieldCheck, AlertTriangle } from 'lucide-react';

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Configuration Header */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
          marginBottom: 20,
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: 16,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className={`badge ${isDrl ? 'badge-sapphire' : 'badge-emerald'}`}>
                {isDrl ? 'Deep RL Sequential Recommender' : 'Route Optimization Engine'}
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {isDrl ? 'Mode B Simulated DQN • Dalla Vecchia et al. (2024)' : 'Multi-Stop TSP & Carbon Accounting'}
              </span>
            </div>
            <h2 style={{ fontSize: '1.4rem', marginTop: 4 }}>
              {isDrl ? 'Deep RL Sustainability-Aware Itinerary' : 'Smart Carbon-Aware Travel Itinerary'}
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {isDrl
                ? 'Autonomous sequential recommendation agent that optimizes traveler interests, budget limits, daily time, and emissions.'
                : 'Sequences chosen destinations using nearest-neighbor heuristic with 2-opt swaps to minimize transit carbon and avoid backtracking.'}
            </p>
          </div>

          <button
            id="btn-build-itinerary"
            onClick={handleGenerate}
            disabled={loading || (!isDrl && selectedAttractionIds.length === 0)}
            className={isDrl ? "btn-primary" : "btn-primary"}
            style={{ opacity: loading || (!isDrl && selectedAttractionIds.length === 0) ? 0.6 : 1 }}
          >
            <Navigation size={16} />
            <span>
              {loading
                ? (isDrl ? 'Agent Planning Route...' : 'Optimizing Route...')
                : (isDrl ? (selectedAttractions.length === 0 ? 'Synthesize Itinerary via DRL' : 'Plan with DRL Agent') : 'Build 2-Opt Itinerary')}
            </span>
          </button>
        </div>

        {/* Selected Stops Chips */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Selected Destinations ({selectedAttractions.length} stops in bucket)
            </span>
            {selectedAttractions.length === 0 && (
              <span style={{ fontSize: '0.8rem', color: isDrl ? 'var(--sapphire-400)' : 'var(--amber-400)' }}>
                {isDrl
                  ? 'Tip: In DRL mode, the agent can autonomously select optimal stops from the entire Rajasthan catalog!'
                  : 'Select attractions from the Recommendations tab first!'}
              </span>
            )}
          </div>

          {selectedAttractions.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {selectedAttractions.map((att) => (
                <div
                  key={att.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid var(--border-subtle)',
                    padding: '6px 12px',
                    borderRadius: 20,
                    fontSize: '0.82rem',
                  }}
                >
                  <span>📍 {att.name} ({att.city})</span>
                  <button
                    type="button"
                    onClick={() => onRemoveFromItinerary(att.id)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <Trash2 size={13} hoverColor="var(--rose-400)" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Route Controls */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 16,
          background: 'rgba(11, 15, 23, 0.4)',
          padding: 16,
          borderRadius: 12,
        }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 6 }}>
              Planning Algorithm
            </label>
            <select
              className="select-control"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="drl">Deep RL Sequential Policy (Mode B DQN Agent)</option>
              <option value="2opt">Classical Greedy + 2-Opt TSP (Baseline)</option>
            </select>
          </div>

          {!isDrl && (
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 6 }}>
                Route Optimization Goal
              </label>
              <select
                className="select-control"
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
            <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 6 }}>
              Trip Days Target
            </label>
            <input
              type="number"
              min="1"
              max="14"
              className="input-control"
              value={tripDays}
              onChange={(e) => setTripDays(parseInt(e.target.value) || 1)}
            />
          </div>
        </div>
      </div>

      {/* Generated Itinerary Output */}
      {itinerary && (
        <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Carbon Savings Summary Card */}
          <div className="glass-panel" style={{
            padding: '20px 24px',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(5, 150, 105, 0.05))',
            border: '1px solid rgba(16, 185, 129, 0.35)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: 'var(--emerald-500)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 16px var(--emerald-glow)',
                }}>
                  <Leaf size={24} color="#ffffff" />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', color: '#ffffff' }}>
                    {itinerary.co2_savings_kg > 0
                      ? `${itinerary.co2_savings_kg} kg CO₂e Carbon Prevented!`
                      : 'Low Carbon Optimized Route'}
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: 'var(--emerald-400)' }}>
                    Compared to uncoordinated private car travel ({itinerary.baseline_car_emissions_kg} kg baseline)
                  </p>
                </div>
              </div>

              {/* Quick stats pills */}
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 14px', borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Total Distance</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
                    {itinerary.total_distance_km} km
                  </div>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 14px', borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Transit Hours</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--sapphire-400)' }}>
                    {itinerary.total_travel_hours} hrs
                  </div>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 14px', borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Planned Duration</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--amber-400)' }}>
                    {itinerary.total_days} Days
                  </div>
                </div>
                {itinerary.total_cost_inr !== undefined && (
                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 14px', borderRadius: 10, textAlign: 'center' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Estimated Cost</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#10b981' }}>
                      ₹{itinerary.total_cost_inr}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* DRL Budget and Provenance Header Banner */}
            {itinerary.strategy_used === 'drl' && (
              <div style={{
                marginTop: 14,
                padding: '10px 14px',
                borderRadius: 8,
                background: 'rgba(59, 130, 246, 0.08)',
                border: '1px solid rgba(59, 130, 246, 0.25)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 12,
                fontSize: '0.82rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="badge badge-sapphire" style={{ fontSize: '0.7rem' }}>
                    {itinerary.provenance_mode || 'Mode B (Simulator-Trained DQN)'}
                  </span>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    Budget Breakdown: Transit Fare <strong>₹{itinerary.total_fare_inr || 0}</strong> • Entry Fees <strong>₹{itinerary.total_entry_fees_inr || 0}</strong> • Remaining Budget <strong>₹{itinerary.remaining_budget_inr || 0}</strong>
                  </span>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Hard action-masking: 0% budget & time violations
                </span>
              </div>
            )}

            {/* Warnings if any */}
            {itinerary.warnings?.length > 0 && (
              <div style={{
                marginTop: 14,
                padding: '8px 12px',
                borderRadius: 8,
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: '0.8rem',
                color: 'var(--amber-400)',
              }}>
                <AlertTriangle size={15} />
                <span>{itinerary.warnings.join(' • ')}</span>
              </div>
            )}
          </div>

          {/* Day-by-Day Timeline */}
          <div className="glass-panel" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '1.15rem', marginBottom: 20 }}>
              Sequential Schedule & Journey Timeline
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {itinerary.stops?.map((stop, idx) => (
                <div
                  key={stop.order}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 16,
                    position: 'relative',
                  }}
                >
                  {/* Step indicator */}
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    minWidth: 40,
                  }}>
                    <div style={{
                      width: 36,
                      height: 36,
                      borderRadius: '50%',
                      background: 'rgba(16, 185, 129, 0.15)',
                      border: '2px solid var(--emerald-500)',
                      color: 'var(--emerald-400)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '0.85rem',
                    }}>
                      {stop.order}
                    </div>
                    {idx < itinerary.stops.length - 1 && (
                      <div style={{
                        width: 2,
                        height: 50,
                        background: 'rgba(255, 255, 255, 0.1)',
                        margin: '6px 0',
                      }} />
                    )}
                  </div>

                  {/* Stop Details Card */}
                  <div style={{
                    flex: 1,
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 12,
                    padding: '14px 18px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span className="badge badge-emerald" style={{ fontSize: '0.68rem' }}>
                            Day {stop.day}
                          </span>
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            Arrival: {stop.arrival_time} • Departure: {stop.departure_time}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '1.05rem', color: '#ffffff', marginTop: 4 }}>
                          {stop.attraction.name}
                        </h4>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                          {stop.attraction.city}, {stop.attraction.district} • Recommended visit: {stop.visit_duration_hours}h
                        </p>
                      </div>

                      {/* Leg Transit Stats */}
                      <div style={{
                        textAlign: 'right',
                        fontSize: '0.78rem',
                        color: 'var(--text-muted)',
                        background: 'rgba(0, 0, 0, 0.25)',
                        padding: '6px 12px',
                        borderRadius: 8,
                      }}>
                        <div>Transit Leg: {stop.travel_from_previous_km} km ({stop.transport_mode})</div>
                        <div style={{ color: 'var(--emerald-400)', fontWeight: 600 }}>
                          Leg CO₂e: {stop.leg_emissions_kg} kg
                        </div>
                        {stop.entry_fee_inr !== undefined && (
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>
                            Fare: ₹{stop.transit_fare_inr} • Entry: ₹{stop.entry_fee_inr}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Provenance Transparency Footer */}
            <div style={{
              marginTop: 24,
              padding: '12px 16px',
              borderRadius: 8,
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.76rem',
              color: 'var(--text-muted)',
            }}>
              <strong>Data Provenance Notice:</strong> Coordinates & attractions are <em>observed</em> (OpenStreetMap). Monument entry fees and durations are <em>sourced</em> (Ministry of Tourism / cleaned Kaggle dataset). Transit distances are <em>calculated</em> (Haversine × 1.30 detour heuristic). Emissions are <em>estimated</em> (WRI India emission factors). Route generation uses <em>{itinerary.strategy_used === 'drl' ? 'simulated' : 'heuristic'}</em> sequential planning.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
