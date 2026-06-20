import {CONFIG} from './config.js';
import {mock} from './mock-data.js';
function qs (params = {}) {
    const clean = Object.entries(params).filter(([, v]) => v != null && v !== "");
    return clean.length ? "?" + new URLSearchParams(clean).toString() : "";
}
async function get(path, params) {
  const res = await fetch(CONFIG.API_BASE + path + qs(params));
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  const json = await res.json();
  return json && "data" in json ? json.data : json;
}
async function live(path, params, mockFn) {
    if (CONFIG.USE_MOCK) return mockFn();
    try{
        const data = await get(path, params);
        return data == null ? mockFn() :data;
    } 
    catch (e) {
        console.warn(`[API] ${path}:`, e);
        return mockFn();
    }
}
export const api = {
    tripStats: (f) => live("/trip/stats", f, () => mock.tripStats(f)),
    tripsByHour: (f) => live("/analytics/trips-by-hour", f, () => mock.tripsByHour(f)),
    tripsByDay: (f) => live("/analytics/trips-by-day", f, () => mock.tripsByDay(f)),
    tripsByBorough: (f) => live("/analytics/trips-by-borough", f, () => mock.tripsByBorough(f)),
    fareDistribution: (f) => live("/analytics/fare-distribution", f, () => mock.fareDistribution(f)),
    distanceDistribution: (f) => live("/analytics/distance-distribution", f, () => mock.distanceDistribution(f)),
    speedByHour: (f) => live("/analytics/speed-by-hour", f, () => mock.speedByHour(f)),
    paymentBreakdown: (f) => live("/analytics/payment-breakdown", f, () => mock.paymentBreakdown(f)),
    topRoutes: (f, limit = 8) => live(`/analytics/top-routes`, {...f, limit}, () => mock.topRoutes(f, limit)),
    boroughs:() => live("/zones/boroughs", {}, () => mock.boroughs()),
    tripsByZone: (f) => live("/analytics/trips-by-zone", f, () => mock.tripsByZone(f)),
    trips: (f) => live("/trips", f, () => mock.trips(f)),
};
