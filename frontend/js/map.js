import { CONFIG } from "./config.js";
import { api } from "./api.js";

let map, layer, geojson;

const greenRamp = (v) =>
    v >= 80 ? "#005a32" : v >= 60 ? "#238b45" : v >= 40 ? "#41ab5d" :
    v >= 20 ? "#74c476" : v >= 8  ? "#c7e9c0" : "#edf8e9";

export async function initMap(filters) {
    const res = await fetch(CONFIG.GEOJSON_PATH);
    geojson = await res.json();
    map = L.map("map", {
        zoomControl: false,
        scrollWheelZoom: false,
        attributionControl: false,
    });
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png", {
        maxZoom: 18,
    }).addTo(map);
    L.control.zoom({ position: "bottomleft" }).addTo(map);
    await paint(filters);
}

export async function paint(filters = {}) {
    if (!map) return;
    if (layer) layer.remove();

    const zones = await api.tripsByZone(filters) || [];

    const counts = {};
    let maxCount = 1;
    zones.forEach(z => {
        counts[z.zone_id] = z.trip_count;
        if (z.trip_count > maxCount) maxCount = z.trip_count;
    });

    const pct = (id) => Math.round((counts[id] || 0) / maxCount * 100);

    layer = L.geoJSON(geojson, {
        style: (f) => ({
            fillColor: greenRamp(pct(f.properties.LocationID)),
            weight: 0.5,
            color: "#fff",
            fillOpacity: 0.82,
        }),
        onEachFeature: (f, lyr) => {
            const p = f.properties;
            const count = counts[p.LocationID];
            const tip = count
                ? `<b>${p.zone}</b><br>
                   <span style="color:#5a6b62">${p.Borough}</span><br>
                   <b style="color:#0a8f5a">${count.toLocaleString()}</b> pickups`
                : `<b>${p.zone}</b><br>
                   <span style="color:#5a6b62">${p.Borough} · No data</span>`;
            lyr.bindTooltip(tip, { sticky: true, className: "map-tip" });
            lyr.on("mouseover", () => lyr.setStyle({ weight: 2, color: "#0a7d4f", fillOpacity: 0.95 }));
            lyr.on("mouseout",  () => lyr.setStyle({ weight: 0.5, color: "#fff", fillOpacity: 0.82 }));
        },
    }).addTo(map);

    map.fitBounds(layer.getBounds(), { padding: [10, 10] });
}
