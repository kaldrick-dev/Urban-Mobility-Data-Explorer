const BOROUGH_SHARES = {
    'Manhattan': 0.42, 
    'Brooklyn': 0.13,
    'Queens': 0.18,
    'Bronx': 0.08,
    'Staten Island': 0.02, EWR: 0.015
};
function scale(filters) {
    const b = filters && filters.pickup_borough;
    return b && BOROUGH_SHARES[b] != null ? BOROUGH_SHARES[b] : 1;
}
const r = (n, d = 0) => Number(n.toFixed(d));

export const mock = {
    tripStats(filters = {}) {
        const s = scale(filters);
        return {
            total_trips: Math.round(1000000 * s),
            avg_fare: 19.42,
            avg_distance: 3.21,
            avg_duration_minutes: 15.7,
            avg_passengers_count: 1.39,
            avg_tip_count: 2.84,
            avg_speed_mph: 12.3,
            total_revenue: r(56982440.55 * s, 2),
        };
    },

    tripsByHour(filters = {}) {
        const s = scale(filters);
        const shape = [34,24,17,12,10,14,28,52,68,60,55,58,62,64,66,72,84,95,98,90,78,66,54,44];
        return shape.map((v, h) => ({
            hour: h,
            trip_count: Math.round(v * 1400 * s),
            avg_fare: r(15 + Math.sin(h / 3) * 3 + (h>=18 ? 4 : 0), 2),
        }));
    },
    tripsByDay(filters = {}) {
        const s = scale(filters);
        const out =[];
        for (let d = 1; d <= 31; d++) {
            const weekend = d % 7 === 0 || d % 7 === 6;
            out.push({
                date: `2026-01-${d.toString().padStart(2, '0')}`,
                trip_count: Math.round((90000 + (weekend ? 18000 : 0) + Math.random() * 12000) * s),

            });
        }
        return out;
    },
    tripsByBorough(filters = {}) {
        return [
      { borough: "Manhattan", trip_count: 1819000, total_revenue: 33200000 },
      { borough: "Queens", trip_count: 528000, total_revenue: 12900000 },
      { borough: "Brooklyn", trip_count: 381000, total_revenue: 6600000 },
      { borough: "Bronx", trip_count: 117000, total_revenue: 1850000 },
      { borough: "EWR", trip_count: 44000, total_revenue: 1980000 },
      { borough: "Staten Island", trip_count: 14000, total_revenue: 252000 },
    ];
    },
    fareDistribution(filters = {}) {
        const s = scale(filters);
        const buckets = [
            ["0-5", 6], ["5-10", 28], ["10-15", 34], ["15-20", 24], ["20-30", 22], ["30-40", 11], ["40-60", 7], ["60+", 3]
        ];
        return buckets.map(([bucket, w]) => ({bucket, count: Math.round(w * 9000 * s) }));
    },
    distanceDistribution(filters = {}) {
        const s = scale(filters);
        const buckets = [
            ["0-1", 31],
            ["1-2", 27],
            ["2-3", 16],
            ["3-4", 13],
            ["4-5", 6],
            ["5-8", 7],
            ["8-12", 4],
            ["12+", 2],
        ];
        return buckets.map(([bucket, w]) => ({bucket, count: Math.round(w * 9000 * s) }));
    },
    speedByHour() {
    const base = [18,19,19,20,19,17,13,9.5,8.6,9.2,10.1,10.6,10.9,10.7,10.4,9.8,8.9,8.4,8.7,9.6,11.2,13.1,15.2,16.8];
    return base.map((v, h) => ({ hour: h, avg_speed_mph: r(v, 1), trip_count: 1000 }));
  },
  paymentBreakdown() {
    return [
        { payment_type: "Credit Card", count: 20610000, total_amount: 43200000 },
        { payment_type: "Cash", count:  786000, total_amount:  12100000 },
        { payment_type: "No Charge", count:  61000, total_amount:  980000 },
        { payment_type: "Dispute", count:  26000, total_amount:  420000 },
    ];
},
topRoutes(filters = {}, limit = 8) {
    const rows = [
      ["JFK Airport", "Midtown Center", "Queens", "Manhattan", 18420, 64.2],
      ["Upper East Side South", "Midtown Center", "Manhattan", "Manhattan", 15110, 11.4],
      ["LaGuardia Airport", "Upper East Side North", "Queens", "Manhattan", 12880, 38.7],
      ["Midtown Center", "Times Sq/Theatre District", "Manhattan", "Manhattan", 11230, 9.8],
      ["Penn Station/Madison Sq W", "Midtown Center", "Manhattan", "Manhattan", 10540, 8.9],
      ["Times Sq/Theatre District", "JFK Airport", "Manhattan", "Queens", 9870, 62.1],
      ["Upper West Side South", "Midtown Center", "Manhattan", "Manhattan", 9210, 12.6],
      ["East Village", "Lower East Side", "Manhattan", "Manhattan", 8430, 8.2],
    ];
    return rows.slice(0, limit).map(([pz, dz, pb, db, c, f]) => ({
      pickup_zone: pz, dropoff_zone: dz, pickup_borough: pb,
      dropoff_borough: db, trip_count: c, avg_fare: f,
    }));
  },
  boroughs() {
    return ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island", "EWR"];
  },
  tripsByZone() {
    return null;
  },
  trips(filters = {}) {
    const zones = ["Midtown Center", "JFK Airport", "Times Sq/Theatre District", "Upper East Side South", "Penn Station/Madison Sq West", "LaGuardia Airport", "Financial District South", "Yorkville East", "TriBeCa/Civic Center", "Battery Park City", "East Village", "Harlem South"];
    const payments = ["Credit card", "Cash", "No charge"];
    const rows = [];
    for (let i = 0; i<120; i++) {
        const dist = r(0.5 + Math.random() * 28, 2);
        const dur = Math.round(4 +dist * (2 + Math.random() *2.5));
        const speed = r ((dist / dur) * 60, 1);
        const fare = r(4 + dist * 2.6 + Math.random() * 8, 2);
        const hour = Math.floor(Math.random() * 24);
        const rush = (hour >= 7 && hour <= 9) || (hour >= 16 && hour <= 19);
        rows.push({
            pickup_datetime: `2026-06-${String(1 + (i % 28)).padStart(2, "0")} ${String(hour).padStart(2, "0")}:${String(Math.floor(Math.random() * 60)).padStart(2, "0")}`,
            pickup_zone: zones[Math.floor(Math.random() * zones.length)],
            dropoff_zone: zones[Math.floor(Math.random() *zones.length)],
            trip_distance: dist,
            duration_minutes: dur,
            speed_mph: speed,
            total_amount: fare,
            payment_type: payments[Math.floor(Math.random() * payments.length)],
            is_rush_hour: rush,
        });
    }
    return rows;
  },
};
