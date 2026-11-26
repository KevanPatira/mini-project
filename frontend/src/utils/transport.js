import { Train, Bus, Car, Plane, Navigation } from 'lucide-react';

/**
 * Maps a transportation mode string to its corresponding Lucide icon component.
 *
 * @param {string} mode - Transit mode (e.g. 'train', 'bus', 'car', 'flight')
 * @returns {React.ComponentType} Lucide icon component
 */
export function getTransportIcon(mode) {
  if (!mode) return Navigation;
  const m = mode.toLowerCase();
  if (m.includes('train') || m.includes('rail')) return Train;
  if (m.includes('bus')) return Bus;
  if (m.includes('car')) return Car;
  if (m.includes('flight') || m.includes('plane')) return Plane;
  return Navigation;
}

/**
 * Returns the canonical stroke/accent color for a transportation mode.
 *
 * @param {string} mode - Transit mode
 * @returns {string} Hex color code
 */
export function getTransportColor(mode) {
  if (!mode) return '#10b981';
  const m = mode.toLowerCase();
  if (m.includes('train') || m.includes('rail')) return '#2563eb'; // Royal Blue
  if (m.includes('bus')) return '#d97706';                        // Sunset Amber
  if (m.includes('flight') || m.includes('plane')) return '#9333ea'; // Royal Purple
  return '#10b981';                                              // Forest Emerald
}

/**
 * Format estimated fare in INR currency.
 */
export function formatFare(inr) {
  if (inr === null || inr === undefined || isNaN(inr)) return 'N/A';
  return `₹${Math.round(inr).toLocaleString('en-IN')}`;
}

/**
 * Format distance in km.
 */
export function formatDistance(km) {
  if (km === null || km === undefined || isNaN(km)) return 'N/A';
  return `${Math.round(km)} km`;
}

/**
 * Format travel duration in hours.
 */
export function formatDuration(hours) {
  if (hours === null || hours === undefined || isNaN(hours)) return 'N/A';
  return `~${hours.toFixed(1)} hrs`;
}

/**
 * Format carbon emissions in kg CO2e.
 */
export function formatEmissions(kg) {
  if (kg === null || kg === undefined || isNaN(kg)) return 'N/A';
  return `${kg.toFixed(2)} kg CO₂e`;
}
