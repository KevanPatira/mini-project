import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { MapPin } from 'lucide-react';

export default function MapView({
  attractions,
  recommendations,
  itinerary,
  selectedAttractionIds,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const polylineLayerRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize Leaflet map if not already done
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [26.9124, 75.7873], // Jaipur center
        zoom: 7,
        zoomControl: true,
      });

      // CartoDB Voyager tiles (warm/neutral aesthetic matching our palette)
      L.tileLayer(
        `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${import.meta.env.VITE_CARTO_API_KEY || ''}`,
        {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
          maxZoom: 19,
        }
      ).addTo(map);

      mapInstanceRef.current = map;
      markersLayerRef.current = L.layerGroup().addTo(map);
      polylineLayerRef.current = L.layerGroup().addTo(map);
    }

    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    const polylineLayer = polylineLayerRef.current;

    markersLayer.clearLayers();
    polylineLayer.clearLayers();

    // Map recommendation items by attraction ID for quick score lookup
    const recMap = {};
    if (recommendations) {
      recommendations.forEach((r, idx) => {
        recMap[r.attraction.id] = { ...r, rank: idx + 1 };
      });
    }

    const bounds = [];

    // Add attraction markers
    const targetAttractions = attractions && attractions.length > 0 
      ? attractions 
      : (recommendations ? recommendations.map(r => r.attraction) : []);

    targetAttractions.forEach((att) => {
      const rec = recMap[att.id];
      const isSelected = selectedAttractionIds?.includes(att.id);
      const isTopRec = rec && rec.rank <= 5;

      // Color coding: Terracotta for selected, Forest Green for top recs, Deep Pine for candidates
      const markerColor = isSelected ? '#C56B45' : (isTopRec ? '#1F3A32' : '#315C4C');
      const markerSize = isSelected ? 32 : (isTopRec ? 28 : 22);

      const customIcon = L.divIcon({
        className: 'at-map-custom-pin',
        html: `
          <div style="
            background: ${markerColor};
            width: ${markerSize}px;
            height: ${markerSize}px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            font-size: 11px;
            font-weight: 700;
            border: 2px solid #ffffff;
            box-shadow: 0 4px 10px rgba(31, 58, 50, 0.4);
            cursor: pointer;
            transition: transform 0.2s ease;
          ">
            ${rec ? rec.rank : '•'}
          </div>
        `,
        iconSize: [markerSize, markerSize],
        iconAnchor: [markerSize / 2, markerSize / 2],
      });

      const marker = L.marker([att.latitude, att.longitude], { icon: customIcon });

      const popupHtml = `
        <div style="font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; padding: 4px; color: #303632; max-width: 250px;">
          <h4 style="margin: 0 0 4px; font-size: 14px; font-weight: 700; color: #1F3A32; font-family: 'DM Serif Display', serif;">${att.name}</h4>
          <p style="margin: 0 0 6px; font-size: 11px; color: #C56B45; font-weight: 700;">${att.city}, ${att.district} District</p>
          ${rec ? `<p style="margin: 0 0 6px; font-size: 12px; font-weight: 700; color: #1F3A32;">Rank #${rec.rank} • Composite: ${(rec.final_score * 100).toFixed(0)}%</p>` : ''}
          <p style="margin: 0; font-size: 11px; color: #59665C; line-height: 1.45;">${att.description ? att.description.slice(0, 95) + '...' : ''}</p>
        </div>
      `;

      marker.bindPopup(popupHtml);
      markersLayer.addLayer(marker);
      bounds.push([att.latitude, att.longitude]);
    });

    // Draw route polyline if itinerary exists
    if (itinerary && itinerary.stops && itinerary.stops.length > 1) {
      const routeCoords = itinerary.stops.map((s) => [s.attraction.latitude, s.attraction.longitude]);
      const polyline = L.polyline(routeCoords, {
        color: '#C56B45',
        weight: 4,
        opacity: 0.9,
        dashArray: '8, 8',
      });
      polylineLayer.addLayer(polyline);
    }

    // Fit map to bounds if markers exist
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
    }
  }, [attractions, recommendations, itinerary, selectedAttractionIds]);

  return (
    <div className="at-card" style={{ padding: 28 }}>
      {/* Header Bar */}
      <div className="at-map-header-bar">
        <div>
          <div className="at-page-tagline" style={{ marginBottom: 6 }}>
            <MapPin size={13} color="var(--c-accent)" />
            <span>Geospatial Tourism Cartography</span>
          </div>
          <h3 style={{ fontSize: '1.45rem', color: 'var(--c-primary)' }}>
            Rajasthan POI & Multimodal Route Visualizer
          </h3>
          <p style={{ fontSize: '0.86rem', color: 'var(--c-text-secondary)', marginTop: 2 }}>
            Regional distribution across 18 districts • Displaying low-carbon clusters and sequential itinerary paths
          </p>
        </div>

        {/* Legend */}
        <div className="at-map-legend">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#C56B45', display: 'inline-block' }} />
            <span>Selected Stop</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#1F3A32', display: 'inline-block' }} />
            <span>Top 5 Recommendations</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#315C4C', display: 'inline-block' }} />
            <span>Candidate POI</span>
          </div>
        </div>
      </div>

      {/* Map Frame */}
      <div className="at-map-wrapper" style={{ position: 'relative' }}>
        <div
          ref={mapContainerRef}
          id="leaflet-map-container"
          className="at-map-canvas"
        />
        {/* Overlay Legend Panel */}
        <div style={{
          position: 'absolute',
          top: 12,
          right: 12,
          zIndex: 1000,
          backgroundColor: 'rgba(255, 255, 255, 0.92)',
          backdropFilter: 'blur(8px)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--c-border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          minWidth: 160,
        }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--c-text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 2 }}>
            Map Legend
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: 'var(--c-text-primary)' }}>
            <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#C56B45', display: 'inline-block', flexShrink: 0, boxShadow: '0 1px 3px rgba(197,107,69,0.4)' }} />
            <span>Selected Stop</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: 'var(--c-text-primary)' }}>
            <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#1F3A32', display: 'inline-block', flexShrink: 0, boxShadow: '0 1px 3px rgba(31,58,50,0.4)' }} />
            <span>Top 5 Picks</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: 'var(--c-text-primary)' }}>
            <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#315C4C', display: 'inline-block', flexShrink: 0, boxShadow: '0 1px 3px rgba(49,92,76,0.4)' }} />
            <span>Candidate POI</span>
          </div>
        </div>
      </div>
    </div>
  );
}
