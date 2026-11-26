import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { MapPin } from 'lucide-react';
import { getTransportColor } from '../../utils/transport';

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

    // Map itinerary stop order if itinerary exists
    const stopSequenceMap = {};
    if (itinerary && itinerary.stops) {
      itinerary.stops.forEach((stop, index) => {
        stopSequenceMap[stop.attraction.id] = {
          order: stop.order || index + 1,
          day: stop.day || 1,
          stop: stop,
        };
      });
    }

    // Add attraction markers
    const targetAttractions = attractions && attractions.length > 0 
      ? attractions 
      : (recommendations ? recommendations.map(r => r.attraction) : []);

    targetAttractions.forEach((att) => {
      const rec = recMap[att.id];
      const isSelected = selectedAttractionIds?.includes(att.id);
      const stopInfo = stopSequenceMap[att.id];
      const isTopRec = rec && rec.rank <= 5;

      // Color coding & sizing: Golden Terracotta for Itinerary stops, Terracotta for selected, Forest Green for top recs
      const isItineraryStop = Boolean(stopInfo);
      const markerColor = isItineraryStop ? '#C56B45' : (isSelected ? '#D97706' : (isTopRec ? '#1F3A32' : '#315C4C'));
      const markerSize = isItineraryStop ? 36 : (isSelected ? 32 : (isTopRec ? 28 : 22));

      const customIcon = L.divIcon({
        className: 'at-map-custom-pin',
        html: `
          <div style="
            background: ${isItineraryStop ? 'linear-gradient(135deg, #C56B45, #B45309)' : markerColor};
            width: ${markerSize}px;
            height: ${markerSize}px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            font-size: ${isItineraryStop ? '13px' : '11px'};
            font-weight: 800;
            border: ${isItineraryStop ? '2.5px solid #ffffff' : '2px solid #ffffff'};
            box-shadow: ${isItineraryStop ? '0 0 14px rgba(197, 107, 69, 0.7), 0 4px 10px rgba(0,0,0,0.3)' : '0 4px 10px rgba(31, 58, 50, 0.4)'};
            cursor: pointer;
            transition: transform 0.2s ease;
          ">
            ${isItineraryStop ? `#${stopInfo.order}` : (rec ? rec.rank : '•')}
          </div>
        `,
        iconSize: [markerSize, markerSize],
        iconAnchor: [markerSize / 2, markerSize / 2],
      });

      const marker = L.marker([att.latitude, att.longitude], { icon: customIcon });

      const popupHtml = `
        <div style="font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; padding: 4px; color: #303632; max-width: 260px;">
          ${isItineraryStop ? `
            <div style="background: var(--c-sage-soft, #e6ebe7); color: #1F3A32; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; margin-bottom: 6px; display: inline-block;">
              Itinerary Stop #${stopInfo.order} • Day ${stopInfo.day}
            </div>
          ` : ''}
          <h4 style="margin: 0 0 4px; font-size: 14px; font-weight: 700; color: #1F3A32; font-family: 'DM Serif Display', serif;">${att.name}</h4>
          <p style="margin: 0 0 6px; font-size: 11px; color: #C56B45; font-weight: 700;">${att.city}, ${att.district} District</p>
          ${isItineraryStop && stopInfo.stop ? `
            <div style="font-size: 11px; color: #1F3A32; margin-bottom: 6px;">
              <span>Arrival: <b>${stopInfo.stop.arrival_time || '9:00 AM'}</b></span> • <span>Duration: <b>${stopInfo.stop.visit_duration_hours || 2}h</b></span><br/>
              ${stopInfo.stop.transit_fare_inr ? `<span>Leg Fare: <b>₹${Math.round(stopInfo.stop.transit_fare_inr)}</b></span> • ` : ''}
              <span>CO₂e: <b>${stopInfo.stop.leg_emissions_kg || 0} kg</b></span>
            </div>
          ` : ''}
          ${rec ? `<p style="margin: 0 0 6px; font-size: 12px; font-weight: 700; color: #1F3A32;">Recommendation Rank #${rec.rank} • Match: ${(rec.final_score * 100).toFixed(0)}%</p>` : ''}
          <p style="margin: 0; font-size: 11px; color: #59665C; line-height: 1.45;">${att.description ? att.description.slice(0, 95) + '...' : ''}</p>
        </div>
      `;

      marker.bindPopup(popupHtml);
      markersLayer.addLayer(marker);
      bounds.push([att.latitude, att.longitude]);
    });

    // Draw route polylines with turn-by-turn road geometry if itinerary exists
    if (itinerary && itinerary.stops && itinerary.stops.length > 0) {
      let prevCoords = null;

      itinerary.stops.forEach((stop, idx) => {
        let segmentCoords = [];

        // Check if turn-by-turn road geometry is provided
        if (stop.route_geometry && Array.isArray(stop.route_geometry) && stop.route_geometry.length > 1) {
          segmentCoords = stop.route_geometry;
        } else if (prevCoords) {
          segmentCoords = [
            prevCoords,
            [stop.attraction.latitude, stop.attraction.longitude],
          ];
        }

        prevCoords = [stop.attraction.latitude, stop.attraction.longitude];

        if (segmentCoords.length > 0) {
          const mode = (stop.transport_mode || '').toLowerCase();
          const isTrain = mode.includes('train') || mode.includes('rail');
          const isFlight = mode.includes('flight') || mode.includes('plane');
          const strokeColor = getTransportColor(mode);

          // Outer glowing halo casing for high visibility
          const halo = L.polyline(segmentCoords, {
            color: strokeColor,
            weight: 8,
            opacity: 0.35,
            lineCap: 'round',
            lineJoin: 'round',
          });
          polylineLayer.addLayer(halo);

          // Inner crisp route polyline
          const polyline = L.polyline(segmentCoords, {
            color: strokeColor,
            weight: 4,
            opacity: 0.95,
            dashArray: isTrain ? '8, 8' : isFlight ? '4, 8' : null,
            lineCap: 'round',
            lineJoin: 'round',
          });

          // Leg popup
          const prevStopName = idx > 0 ? itinerary.stops[idx - 1].attraction.name : (itinerary.origin || 'Origin City');
          const legPopup = `
            <div style="font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; font-size: 12px; color: #1F3A32; padding: 6px; max-width: 250px;">
              <div style="font-weight: 700; font-size: 13px; color: #C56B45; margin-bottom: 4px;">
                Leg ${stop.order || idx + 1}: ${prevStopName} &rarr; ${stop.attraction.name}
              </div>
              <div style="margin-bottom: 2px;">
                <strong>Distance:</strong> ${Math.round(stop.travel_from_previous_km || 0)} km
              </div>
              <div style="margin-bottom: 2px;">
                <strong>Mode:</strong> <span style="text-transform: capitalize; font-weight: 600;">${stop.transport_mode || 'transit'}</span> (${stop.travel_from_previous_hours || 0} hrs)
              </div>
              ${stop.transit_fare_inr ? `
                <div style="margin-bottom: 2px; color: #C56B45; font-weight: 700;">
                  <strong>Fare:</strong> ₹${Math.round(stop.transit_fare_inr)}
                </div>
              ` : ''}
              <div style="color: #1F3A32; font-weight: 700;">
                <strong>Emissions:</strong> ${stop.leg_emissions_kg || 0} kg CO₂e
              </div>
              ${stop.routing_source === 'openrouteservice' ? `
                <div style="margin-top: 4px; font-size: 10px; color: #2563eb; font-weight: 600;">
                  &bull; Live OpenRouteService Turn-by-Turn
                </div>
              ` : ''}
            </div>
          `;
          polyline.bindPopup(legPopup);
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
          backgroundColor: 'rgba(255, 255, 255, 0.94)',
          backdropFilter: 'blur(8px)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--c-border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          minWidth: 175,
        }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--c-text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 2 }}>
            Map Legend
          </div>
          {itinerary && itinerary.stops && itinerary.stops.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: 'var(--c-primary)', fontWeight: 700 }}>
              <span style={{
                width: 16, height: 16, borderRadius: '50%', background: 'linear-gradient(135deg, #C56B45, #B45309)',
                color: '#fff', fontSize: '9px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
              }}>#1</span>
              <span>Trip Waypoint ({itinerary.stops.length} stops)</span>
            </div>
          )}
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

          {itinerary && itinerary.stops && itinerary.stops.length > 0 && (
            <div style={{ borderTop: '1px solid var(--c-border-subtle)', paddingTop: 6, display: 'flex', flexDirection: 'column', gap: 5, fontSize: '0.74rem' }}>
              <div style={{ fontSize: '0.66rem', fontWeight: 700, color: 'var(--c-accent)', textTransform: 'uppercase' }}>
                Trip Route ({itinerary.strategy_used === 'drl' ? 'DQN Agent' : '2-Opt TSP'})
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 14, height: 3, backgroundColor: '#2563eb', borderTop: '1px dashed #2563eb', display: 'inline-block' }} />
                <span>Rail Corridor</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 14, height: 3, backgroundColor: '#d97706', display: 'inline-block' }} />
                <span>Bus Route</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 14, height: 3, backgroundColor: '#10b981', display: 'inline-block' }} />
                <span>Road / Car</span>
              </div>
              {itinerary.routing_provider && (
                <div style={{ fontSize: '0.68rem', color: '#2563eb', fontWeight: 600, marginTop: 2 }}>
                  &bull; {itinerary.routing_provider}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
