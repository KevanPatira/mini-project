import React, { useState, useEffect } from 'react';
import { 
  Users, Shield, CheckCircle2, AlertCircle, HelpCircle, ArrowRight, 
  Send, RefreshCw, BarChart2, Award, Sparkles, Compass, ThumbsUp
} from 'lucide-react';

export default function UserStudyView() {
  const [personaId, setPersonaId] = useState('P1');
  const [questionnaire, setQuestionnaire] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submissionSuccess, setSubmissionSuccess] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Participant Identity & Consent
  const [participantId, setParticipantId] = useState('');
  const [consentGiven, setConsentGiven] = useState(false);

  // Ratings (1 to 5 for each dimension)
  const [ratingsA, setRatingsA] = useState({
    relevance: 0,
    perceived_sustainability: 0,
    usefulness: 0,
    trust: 0,
    feasibility: 0,
    willingness_to_visit: 0,
  });

  const [ratingsB, setRatingsB] = useState({
    relevance: 0,
    perceived_sustainability: 0,
    usefulness: 0,
    trust: 0,
    feasibility: 0,
    willingness_to_visit: 0,
  });

  const [preferredSystem, setPreferredSystem] = useState('');
  const [qualitativeFeedback, setQualitativeFeedback] = useState('');

  // Study summary telemetry
  const [studySummary, setStudySummary] = useState(null);

  // Initialize or restore anonymous participant UUID from sessionStorage
  useEffect(() => {
    let storedId = sessionStorage.getItem('auratour_study_participant_id');
    if (!storedId) {
      storedId = 'anon_' + (crypto?.randomUUID ? crypto.randomUUID().slice(0, 12) : Math.random().toString(36).substring(2, 14));
      sessionStorage.setItem('auratour_study_participant_id', storedId);
    }
    setParticipantId(storedId);
    fetchSummary();
  }, []);

  // Fetch questionnaire whenever persona changes
  useEffect(() => {
    fetchQuestionnaire(personaId);
  }, [personaId]);

  const fetchQuestionnaire = async (pid) => {
    try {
      setLoading(true);
      setErrorMessage(null);
      setSubmissionSuccess(null);
      // Reset form ratings for new persona
      setRatingsA({ relevance: 0, perceived_sustainability: 0, usefulness: 0, trust: 0, feasibility: 0, willingness_to_visit: 0 });
      setRatingsB({ relevance: 0, perceived_sustainability: 0, usefulness: 0, trust: 0, feasibility: 0, willingness_to_visit: 0 });
      setPreferredSystem('');
      setQualitativeFeedback('');

      const res = await fetch(`/api/user-study/questionnaire?persona_id=${pid}`);
      if (!res.ok) {
        throw new Error(`Failed to load questionnaire: ${res.statusText}`);
      }
      const data = await res.json();
      setQuestionnaire(data);
    } catch (err) {
      console.error(err);
      setErrorMessage(err.message || 'Error fetching questionnaire.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch('/api/user-study/responses');
      if (res.ok) {
        const data = await res.json();
        setStudySummary(data);
      }
    } catch (err) {
      console.warn('Could not fetch study summary:', err);
    }
  };

  const handleRatingChange = (system, dimension, value) => {
    if (system === 'A') {
      setRatingsA(prev => ({ ...prev, [dimension]: value }));
    } else {
      setRatingsB(prev => ({ ...prev, [dimension]: value }));
    }
  };

  const isFormValid = () => {
    if (!consentGiven) return false;
    const dims = ['relevance', 'perceived_sustainability', 'usefulness', 'trust', 'feasibility', 'willingness_to_visit'];
    const validA = dims.every(d => ratingsA[d] >= 1 && ratingsA[d] <= 5);
    const validB = dims.every(d => ratingsB[d] >= 1 && ratingsB[d] <= 5);
    const validPref = ['System A', 'System B', 'No preference'].includes(preferredSystem);
    return validA && validB && validPref;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isFormValid()) {
      setErrorMessage('Please complete all 6 rating dimensions for both System A and System B, select your preferred system, and confirm consent.');
      return;
    }

    try {
      setSubmitting(true);
      setErrorMessage(null);

      const payload = {
        participant_id: participantId,
        persona_id: personaId,
        questionnaire_id: questionnaire.questionnaire_id,
        blinded_a_is: questionnaire.blinded_mapping['System A'],
        consent_given: consentGiven,
        ratings_system_a: ratingsA,
        ratings_system_b: ratingsB,
        preferred_system: preferredSystem,
        qualitative_feedback: qualitativeFeedback || null,
      };

      const res = await fetch('/api/user-study/responses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.status === 409) {
        throw new Error(`You have already submitted an evaluation for scenario ${personaId}. Thank you! You may select another persona above.`);
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Submission failed with status ${res.status}`);
      }

      const resData = await res.json();
      setSubmissionSuccess({
        submission_id: resData.submission_id,
        total_responses: resData.total_responses,
        persona: personaId,
      });

      // Refresh telemetry summary
      fetchSummary();
    } catch (err) {
      console.error(err);
      setErrorMessage(err.message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const personaList = [
    { id: 'P1', name: 'Solo Heritage Explorer', origin: 'Delhi', duration: '5 days' },
    { id: 'P2', name: 'Eco-Conscious Couple', origin: 'Mumbai', duration: '7 days' },
    { id: 'P3', name: 'Cultural Family Trip', origin: 'Delhi', duration: '4 days' },
    { id: 'P4', name: 'Budget Backpacker', origin: 'Bangalore', duration: '6 days' },
    { id: 'P5', name: 'Summer Hill Seeker', origin: 'Delhi', duration: '3 days' },
    { id: 'P6', name: 'Wildlife Enthusiast', origin: 'Mumbai', duration: '5 days' },
    { id: 'P7', name: 'Desert Adventurer', origin: 'Jaipur', duration: '4 days' },
  ];

  const ratingQuestions = questionnaire?.questions || [
    { key: 'relevance', text: 'Interest Relevance: Do these destinations match the stated interests?' },
    { key: 'perceived_sustainability', text: 'Perceived Sustainability: Does this itinerary appear environmentally and socially responsible?' },
    { key: 'usefulness', text: 'Practical Usefulness: Is this set of recommendations practical, appealing, and well-balanced?' },
    { key: 'trust', text: 'Trust & Credibility: Do the recommendations and accompanying travel details feel credible?' },
    { key: 'feasibility', text: 'Itinerary Feasibility: Is the geographic routing and travel time realistic for the duration?' },
    { key: 'willingness_to_visit', text: 'Willingness to Visit: Would the traveller be excited to actually follow this journey?' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28, maxWidth: 1280, margin: '0 auto', width: '100%' }}>
      {/* Header Banner */}
      <div className="glass-panel" style={{ padding: 28, position: 'relative', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute',
          top: -20,
          right: -20,
          width: 180,
          height: 180,
          background: 'radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, transparent 70%)',
          borderRadius: '50%',
          pointerEvents: 'none',
        }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--emerald-400)',
          }}>
            <Users size={24} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Empirical User Study Questionnaire</h2>
              <span className="badge badge-emerald">Double-Blinded Paired Comparison</span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
              Academic evaluation validating tourism recommendation quality, routing feasibility, and perceived sustainability.
            </p>
          </div>
        </div>

        {/* Protocol & Ethics Badges */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 12,
          marginTop: 18,
          paddingTop: 16,
          borderTop: '1px solid var(--border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            <Shield size={16} color="var(--emerald-400)" />
            <span><strong>Zero PII Collected:</strong> No names, emails, IPs, or cookies</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem', color: 'var(--sapphire-400)' }}>
            <Sparkles size={16} color="var(--sapphire-400)" />
            <span><strong>Target Cohort:</strong> 30–50 verified participants</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem', color: 'var(--amber-400)' }}>
            <Compass size={16} color="var(--amber-400)" />
            <span><strong>Token:</strong> <code>{participantId}</code></span>
          </div>
        </div>
      </div>

      {/* Informed Consent Box */}
      <div className="glass-panel" style={{
        padding: 20,
        background: consentGiven ? 'rgba(16, 185, 129, 0.05)' : 'rgba(59, 130, 246, 0.05)',
        border: `1px solid ${consentGiven ? 'rgba(16, 185, 129, 0.3)' : 'rgba(59, 130, 246, 0.25)'}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
          <div style={{ marginTop: 2 }}>
            <input
              type="checkbox"
              id="study-consent-checkbox"
              checked={consentGiven}
              onChange={(e) => setConsentGiven(e.target.checked)}
              style={{ width: 18, height: 18, cursor: 'pointer', accentColor: 'var(--emerald-500)' }}
            />
          </div>
          <div>
            <label htmlFor="study-consent-checkbox" style={{ fontWeight: 600, fontSize: '0.95rem', cursor: 'pointer', display: 'block', marginBottom: 4 }}>
              Informed Consent & Voluntary Participation Declaration
            </label>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              I agree to participate voluntarily in this anonymous academic research study on tourism recommender systems. I understand that my responses will be evaluated strictly in statistical aggregate, no personal identifying information is collected, and I may exit the questionnaire at any time.
            </p>
          </div>
        </div>
      </div>

      {/* Scenario / Persona Picker */}
      <div className="glass-panel" style={{ padding: 22 }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Compass size={18} color="var(--emerald-400)" />
          Step 1: Select Traveler Scenario to Evaluate
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>
          Each participant evaluates the two recommendation strategies for a specific traveler scenario. You may evaluate multiple scenarios by switching below.
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 10,
        }}>
          {personaList.map((p) => {
            const active = personaId === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setPersonaId(p.id)}
                className={`nav-tab ${active ? 'active' : ''}`}
                style={{
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  gap: 4,
                  borderRadius: 'var(--radius-md)',
                  textAlign: 'left',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{p.id}</span>
                  <span style={{ fontSize: '0.7rem', color: active ? 'var(--emerald-400)' : 'var(--text-muted)' }}>{p.origin}</span>
                </div>
                <div style={{ fontSize: '0.8rem', fontWeight: 500 }}>{p.name}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{p.duration}</div>
              </button>
            );
          })}
        </div>

        {/* Active Scenario Details */}
        {questionnaire && (
          <div style={{
            marginTop: 18,
            padding: 16,
            background: 'rgba(0, 0, 0, 0.25)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexWrap: 'wrap',
            gap: 20,
            fontSize: '0.85rem',
          }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Persona Profile: </span>
              <strong>{questionnaire.scenario.persona_name} ({questionnaire.scenario.persona_id})</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Starting City: </span>
              <strong>{questionnaire.scenario.origin.toUpperCase()}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Travel Month: </span>
              <strong>Month {questionnaire.scenario.travel_month} (Calendar)</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Trip Duration: </span>
              <strong>{questionnaire.scenario.duration_days} Days</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Stated Interests: </span>
              <span style={{ display: 'inline-flex', gap: 6, marginLeft: 6 }}>
                {questionnaire.scenario.interests.map(i => (
                  <span key={i} className="badge badge-sapphire" style={{ fontSize: '0.72rem', textTransform: 'capitalize' }}>
                    {i}
                  </span>
                ))}
              </span>
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>
          <RefreshCw className="spin" size={32} style={{ margin: '0 auto 12px' }} />
          <p>Generating blinded comparison itineraries...</p>
        </div>
      ) : questionnaire ? (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
          {/* Side-by-side Systems */}
          <div>
            <h3 style={{ fontSize: '1.15rem', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <BarChart2 size={18} color="var(--sapphire-400)" />
              Step 2: Inspect Recommended Itineraries (Double-Blinded)
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>
              Both systems use identical traveler inputs. One represents the standard recommendation algorithm and the other incorporates multi-criteria sustainability and crowding constraints.
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))',
              gap: 24,
            }}>
              {/* System A Panel */}
              <div className="glass-panel" style={{ padding: 22, borderTop: '3px solid var(--sapphire-500)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <h4 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--sapphire-400)' }}>
                    Itinerary Plan — System A
                  </h4>
                  <span className="badge badge-sapphire">5 Candidate Recommendations</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {questionnaire.system_a_items.map((item) => (
                    <div
                      key={item.rank}
                      style={{
                        padding: 12,
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                        <div style={{ fontWeight: 600, fontSize: '0.92rem' }}>
                          <span style={{ color: 'var(--sapphire-400)', marginRight: 6 }}>#{item.rank}</span>
                          {item.name}
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {item.city} ({item.district})
                        </span>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                        {item.categories.map((c) => (
                          <span key={c} style={{ fontSize: '0.68rem', padding: '2px 6px', background: 'rgba(255,255,255,0.05)', borderRadius: 4, color: 'var(--text-secondary)' }}>
                            {c}
                          </span>
                        ))}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span>Duration: {item.estimated_visit_duration_hours}h</span>
                        <span>Transport: {item.recommended_transport} ({item.travel_hours}h)</span>
                        <span>Transit CO₂: {item.estimated_emissions_kg} kg</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* System B Panel */}
              <div className="glass-panel" style={{ padding: 22, borderTop: '3px solid var(--emerald-500)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <h4 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--emerald-400)' }}>
                    Itinerary Plan — System B
                  </h4>
                  <span className="badge badge-emerald">5 Candidate Recommendations</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {questionnaire.system_b_items.map((item) => (
                    <div
                      key={item.rank}
                      style={{
                        padding: 12,
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                        <div style={{ fontWeight: 600, fontSize: '0.92rem' }}>
                          <span style={{ color: 'var(--emerald-400)', marginRight: 6 }}>#{item.rank}</span>
                          {item.name}
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {item.city} ({item.district})
                        </span>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                        {item.categories.map((c) => (
                          <span key={c} style={{ fontSize: '0.68rem', padding: '2px 6px', background: 'rgba(255,255,255,0.05)', borderRadius: 4, color: 'var(--text-secondary)' }}>
                            {c}
                          </span>
                        ))}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span>Duration: {item.estimated_visit_duration_hours}h</span>
                        <span>Transport: {item.recommended_transport} ({item.travel_hours}h)</span>
                        <span>Transit CO₂: {item.estimated_emissions_kg} kg</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Rating Matrix */}
          <div className="glass-panel" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '1.15rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Award size={18} color="var(--emerald-400)" />
              Step 3: Comparative 5-Point Likert Evaluation
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 20 }}>
              Rate both itineraries independently on each dimension (1 = Very Poor, 2 = Poor, 3 = Neutral, 4 = Good, 5 = Excellent).
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {ratingQuestions.map((q, idx) => (
                <div
                  key={q.key}
                  style={{
                    padding: 16,
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 12, color: 'var(--text-main)' }}>
                    {idx + 1}. {q.text}
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                    gap: 20,
                  }}>
                    {/* System A Rating */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(59, 130, 246, 0.05)', padding: '10px 14px', borderRadius: 8 }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--sapphire-400)' }}>System A</span>
                      <div style={{ display: 'flex', gap: 6 }}>
                        {[1, 2, 3, 4, 5].map((val) => (
                          <button
                            key={val}
                            type="button"
                            onClick={() => handleRatingChange('A', q.key, val)}
                            style={{
                              width: 32,
                              height: 32,
                              borderRadius: 6,
                              border: ratingsA[q.key] === val ? '2px solid var(--sapphire-400)' : '1px solid var(--border-subtle)',
                              background: ratingsA[q.key] === val ? 'var(--sapphire-500)' : 'rgba(255, 255, 255, 0.04)',
                              color: ratingsA[q.key] === val ? '#ffffff' : 'var(--text-secondary)',
                              fontWeight: 700,
                              cursor: 'pointer',
                              transition: 'all 0.15s ease',
                            }}
                          >
                            {val}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* System B Rating */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(16, 185, 129, 0.05)', padding: '10px 14px', borderRadius: 8 }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--emerald-400)' }}>System B</span>
                      <div style={{ display: 'flex', gap: 6 }}>
                        {[1, 2, 3, 4, 5].map((val) => (
                          <button
                            key={val}
                            type="button"
                            onClick={() => handleRatingChange('B', q.key, val)}
                            style={{
                              width: 32,
                              height: 32,
                              borderRadius: 6,
                              border: ratingsB[q.key] === val ? '2px solid var(--emerald-400)' : '1px solid var(--border-subtle)',
                              background: ratingsB[q.key] === val ? 'var(--emerald-500)' : 'rgba(255, 255, 255, 0.04)',
                              color: ratingsB[q.key] === val ? '#ffffff' : 'var(--text-secondary)',
                              fontWeight: 700,
                              cursor: 'pointer',
                              transition: 'all 0.15s ease',
                            }}
                          >
                            {val}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Forced-Choice & Qualitative Feedback */}
          <div className="glass-panel" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '1.15rem', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <ThumbsUp size={18} color="var(--amber-400)" />
              Step 4: Overall Preference & Comments
            </h3>

            {/* Overall Preference */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 600, marginBottom: 10 }}>
                Which itinerary would you personally recommend for this traveler?
              </label>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {['System A', 'System B', 'No preference'].map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setPreferredSystem(opt)}
                    className={`nav-tab ${preferredSystem === opt ? 'active' : ''}`}
                    style={{
                      padding: '10px 20px',
                      borderRadius: 8,
                      fontWeight: 600,
                      fontSize: '0.9rem',
                    }}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            {/* Qualitative Feedback */}
            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 600, marginBottom: 6 }}>
                Qualitative Feedback (Optional)
              </label>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 8 }}>
                What specific trade-offs or factors influenced your rating? (e.g. transit hours, attraction variety, carbon footprint)
              </p>
              <textarea
                value={qualitativeFeedback}
                onChange={(e) => setQualitativeFeedback(e.target.value)}
                maxLength={1000}
                rows={3}
                placeholder="Share your thoughts on the routing, pacing, or sustainability trade-offs..."
                style={{
                  width: '100%',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 8,
                  padding: 12,
                  color: 'var(--text-main)',
                  fontSize: '0.85rem',
                  resize: 'vertical',
                }}
              />
            </div>
          </div>

          {/* Feedback & Error Messages */}
          {errorMessage && (
            <div style={{
              padding: 14,
              borderRadius: 8,
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: 'var(--rose-400)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: '0.88rem',
            }}>
              <AlertCircle size={18} />
              <span>{errorMessage}</span>
            </div>
          )}

          {submissionSuccess && (
            <div style={{
              padding: 18,
              borderRadius: 8,
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid var(--emerald-500)',
              color: 'var(--text-main)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <CheckCircle2 size={20} color="var(--emerald-400)" />
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--emerald-400)' }}>
                  Thank you! Anonymous Evaluation Successfully Recorded.
                </h4>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                Submission Receipt ID: <code>{submissionSuccess.submission_id}</code> • Total verified study submissions to date: <strong>{submissionSuccess.total_responses}</strong>.
              </p>
            </div>
          )}

          {/* Submission Bar */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, alignItems: 'center' }}>
            {!consentGiven && (
              <span style={{ fontSize: '0.82rem', color: 'var(--amber-400)' }}>
                * Informed consent is required before submission.
              </span>
            )}
            <button
              type="submit"
              disabled={submitting || !consentGiven}
              className="btn-primary"
              style={{
                padding: '12px 28px',
                fontSize: '0.95rem',
                opacity: (!consentGiven || submitting) ? 0.6 : 1,
                cursor: (!consentGiven || submitting) ? 'not-allowed' : 'pointer',
              }}
            >
              {submitting ? (
                <>
                  <RefreshCw className="spin" size={16} />
                  <span>Submitting Securely...</span>
                </>
              ) : (
                <>
                  <Send size={16} />
                  <span>Submit Anonymous Evaluation</span>
                </>
              )}
            </button>
          </div>
        </form>
      ) : null}

      {/* Live Study Telemetry & Recruitment Progress */}
      <div className="glass-panel" style={{ padding: 24, marginTop: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <BarChart2 size={20} color="var(--emerald-400)" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>User Study Telemetry & Recruitment Status</h3>
          </div>
          <button
            onClick={fetchSummary}
            className="btn-secondary"
            style={{ fontSize: '0.78rem', padding: '6px 12px' }}
          >
            <RefreshCw size={14} />
            <span>Refresh Telemetry</span>
          </button>
        </div>

        {studySummary && studySummary.status === 'active' ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 20 }}>
              <div style={{ padding: 14, background: 'rgba(255, 255, 255, 0.02)', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Verified Participants</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--emerald-400)' }}>
                  {studySummary.total_participants}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Progress: {Math.round((studySummary.total_participants / 30) * 100)}% of N=30 target
                </div>
              </div>

              <div style={{ padding: 14, background: 'rgba(255, 255, 255, 0.02)', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Overall System Preference</div>
                <div style={{ fontSize: '0.85rem', marginTop: 6 }}>
                  <div>C5 Multi-Criteria: <strong>{studySummary.preference_distribution['C5_full']}</strong></div>
                  <div>C1 Baseline: <strong>{studySummary.preference_distribution['C1_baseline']}</strong></div>
                  <div>No Preference: <strong>{studySummary.preference_distribution['No preference']}</strong></div>
                </div>
              </div>
            </div>

            {/* Dimension Breakdown Table */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '8px 12px' }}>Evaluation Dimension</th>
                    <th style={{ padding: '8px 12px', color: 'var(--sapphire-400)' }}>C1 Baseline (Mean)</th>
                    <th style={{ padding: '8px 12px', color: 'var(--emerald-400)' }}>C5 Multi-Criteria (Mean)</th>
                    <th style={{ padding: '8px 12px' }}>Δ (C5 - C1)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.keys(studySummary.mean_ratings.C1_baseline).map((dim) => {
                    const c1 = studySummary.mean_ratings.C1_baseline[dim];
                    const c5 = studySummary.mean_ratings.C5_full[dim];
                    const diff = (c5 - c1).toFixed(2);
                    return (
                      <tr key={dim} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 500, textTransform: 'capitalize' }}>
                          {dim.replace(/_/g, ' ')}
                        </td>
                        <td style={{ padding: '10px 12px' }}>{c1} / 5.00</td>
                        <td style={{ padding: '10px 12px', fontWeight: 600 }}>{c5} / 5.00</td>
                        <td style={{ padding: '10px 12px', color: diff >= 0 ? 'var(--emerald-400)' : 'var(--rose-400)' }}>
                          {diff >= 0 ? `+${diff}` : diff}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.01)', borderRadius: 8 }}>
            <p style={{ marginBottom: 6, fontSize: '0.9rem' }}>
              Currently in participant intake phase ({studySummary?.total_participants || 0} participants recorded).
            </p>
            <p style={{ fontSize: '0.8rem' }}>
              Select a traveler scenario above and complete the questionnaire to contribute empirical evaluations to the study.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
