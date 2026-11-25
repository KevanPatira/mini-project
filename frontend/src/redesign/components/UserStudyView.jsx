import React, { useState, useEffect } from 'react';
import { 
  Users, Shield, CheckCircle2, AlertCircle, 
  Send, RefreshCw, BarChart2, Award, Sparkles, Compass, ThumbsUp, Layers 
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
      {/* Header Banner */}
      <div className="at-card" style={{ padding: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 18 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'var(--c-accent-soft)',
            color: 'var(--c-accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Users size={26} />
          </div>
          <div>
            <div className="at-page-tagline" style={{ marginBottom: 6 }}>
              <Shield size={13} color="var(--c-primary)" />
              <span>Double-Blinded Human Subject Evaluation</span>
            </div>
            <h2 style={{ fontSize: '2rem', color: 'var(--c-primary)' }}>
              Empirical User Study Questionnaire
            </h2>
            <p style={{ color: 'var(--c-text-secondary)', fontSize: '0.94rem', maxWidth: 760, lineHeight: 1.6 }}>
              Academic evaluation validating tourism recommendation quality, routing feasibility, and perceived environmental responsibility.
            </p>
          </div>
        </div>

        {/* Protocol & Ethics Badges */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 14,
          paddingTop: 18,
          borderTop: '1px solid var(--c-border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.84rem', color: 'var(--c-text-secondary)' }}>
            <Shield size={16} color="var(--c-primary)" />
            <span><strong>Zero PII Collected:</strong> No names, emails, IPs, or cookies</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.84rem', color: 'var(--c-text-secondary)' }}>
            <Sparkles size={16} color="var(--c-accent)" />
            <span><strong>Target Cohort:</strong> 30–50 verified participants</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.84rem', color: 'var(--c-text-secondary)' }}>
            <Compass size={16} color="var(--c-primary)" />
            <span><strong>Anonymous ID:</strong> <code>{participantId}</code></span>
          </div>
        </div>
      </div>

      {/* Informed Consent Declaration */}
      <div style={{
        padding: 24,
        borderRadius: 'var(--radius-lg)',
        backgroundColor: consentGiven ? 'var(--c-sage-soft)' : 'var(--c-bg-subtle)',
        border: `1.5px solid ${consentGiven ? 'var(--c-primary)' : 'var(--c-border)'}`,
        transition: 'all 0.2s ease',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
          <input
            type="checkbox"
            id="study-consent-checkbox"
            checked={consentGiven}
            onChange={(e) => setConsentGiven(e.target.checked)}
            style={{ width: 20, height: 20, cursor: 'pointer', marginTop: 3, accentColor: 'var(--c-primary)' }}
          />
          <div>
            <label htmlFor="study-consent-checkbox" style={{ fontWeight: 700, fontSize: '1rem', cursor: 'pointer', display: 'block', marginBottom: 4, color: 'var(--c-primary)' }}>
              Informed Consent & Voluntary Participation Declaration
            </label>
            <p style={{ fontSize: '0.86rem', color: 'var(--c-text-secondary)', lineHeight: 1.55 }}>
              I agree to participate voluntarily in this anonymous academic research study on tourism recommender systems. I understand that my responses will be evaluated strictly in statistical aggregate, no personal identifying information is collected, and I may exit the questionnaire at any time.
            </p>
          </div>
        </div>
      </div>

      {/* Step 1: Scenario Picker */}
      <div className="at-card" style={{ padding: 28 }}>
        <h3 style={{ fontSize: '1.25rem', color: 'var(--c-primary)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Compass size={18} color="var(--c-accent)" />
          Step 1: Select Traveler Scenario to Evaluate
        </h3>
        <p style={{ fontSize: '0.86rem', color: 'var(--c-text-muted)', marginBottom: 18 }}>
          Each participant evaluates two blinded recommendation strategies for a specific persona. You may evaluate multiple scenarios by switching below.
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: 12,
        }}>
          {personaList.map((p) => {
            const active = personaId === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setPersonaId(p.id)}
                className={`at-config-pill ${active ? 'active' : ''}`}
                style={{
                  padding: '14px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  gap: 3,
                  textAlign: 'left',
                  borderRadius: 'var(--radius-md)',
                }}
                type="button"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                  <span style={{ fontWeight: 800, fontSize: '0.96rem' }}>{p.id}</span>
                  <span style={{ fontSize: '0.74rem', opacity: 0.85 }}>{p.origin}</span>
                </div>
                <div style={{ fontSize: '0.84rem', fontWeight: 600 }}>{p.name}</div>
                <div style={{ fontSize: '0.74rem', opacity: 0.8 }}>{p.duration}</div>
              </button>
            );
          })}
        </div>

        {/* Scenario Details */}
        {questionnaire && (
          <div style={{
            marginTop: 20,
            padding: 18,
            backgroundColor: 'var(--c-bg-page)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--c-border)',
            display: 'flex',
            flexWrap: 'wrap',
            gap: 20,
            fontSize: '0.88rem',
          }}>
            <div>
              <span style={{ color: 'var(--c-text-muted)' }}>Profile: </span>
              <strong>{questionnaire.scenario.persona_name} ({questionnaire.scenario.persona_id})</strong>
            </div>
            <div>
              <span style={{ color: 'var(--c-text-muted)' }}>Gateway Origin: </span>
              <strong>{questionnaire.scenario.origin.toUpperCase()}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--c-text-muted)' }}>Travel Month: </span>
              <strong>Month {questionnaire.scenario.travel_month}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--c-text-muted)' }}>Trip Duration: </span>
              <strong>{questionnaire.scenario.duration_days} Days</strong>
            </div>
            <div>
              <span style={{ color: 'var(--c-text-muted)' }}>Stated Interests: </span>
              <span style={{ display: 'inline-flex', gap: 6, marginLeft: 6 }}>
                {questionnaire.scenario.interests.map(i => (
                  <span key={i} className="at-badge at-badge-accent" style={{ fontSize: '0.74rem', textTransform: 'capitalize' }}>
                    {i}
                  </span>
                ))}
              </span>
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--c-text-muted)' }}>
          <RefreshCw className="at-spin" size={34} style={{ margin: '0 auto 12px', color: 'var(--c-primary)' }} />
          <p>Generating blinded comparison itineraries...</p>
        </div>
      ) : questionnaire ? (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
          {/* Step 2: Side-by-Side Systems */}
          <div className="at-card" style={{ padding: 28 }}>
            <h3 style={{ fontSize: '1.35rem', color: 'var(--c-primary)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
              <BarChart2 size={18} color="var(--c-accent)" />
              Step 2: Inspect Recommended Itineraries (Double-Blinded)
            </h3>
            <p style={{ fontSize: '0.86rem', color: 'var(--c-text-muted)', marginBottom: 22 }}>
              Both systems use identical traveler inputs. One represents the baseline algorithm and the other incorporates multi-criteria sustainability and crowding constraints.
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: 24,
            }}>
              {/* System A Panel */}
              <div style={{
                backgroundColor: 'var(--c-bg-page)',
                border: '1px solid var(--c-border)',
                borderTop: '4px solid var(--c-accent)',
                borderRadius: 'var(--radius-lg)',
                padding: 20,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <h4 style={{ fontSize: '1.25rem', color: 'var(--c-accent)' }}>
                    Itinerary Plan — System A
                  </h4>
                  <span className="at-badge at-badge-accent">5 Recommendations</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {questionnaire.system_a_items.map((item) => (
                    <div
                      key={item.rank}
                      style={{
                        padding: 14,
                        backgroundColor: '#FFFFFF',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--c-border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                        <div style={{ fontWeight: 700, fontSize: '0.96rem', color: 'var(--c-primary)' }}>
                          <span style={{ color: 'var(--c-accent)', marginRight: 6 }}>#{item.rank}</span>
                          {item.name}
                        </div>
                        <span style={{ fontSize: '0.78rem', color: 'var(--c-text-muted)' }}>
                          {item.city} ({item.district})
                        </span>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 8 }}>
                        {item.categories.map((c) => (
                          <span key={c} className="at-badge at-badge-neutral" style={{ fontSize: '0.7rem', padding: '2px 8px', textTransform: 'capitalize' }}>
                            {c}
                          </span>
                        ))}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--c-text-secondary)' }}>
                        <span>Duration: {item.estimated_visit_duration_hours}h</span>
                        <span>Transit: {item.recommended_transport} ({item.travel_hours}h)</span>
                        <span style={{ color: 'var(--c-primary)', fontWeight: 700 }}>{item.estimated_emissions_kg} kg CO₂</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* System B Panel */}
              <div style={{
                backgroundColor: 'var(--c-bg-page)',
                border: '1px solid var(--c-border)',
                borderTop: '4px solid var(--c-primary)',
                borderRadius: 'var(--radius-lg)',
                padding: 20,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <h4 style={{ fontSize: '1.25rem', color: 'var(--c-primary)' }}>
                    Itinerary Plan — System B
                  </h4>
                  <span className="at-badge at-badge-sustain">5 Recommendations</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {questionnaire.system_b_items.map((item) => (
                    <div
                      key={item.rank}
                      style={{
                        padding: 14,
                        backgroundColor: '#FFFFFF',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--c-border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                        <div style={{ fontWeight: 700, fontSize: '0.96rem', color: 'var(--c-primary)' }}>
                          <span style={{ color: 'var(--c-primary)', marginRight: 6 }}>#{item.rank}</span>
                          {item.name}
                        </div>
                        <span style={{ fontSize: '0.78rem', color: 'var(--c-text-muted)' }}>
                          {item.city} ({item.district})
                        </span>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 8 }}>
                        {item.categories.map((c) => (
                          <span key={c} className="at-badge at-badge-neutral" style={{ fontSize: '0.7rem', padding: '2px 8px', textTransform: 'capitalize' }}>
                            {c}
                          </span>
                        ))}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--c-text-secondary)' }}>
                        <span>Duration: {item.estimated_visit_duration_hours}h</span>
                        <span>Transit: {item.recommended_transport} ({item.travel_hours}h)</span>
                        <span style={{ color: 'var(--c-primary)', fontWeight: 700 }}>{item.estimated_emissions_kg} kg CO₂</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Likert Rating Matrix */}
          <div className="at-card" style={{ padding: 28 }}>
            <h3 style={{ fontSize: '1.35rem', color: 'var(--c-primary)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Award size={18} color="var(--c-accent)" />
              Step 3: Comparative 5-Point Likert Evaluation
            </h3>
            <p style={{ fontSize: '0.86rem', color: 'var(--c-text-muted)', marginBottom: 22 }}>
              Rate both itineraries independently on each dimension (1 = Very Poor, 2 = Poor, 3 = Neutral, 4 = Good, 5 = Excellent).
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              {ratingQuestions.map((q, idx) => (
                <div
                  key={q.key}
                  style={{
                    padding: 18,
                    backgroundColor: 'var(--c-bg-page)',
                    borderRadius: 'var(--radius-lg)',
                    border: '1px solid var(--c-border)',
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '0.94rem', marginBottom: 14, color: 'var(--c-primary)' }}>
                    {idx + 1}. {q.text}
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))',
                    gap: 16,
                  }}>
                    {/* System A Rating */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#FFFFFF', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--c-border-subtle)' }}>
                      <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--c-accent)' }}>System A</span>
                      <div className="at-likert-container">
                        {[1, 2, 3, 4, 5].map((val) => (
                          <button
                            key={val}
                            type="button"
                            onClick={() => handleRatingChange('A', q.key, val)}
                            className={`at-likert-button ${ratingsA[q.key] === val ? 'active-a' : ''}`}
                          >
                            {val}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* System B Rating */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#FFFFFF', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--c-border-subtle)' }}>
                      <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--c-primary)' }}>System B</span>
                      <div className="at-likert-container">
                        {[1, 2, 3, 4, 5].map((val) => (
                          <button
                            key={val}
                            type="button"
                            onClick={() => handleRatingChange('B', q.key, val)}
                            className={`at-likert-button ${ratingsB[q.key] === val ? 'active-b' : ''}`}
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

          {/* Step 4: Overall Preference & Comments */}
          <div className="at-card" style={{ padding: 28 }}>
            <h3 style={{ fontSize: '1.35rem', color: 'var(--c-primary)', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <ThumbsUp size={18} color="var(--c-accent)" />
              Step 4: Overall Preference & Comments
            </h3>

            {/* Overall Preference */}
            <div style={{ marginBottom: 22 }}>
              <label style={{ display: 'block', fontSize: '0.94rem', fontWeight: 700, color: 'var(--c-primary)', marginBottom: 10 }}>
                Which itinerary would you personally recommend for this traveler?
              </label>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {['System A', 'System B', 'No preference'].map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setPreferredSystem(opt)}
                    className={`at-config-pill ${preferredSystem === opt ? 'active' : ''}`}
                    style={{ padding: '11px 24px', fontSize: '0.92rem' }}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            {/* Qualitative Feedback */}
            <div>
              <label style={{ display: 'block', fontSize: '0.94rem', fontWeight: 700, color: 'var(--c-primary)', marginBottom: 4 }}>
                Qualitative Feedback (Optional)
              </label>
              <p style={{ fontSize: '0.82rem', color: 'var(--c-text-muted)', marginBottom: 10 }}>
                What specific trade-offs or factors influenced your rating? (e.g. transit time, attraction variety, carbon footprint)
              </p>
              <textarea
                value={qualitativeFeedback}
                onChange={(e) => setQualitativeFeedback(e.target.value)}
                maxLength={1000}
                rows={3}
                placeholder="Share your thoughts on the routing, pacing, or sustainability trade-offs..."
                className="at-input"
                style={{ resize: 'vertical' }}
              />
            </div>
          </div>

          {/* Error Message Alert */}
          {errorMessage && (
            <div style={{
              padding: 16,
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--c-rose-soft)',
              border: '1.5px solid var(--c-rose)',
              color: 'var(--c-rose)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              fontSize: '0.92rem',
              fontWeight: 600,
            }}>
              <AlertCircle size={20} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Submission Success Banner */}
          {submissionSuccess && (
            <div style={{
              padding: 20,
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--c-sage-soft)',
              border: '1.5px solid var(--c-primary)',
              color: 'var(--c-primary)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <CheckCircle2 size={24} color="var(--c-primary)" />
                <h4 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--c-primary)' }}>
                  Thank you! Anonymous Evaluation Successfully Recorded.
                </h4>
              </div>
              <p style={{ fontSize: '0.88rem' }}>
                Receipt ID: <code>{submissionSuccess.submission_id}</code> • Total verified study submissions to date: <strong>{submissionSuccess.total_responses}</strong>.
              </p>
            </div>
          )}

          {/* Submission Bar */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 16, alignItems: 'center' }}>
            {!consentGiven && (
              <span style={{ fontSize: '0.86rem', color: 'var(--c-accent)', fontWeight: 600 }}>
                * Informed consent declaration is required before submission.
              </span>
            )}
            <button
              type="submit"
              disabled={submitting || !consentGiven}
              className="at-btn-primary"
              style={{ padding: '13px 32px', fontSize: '0.96rem' }}
            >
              {submitting ? (
                <>
                  <RefreshCw className="at-spin" size={17} />
                  <span>Submitting Securely...</span>
                </>
              ) : (
                <>
                  <Send size={17} />
                  <span>Submit Anonymous Evaluation</span>
                </>
              )}
            </button>
          </div>
        </form>
      ) : null}

      {/* Live Study Telemetry Card */}
      <div className="at-card" style={{ padding: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18, flexWrap: 'wrap', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <BarChart2 size={22} color="var(--c-primary)" />
            <h3 style={{ fontSize: '1.35rem', color: 'var(--c-primary)' }}>
              User Study Telemetry & Recruitment Status
            </h3>
          </div>
          <button
            onClick={fetchSummary}
            className="at-btn-secondary"
            style={{ fontSize: '0.82rem', padding: '7px 16px' }}
            type="button"
          >
            <RefreshCw size={14} />
            <span>Refresh Telemetry</span>
          </button>
        </div>

        {studySummary && studySummary.status === 'active' ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 16, marginBottom: 24 }}>
              <div style={{ padding: 16, backgroundColor: 'var(--c-bg-page)', borderRadius: 'var(--radius-md)', border: '1px solid var(--c-border-subtle)' }}>
                <div style={{ fontSize: '0.76rem', color: 'var(--c-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Verified Participants</div>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: '2rem', color: 'var(--c-primary)' }}>
                  {studySummary.total_participants}
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--c-text-muted)' }}>
                  Progress: {Math.round((studySummary.total_participants / 30) * 100)}% of N=30 target
                </div>
              </div>

              <div style={{ padding: 16, backgroundColor: 'var(--c-bg-page)', borderRadius: 'var(--radius-md)', border: '1px solid var(--c-border-subtle)' }}>
                <div style={{ fontSize: '0.76rem', color: 'var(--c-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Overall System Preference</div>
                <div style={{ fontSize: '0.88rem', marginTop: 8, lineHeight: 1.45 }}>
                  <div>C5 Multi-Criteria: <strong>{studySummary.preference_distribution['C5_full']}</strong></div>
                  <div>C1 Baseline: <strong>{studySummary.preference_distribution['C1_baseline']}</strong></div>
                  <div>No Preference: <strong>{studySummary.preference_distribution['No preference']}</strong></div>
                </div>
              </div>
            </div>

            {/* Dimension Breakdown Table */}
            <div className="at-table-container">
              <table className="at-table-editorial">
                <thead>
                  <tr>
                    <th>Evaluation Dimension</th>
                    <th>C1 Baseline (Mean)</th>
                    <th>C5 Multi-Criteria (Mean)</th>
                    <th>Difference (C5 - C1)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.keys(studySummary.mean_ratings.C1_baseline).map((dim) => {
                    const c1 = studySummary.mean_ratings.C1_baseline[dim];
                    const c5 = studySummary.mean_ratings.C5_full[dim];
                    const diff = (c5 - c1).toFixed(2);
                    return (
                      <tr key={dim}>
                        <td style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                          {dim.replace(/_/g, ' ')}
                        </td>
                        <td>{c1} / 5.00</td>
                        <td style={{ fontWeight: 700, color: 'var(--c-primary)' }}>{c5} / 5.00</td>
                        <td style={{ color: diff >= 0 ? 'var(--c-primary)' : 'var(--c-rose)', fontWeight: 700 }}>
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
          <div style={{ padding: 26, textAlign: 'center', color: 'var(--c-text-muted)', backgroundColor: 'var(--c-bg-page)', borderRadius: 'var(--radius-md)' }}>
            <p style={{ marginBottom: 6, fontSize: '0.94rem' }}>
              Currently in participant intake phase ({studySummary?.total_participants || 0} participants recorded).
            </p>
            <p style={{ fontSize: '0.84rem' }}>
              Select a traveler scenario above and submit a questionnaire to contribute empirical evaluations to the study.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
