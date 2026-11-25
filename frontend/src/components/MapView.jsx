import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { MapPin, Layers, Check, ShieldCheck, Navigation } from 'lucide-react';

const CARTO_STYLES = {
  dark_all: {
    id: 'dark_all',
    name: 'Dark Matter',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  voyager: {
    id: 'voyager',
    name: 'Voyager',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  light_all: {
    id: 'light_all',
    name: 'Positron',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
};

export default function MapView({
  attractions,
  recommendations,
  itinerary,
  selectedAttractionIds,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const markersLayerRef = useRef(null);
  const polylineLayerRef = useRef(null);

  const [mapStyle, setMapStyle] = useState('dark_all');
  const cartoApiKey = import.meta.env.VITE_CARTO_API_KEY || '';
  const hasCartoKey = Boolean(cartoApiKey && cartoApiKey !== 'your_carto_api_key_here');

  // Initialize Leaflet map instance once
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [26.9124, 75.7873], // Jaipur center
        zoom: 7,
        zoomControl: true,
      });

      mapInstanceRef.current = map;
      markersLayerRef.current = L.layerGroup().addTo(map);
      polylineLayerRef.current = L.layerGroup().addTo(map);
    }
  }, []);

  // Update CARTO tile layer whenever mapStyle or cartoApiKey changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }

    const currentStyle = CARTO_STYLES[mapStyle] || CARTO_STYLES.dark_all;
    const tileUrl = hasCartoKey
      ? `${currentStyle.url}?api_key=${encodeURIComponent(cartoApiKey)}`
      : currentStyle.url;

    const newTileLayer = L.tileLayer(tileUrl, {
      attribution: currentStyle.attribution,
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    tileLayerRef.current = newTileLayer;
  }, [mapStyle, cartoApiKey, hasCartoKey]);

  // Update markers, bounds, and route polylines
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    const polylineLayer = polylineLayerRef.current;
    if (!map || !markersLayer || !polylineLayer) return;

    markersLayer.clearLayers();
    polylineLayer.clearLayers();

    // Map recommendation items by attraction ID for quick rank lookup
    const recMap = {};
    if (recommendations) {
      recommendations.forEach((r, idx) => {
        recMap[r.attraction.id] = { ...r, rank: idx + 1 };
      });
    }

    const bounds = [];

    // Add attraction markers
    const targetAttractions =
      attractions && attractions.length > 0
        ? attractions
        : recommendations
        ? recommendations.map((r) => r.attraction)
        : [];

    targetAttractions.forEach((att) => {
      const rec = recMap[att.id];
      const isSelected = selectedAttractionIds?.includes(att.id);
      const isTopRec = rec && rec.rank <= 5;

      const markerColor = isSelected ? '#10b981' : isTopRec ? '#059669' : '#3b82f6';
      const markerSize = isSelected ? 30 : isTopRec ? 26 : 22;

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
        <div style="font-family: sans-serif; padding: 4px; color: #111827; max-width: 220px;">
          <h4 style="margin: 0 0 4px; font-size: 13px; font-weight: 700;">${att.name}</h4>
          <p style="margin: 0 0 4px; font-size: 11px; color: #4b5563;">${att.city || ''}, ${att.district || ''}</p>
          ${
            rec
              ? `<p style="margin: 0 0 4px; font-size: 11px; font-weight: 600; color: #059669;">Rank #${rec.rank} • Score: ${(rec.final_score * 100).toFixed(0)}%</p>`
              : ''
          }
          <p style="margin: 0; font-size: 11px; color: #374151;">${att.description ? att.description.slice(0, 90) + '...' : ''}</p>
        </div>
      `;

      marker.bindPopup(popupHtml);
      markersLayer.addLayer(marker);
      bounds.push([att.latitude, att.longitude]);
    });

    // Draw route polylines with turn-by-turn road geometry if itinerary exists
    if (itinerary && itinerary.stops && itinerary.stops.length > 0) {
      itinerary.stops.forEach((stop, idx) => {
        let segmentCoords = [];

        // Check if turn-by-turn road geometry is provided by OpenRouteService
        if (stop.route_geometry && Array.isArray(stop.route_geometry) && stop.route_geometry.length > 1) {
          segmentCoords = stop.route_geometry;
        } else if (idx > 0) {
          const prevStop = itinerary.stops[idx - 1];
          segmentCoords = [
            [prevStop.attraction.latitude, prevStop.attraction.longitude],
            [stop.attraction.latitude, stop.attraction.longitude],
          ];
        }

        if (segmentCoords.length > 0) {
          const isTrain = stop.transport_mode === 'train';
          const isCar = stop.transport_mode === 'car';
          const strokeColor = isTrain ? '#38bdf8' : isCar ? '#10b981' : '#f59e0b';

          const polyline = L.polyline(segmentCoords, {
            color: strokeColor,
            weight: 4,
            opacity: 0.85,
            dashArray: isTrain ? '6, 6' : null,
          });

          if (idx > 0) {
            const prevStop = itinerary.stops[idx - 1];
            const legPopup = `
              <div style="font-family: sans-serif; font-size: 12px; color: #111827; padding: 4px;">
                <strong>Leg ${idx}:</strong> ${prevStop.attraction.name} &rarr; ${stop.attraction.name}<br/>
                <span>Road Distance: <b>${stop.travel_from_previous_km || 0} km</b></span><br/>
                <span>Mode: <b style="text-transform: capitalize;">${stop.transport_mode || 'transit'}</b> (${stop.travel_from_previous_hours || 0} hrs)</span><br/>
                <span style="color: #059669;">Emissions: <b>${stop.leg_emissions_kg || 0} kg CO₂e</b></span>
                ${
                  stop.routing_source === 'openrouteservice'
                    ? '<br/><span style="color: #2563eb; font-size: 10px; font-weight: 600;">&bull; OpenRouteService Turn-by-Turn</span>'
                    : ''
                }
              </div>
            `;
            polyline.bindPopup(legPopup);
          }

          polylineLayer.addLayer(polyline);

          // Add road coordinates to map bounds
          segmentCoords.forEach((pt) => {
            if (Array.isArray(pt) && pt.length >= 2) {
              bounds.push(pt);
            }
          });
        }
      });
    }

    // Fit map view to bounds
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
    }
  }, [attractions, recommendations, itinerary, selectedAttractionIds]);

  return (
    <div className="glass-panel" style={{ padding: 20 }}>
      {/* Header & Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div>
          <h3 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <MapPin size={20} color="var(--emerald-400)" />
            Geographic POI & Route Visualizer
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Spatial distribution across Rajasthan • Highlighting low-carbon clusters & multi-stop routes
          </p>
        </div>

        {/* Controls: CARTO style switcher & status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* CARTO Key indicator */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              fontSize: '0.74rem',
              padding: '4px 10px',
              borderRadius: 20,
              background: hasCartoKey ? 'rgba(16, 185, 129, 0.12)' : 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${hasCartoKey ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-subtle)'}`,
              color: hasCartoKey ? '#34d399' : 'var(--text-muted)',
            }}
            title={hasCartoKey ? 'CARTO API Key authenticated' : 'Using public CARTO tile layer'}
          >
            {hasCartoKey ? <ShieldCheck size={13} /> : <Layers size={13} />}
            <span>CARTO {hasCartoKey ? 'Authenticated' : 'Tiles'}</span>
          </div>

          {/* Style Selector */}
          <div
            style={{
              display: 'inline-flex',
              background: 'rgba(255, 255, 255, 0.04)',
              borderRadius: 8,
              padding: 2,
              border: '1px solid var(--border-subtle)',
            }}
          >
            {Object.values(CARTO_STYLES).map((style) => {
              const isActive = mapStyle === style.id;
              return (
                <button
                  key={style.id}
                  onClick={() => setMapStyle(style.id)}
                  style={{
                    padding: '4px 10px',
                    fontSize: '0.74rem',
                    fontWeight: isActive ? 600 : 400,
                    borderRadius: 6,
                    border: 'none',
                    background: isActive ? 'var(--emerald-500)' : 'transparent',
                    color: isActive ? '#ffffff' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {style.name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 12,
          padding: '6px 12px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: 8,
          fontSize: '0.75rem',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
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

        {itinerary && itinerary.stops && itinerary.stops.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--text-muted)' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 3, background: '#10b981', display: 'inline-block' }} /> Road (Car/Taxi)
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 3, background: '#38bdf8', display: 'inline-block', borderTop: '1px dashed #38bdf8' }} /> Rail Corridor
            </span>
            {itinerary.routing_provider && (
              <span style={{ color: 'var(--emerald-400)', fontWeight: 500 }}>
                &bull; {itinerary.routing_provider}
              </span>
            )}
          </div>
        )}
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
