import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './components/LandingPage';
import PreferenceForm from './components/PreferenceForm';
import RecommendationCard from './components/RecommendationCard';
import ComparisonView from './components/ComparisonView';
import MapView from './components/MapView';
import ItineraryView from './components/ItineraryView';
import ResearchDashboard from './components/ResearchDashboard';
import UserStudyView from './components/UserStudyView';
import { GitCompare, MapPin, Menu, ChevronRight } from 'lucide-react';
import './styles/global.css';
import './styles/components.css';
import './styles/landing.css';

export default function RedesignApp({
  activeTab,
  setActiveTab,
  backendStatus,
  totalAttractions,
  preferences,
  setPreferences,
  origins,
  categories,
  allDestinations,
  recommendations,
  comparisons,
  selectedAttractionIds,
  itinerary,
  loading,
  itineraryLoading,
  onRecommend,
  onToggleItinerary,
  onRemoveFromItinerary,
  onGenerateItinerary,
  onToggleLegacy,
  isRedesignActive,
}) {
  const [showLanding, setShowLanding] = useState(true);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const getTabTitle = (tab) => {
    switch (tab) {
      case 'recommendations': return { title: 'Destination Discovery', sub: 'Pareto-optimal sustainable recommendations' };
      case 'comparison': return { title: 'C1 vs C5 Compare', sub: 'Baseline interest ranking vs multi-criteria ablation' };
      case 'map': return { title: 'Interactive Map', sub: 'Geospatial distribution across Rajasthan districts' };
      case 'itinerary': return { title: 'Smart Itinerary Planner', sub: 'Deep Q-Network and 2-Opt sequential travel routing' };
      case 'research': return { title: 'Research & Metrics', sub: 'Empirical ablation findings & algorithmic benchmarks' };
      case 'user-study': return { title: 'User Study Survey', sub: 'Double-blinded Likert academic human evaluation' };
      default: return { title: 'Sustainable Tourism Recommender', sub: 'Rajasthan Sustainable Tourism' };
    }
  };

  const currentTabInfo = getTabTitle(activeTab);

  // Show cinematic landing page before entering the app
  if (showLanding) {
    return (
      <LandingPage
        onEnterApp={() => setShowLanding(false)}
        setActiveTab={setActiveTab}
      />
    );
  }

  return (
    <div className="at-redesign-root">
      <div className="at-shell">
        {/* Left Vertical Sidebar */}
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          backendStatus={backendStatus}
          totalAttractions={totalAttractions}
          onToggleLegacy={onToggleLegacy}
          isRedesignActive={isRedesignActive}
          mobileOpen={mobileNavOpen}
          setMobileOpen={setMobileNavOpen}
          onGoHome={() => setShowLanding(true)}
        />

        {/* Content Area */}
        <div className="at-content-area">
          {/* Topbar Header */}
          <header className="at-topbar">
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <button
                className="at-mobile-menu-btn"
                onClick={() => setMobileNavOpen(true)}
                type="button"
                aria-label="Open navigation menu"
              >
                <Menu size={22} />
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--c-text-muted)', fontWeight: 600 }}>Rajasthan Explorer</span>
                <ChevronRight size={14} color="var(--c-text-light)" />
                <span style={{ color: 'var(--c-primary)', fontWeight: 700 }}>
                  {currentTabInfo.title}
                </span>
              </div>
            </div>

            {/* Quick Context Chips */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span className="at-badge at-badge-neutral" style={{ fontSize: '0.74rem' }}>
                Origin: {origins[preferences.origin_city]?.name || 'Rajasthan'}
              </span>
              <span className="at-badge at-badge-sustain" style={{ fontSize: '0.74rem' }}>
                Eco-Weight: {(preferences.sustainability_priority * 100).toFixed(0)}%
              </span>
            </div>
          </header>

          {/* Main Body */}
          <main className="at-main-body">
            <div className="at-container">
              {activeTab === 'recommendations' && (
                <div>
                  {/* Preferences Configuration Panel */}
                  <PreferenceForm
                    preferences={preferences}
                    setPreferences={setPreferences}
                    origins={origins}
                    categories={categories}
                    onRecommend={onRecommend}
                    loading={loading}
                  />

                  {/* Recommendations Section Header & Jump Shortcuts */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 24,
                    flexWrap: 'wrap',
                    gap: 16,
                  }}>
                    <div>
                      <h3 style={{ fontSize: '1.65rem', color: 'var(--c-primary)', marginBottom: 2 }}>
                        Top Recommended POIs ({recommendations.length} Destinations)
                      </h3>
                      <p style={{ fontSize: '0.9rem', color: 'var(--c-text-secondary)' }}>
                        Ranked via multi-criteria composite index with sustainability priority λ = {preferences.sustainability_priority}
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      <button
                        onClick={() => setActiveTab('comparison')}
                        className="at-btn-secondary"
                        type="button"
                      >
                        <GitCompare size={15} color="var(--c-accent)" />
                        <span>Compare with C1 Baseline</span>
                      </button>
                      <button
                        onClick={() => setActiveTab('map')}
                        className="at-btn-secondary"
                        type="button"
                      >
                        <MapPin size={15} color="var(--c-primary)" />
                        <span>Explore on Map</span>
                      </button>
                    </div>
                  </div>

                  {/* Recommendation Cards Grid */}
                  <div className="at-discovery-grid">
                    {recommendations.map((item, index) => (
                      <RecommendationCard
                        key={item.attraction.id}
                        item={item}
                        rank={index + 1}
                        onAddToItinerary={onToggleItinerary}
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
                />
              )}

              {activeTab === 'itinerary' && (
                <ItineraryView
                  selectedAttractionIds={selectedAttractionIds}
                  onRemoveFromItinerary={onRemoveFromItinerary}
                  onGenerateItinerary={onGenerateItinerary}
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
            </div>
          </main>

          {/* Footer */}
          <Footer />
        </div>
      </div>
    </div>
  );
}
