import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { MapPin, Navigation, Info, Plus } from 'lucide-react';

export default function MapView({
  attractions,
  recommendations,
  itinerary,
  onAddToItinerary,
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

      // CartoDB Dark Matter tiles for a sleek dark aesthetic
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map);

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
    const targetAttractions = attractions && attractions.length > 0 ? attractions : (recommendations ? recommendations.map(r => r.attraction) : []);

    targetAttractions.forEach((att) => {
      const rec = recMap[att.id];
      const isSelected = selectedAttractionIds?.includes(att.id);
      const isTopRec = rec && rec.rank <= 5;

      const markerColor = isSelected ? '#10b981' : (isTopRec ? '#059669' : '#3b82f6');
      const markerSize = isSelected ? 30 : (isTopRec ? 26 : 22);

      const customIcon = L.divIcon({
        className: 'custom-map-pin',
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
            font-size: 11px;
            font-weight: 700;
            border: 2px solid #ffffff;
            box-shadow: 0 0 12px ${markerColor}88;
            cursor: pointer;
          ">
            ${rec ? rec.rank : '•'}
          </div>
        `,
        iconSize: [markerSize, markerSize],
        iconAnchor: [markerSize / 2, markerSize / 2],
      });

      const marker = L.marker([att.latitude, att.longitude], { icon: customIcon });

      const popupHtml = `
        <div style="font-family: sans-serif; padding: 4px; color: #111827;">
          <h4 style="margin: 0 0 4px; font-size: 14px; font-weight: 700;">${att.name}</h4>
          <p style="margin: 0 0 6px; font-size: 11px; color: #4b5563;">${att.city}, ${att.district}</p>
          ${rec ? `<p style="margin: 0 0 6px; font-size: 12px; font-weight: 600; color: #059669;">Rank #${rec.rank} • Score: ${(rec.final_score * 100).toFixed(0)}%</p>` : ''}
          <p style="margin: 0 0 8px; font-size: 11px; color: #374151;">${att.description ? att.description.slice(0, 90) + '...' : ''}</p>
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
        color: '#10b981',
        weight: 4,
        opacity: 0.8,
        dashArray: '8, 8',
      });
      polylineLayer.addLayer(polyline);
    }

    // Fit map to bounds if markers exist
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
    }

    return () => {
      // Keep map instance alive across re-renders
    };
  }, [attractions, recommendations, itinerary, selectedAttractionIds]);

  return (
    <div className="glass-panel" style={{ padding: 20 }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
        flexWrap: 'wrap',
        gap: 12,
      }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <MapPin size={20} color="var(--emerald-400)" />
            Geographic POI & Route Visualizer
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Spatial distribution across Rajasthan • Highlighting low-carbon clusters & multi-stop routes
          </p>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: '0.78rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Selected in Route</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#059669' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Top 5 Recommendations</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#3b82f6' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Candidate Destination</span>
          </div>
        </div>
      </div>

      {/* Map Container */}
      <div
        ref={mapContainerRef}
        id="leaflet-map-container"
        style={{
          width: '100%',
          height: '560px',
          borderRadius: 14,
          overflow: 'hidden',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-md)',
        }}
      />
    </div>
  );
}
