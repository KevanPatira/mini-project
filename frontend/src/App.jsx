import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import PreferenceForm from './components/PreferenceForm';
import RecommendationCard from './components/RecommendationCard';
import ComparisonView from './components/ComparisonView';
import MapView from './components/MapView';
import ItineraryView from './components/ItineraryView';
import ResearchDashboard from './components/ResearchDashboard';
import UserStudyView from './components/UserStudyView';
import { Compass, Sparkles, MapPin, Calendar, GitCompare, ArrowRight } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('recommendations');
  const [backendStatus, setBackendStatus] = useState('checking');
  const [totalAttractions, setTotalAttractions] = useState(0);

  // Preference state
  const [preferences, setPreferences] = useState({
    interests: ['history', 'architecture', 'culture'],
    origin_city: 'delhi',
    travel_month: 11,
    trip_duration_days: 5,
    budget_level: 'medium',
    preferred_transport: null,
    sustainability_priority: 0.5,
  });

  // Metadata
  const [origins, setOrigins] = useState({
    delhi: { name: 'New Delhi', lat: 28.61, lon: 77.21 },
    mumbai: { name: 'Mumbai', lat: 19.08, lon: 72.88 },
    bangalore: { name: 'Bangalore', lat: 12.97, lon: 77.59 },
    jaipur: { name: 'Jaipur', lat: 26.91, lon: 75.79 },
  });
  const [categories, setCategories] = useState([
    'history', 'architecture', 'nature', 'wildlife', 'culture',
    'religion', 'adventure', 'food', 'shopping', 'relaxation'
  ]);

  // Data state
  const [allDestinations, setAllDestinations] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [comparisons, setComparisons] = useState({});
  const [selectedAttractionIds, setSelectedAttractionIds] = useState(['raj_001', 'raj_002', 'raj_003', 'raj_004']);
  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [itineraryLoading, setItineraryLoading] = useState(false);

  // Initial load
  useEffect(() => {
    checkHealthAndLoadMeta();
  }, []);

  const checkHealthAndLoadMeta = async () => {
    try {
      const healthRes = await fetch('/api/health');
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setBackendStatus('online');
        setTotalAttractions(healthData.total_attractions || 45);
      } else {
        setBackendStatus('offline');
      }

      const [catRes, origRes, destRes] = await Promise.all([
        fetch('/api/meta/categories'),
        fetch('/api/meta/origins'),
        fetch('/api/destinations'),
      ]);

      if (catRes.ok) {
        const catData = await catRes.json();
        if (catData.categories) setCategories(catData.categories);
      }

      if (origRes.ok) {
        const origData = await origRes.json();
        if (origData.origins) setOrigins(origData.origins);
      }

      if (destRes.ok) {
        const destData = await destRes.json();
        if (destData.destinations) setAllDestinations(destData.destinations);
      }

      // Run initial recommendations and comparisons
      runRecommendation();
      runComparison();
    } catch (err) {
      console.warn('Backend not responding yet:', err);
      setBackendStatus('offline');
    }
  };

  const runRecommendation = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences),
      });
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations || []);
      }
    } catch (err) {
      console.error('Failed to get recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const runComparison = async () => {
    try {
      const res = await fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferences,
          configurations: [
            { preference_score: 1.0 },
            { preference_score: 0.5, emission_score: 0.5 },
            { preference_score: 0.4, emission_score: 0.3, popularity_score: 0.3 },
            { preference_score: 0.3, emission_score: 0.3, popularity_score: 0.2, seasonality_score: 0.2 },
            { preference_score: 0.25, emission_score: 0.25, popularity_score: 0.2, seasonality_score: 0.15, feasibility_score: 0.15 },
          ],
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setComparisons(data.comparisons || {});
      }
    } catch (err) {
      console.error('Failed to compare configurations:', err);
    }
  };

  const handleRecommendClick = () => {
    runRecommendation();
    runComparison();
  };

  const handleToggleItinerary = (id) => {
    if (selectedAttractionIds.includes(id)) {
      setSelectedAttractionIds(selectedAttractionIds.filter((item) => item !== id));
    } else {
      setSelectedAttractionIds([...selectedAttractionIds, id]);
    }
  };

  const handleRemoveFromItinerary = (id) => {
    setSelectedAttractionIds(selectedAttractionIds.filter((item) => item !== id));
  };

  const handleGenerateItinerary = async ({ optimize_for, trip_duration_days, strategy }) => {
    try {
      setItineraryLoading(true);
      const res = await fetch('/api/itinerary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferences: {
            ...preferences,
            trip_duration_days,
          },
          selected_attraction_ids: selectedAttractionIds,
          optimize_for,
          strategy: strategy || '2opt',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setItinerary(data);
      }
    } catch (err) {
      console.error('Failed to generate itinerary:', err);
    } finally {
      setItineraryLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendStatus={backendStatus}
        totalAttractions={totalAttractions}
      />

      <main style={{ maxWidth: 1400, margin: '24px auto', padding: '0 24px', flex: 1, width: '100%' }}>
        {activeTab === 'recommendations' && (
          <div>
            <PreferenceForm
              preferences={preferences}
              setPreferences={setPreferences}
              origins={origins}
              categories={categories}
              onRecommend={handleRecommendClick}
              loading={loading}
            />

            {/* Recommendations Header & Quick Actions */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 16,
              flexWrap: 'wrap',
              gap: 12,
            }}>
              <div>
                <h3 style={{ fontSize: '1.25rem' }}>
                  Recommended Destinations ({recommendations.length} Top Matches)
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Ranked via Multi-Criteria Index (Weight λ = {preferences.sustainability_priority})
                </p>
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => setActiveTab('comparison')}
                  className="btn-secondary"
                  style={{ fontSize: '0.82rem' }}
                >
                  <GitCompare size={14} />
                  <span>Compare with C1 Baseline</span>
                </button>
                <button
                  onClick={() => setActiveTab('map')}
                  className="btn-secondary"
                  style={{ fontSize: '0.82rem' }}
                >
                  <MapPin size={14} />
                  <span>View on Map</span>
                </button>
              </div>
            </div>

            {/* Grid of Recommendation Cards */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
              gap: 20,
            }}>
              {recommendations.map((item, index) => (
                <RecommendationCard
                  key={item.attraction.id}
                  item={item}
                  rank={index + 1}
                  onAddToItinerary={handleToggleItinerary}
                  isInItinerary={selectedAttractionIds.includes(item.attraction.id)}
                />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'comparison' && (
          <ComparisonView
            comparisons={comparisons}
            preferences={preferences}
          />
        )}

        {activeTab === 'map' && (
          <MapView
            attractions={allDestinations}
            recommendations={recommendations}
            itinerary={itinerary}
            selectedAttractionIds={selectedAttractionIds}
            onAddToItinerary={handleToggleItinerary}
          />
        )}

        {activeTab === 'itinerary' && (
          <ItineraryView
            selectedAttractionIds={selectedAttractionIds}
            onRemoveFromItinerary={handleRemoveFromItinerary}
            onGenerateItinerary={handleGenerateItinerary}
            itinerary={itinerary}
            loading={itineraryLoading}
            allAttractions={allDestinations}
            preferences={preferences}
          />
        )}

        {activeTab === 'research' && (
          <ResearchDashboard />
        )}

        {activeTab === 'user-study' && (
          <UserStudyView />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '24px',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: 'var(--text-muted)',
        background: 'rgba(11, 15, 23, 0.9)',
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          AuraTour • A Sustainable and Crowd-Aware Tourism Recommendation System • Rajasthan Research Dataset
        </div>
      </footer>
    </div>
  );
}
