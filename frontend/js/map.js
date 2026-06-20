import { CONFIG } from "./config.js";
let map, layer,geojson;
const greenRamp = (v) =>
    v >= 80 ? "#005a32" : v >= 60 ? "#238b45" : v >= 40 ? "#41ab5d" :
    v >= 25 ? "#74c476" : v >= 15 ? "#a1d99b" : v >= 6 ? "#c7e9c0" : "#edf8e9";

const BOROUGH_BASE = {
    Manhattan: [55,100], Queens: [8, 40], Brooklyn: [8, 38], Bronx: [3, 18], EWR: [12, 18], "Staten Island": [1, 7],
};
const SPIKES = { 132: 95, 138: 88, 161: 100, 162: 96, 230: 92, 237: 90, 236: 88, 186: 80, 234: 78 };
function mockValueFor(props) {
    if (SPIKES[props.LocationID]) return SPIKES[props.LocationID];
    const [lo, hi] = BOROUGH_BASE[props.Borough] || [5, 30];
    const j = (props.LocationID * 37) % 100 / 100;
    return Math.round(lo + (hi - lo) * j);

}

export async function initMap(filters) {
    const res = await fetch(CONFIG.GEOJSON_PATH);
    geojson = await res.json();
    map = L.map("map", { zoomControl: false, scrollWheelZoom: false, attributionControl: false });
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png", { maxZoom: 18 }).addTo(map);
    L.control.zoom({ position: "bottomleft" }).addTo(map);
    paint(filters);
}
export function paint() {
    if (!map) return;
    if (layer) layer.remove();
    layer = L.geoJSON(geojson, {
        style: (f) => ({
            fillColor: greenRamp(mockValueFor(f.properties)),
            weight: 0.5, color :"#fff", fillOpacity: 0.8,
        }),
        onEachFeature: (f, lyr) => {
            const p = f.properties;
            lyr.bindTooltip(`${p.zone}, ${p.Borough}`, { sticky: true });
            lyr.on("mouseover", () => lyr.setStyle({ weight: 1.6, color: "#0a7d4f" }));
            lyr.on("mouseout", () => lyr.setStyle({ weight: 0.5, color: "#fff" }));
        },
    }).addTo(map);
    map.fitBounds(layer.getBounds(), { padding: [10, 10] });
}