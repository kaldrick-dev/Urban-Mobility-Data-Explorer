import { api } from "./api.js";
import * as charts from "./charts.js";
import { initMap, paint } from "./map.js";

const state = { filters: { pickup_borough: null } };

const fmt = {
    int:  (n) => Number(n).toLocaleString("en-US"),
    usd:  (n) => "$" + Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 }),
    fare: (n) => "$" + Number(n).toFixed(2),
};

// ── Loading bar ─────────────────────────────────────────────
const bar = document.getElementById("loadingBar");
function startLoad() { bar.classList.add("active"); }
function endLoad()   { bar.classList.remove("active"); }

// ── KPI panel ───────────────────────────────────────────────
function setKpis(s) {
    const el = (id, v) => (document.getElementById(id).textContent = v);
    el("kpiTrips",    fmt.int(s.total_trips));
    el("kpiRevenue",  fmt.usd(s.total_revenue));
    el("kpiFare",     fmt.fare(s.avg_fare));
    el("kpiDistance", s.avg_distance.toFixed(1) + " mi");
    el("kpiSpeed",    s.avg_speed_mph.toFixed(1) + " mph");
    el("kpiTip",      fmt.fare(s.avg_tip_count));
}

// ── Top routes ──────────────────────────────────────────────
function setTopRoutes(rows) {
    const max = Math.max(...rows.map(r => r.trip_count));
    document.getElementById("routeList").innerHTML = rows.map((r, i) => `
        <div class="route">
            <span class="route-rank">${i + 1}</span>
            <div class="route-body">
                <div class="route-od">
                    <span class="rz">${r.pickup_zone}</span>
                    <span class="arrow">→</span>
                    <span class="rz">${r.dropoff_zone}</span>
                </div>
                <div class="route-boroughs">
                    <span class="borough-tag">${r.pickup_borough}</span>
                    <span class="arrow-sm">→</span>
                    <span class="borough-tag">${r.dropoff_borough}</span>
                </div>
                <div class="route-bar">
                    <span style="width:${Math.round(r.trip_count / max * 100)}%"></span>
                </div>
                <div class="route-meta">
                    <span>${fmt.int(r.trip_count)} trips</span>
                    <span>${fmt.fare(r.avg_fare)} avg fare</span>
                </div>
            </div>
        </div>
    `).join("");
}

// ── Main data load ───────────────────────────────────────────
async function loadAll() {
    startLoad();
    const f = state.filters;
    const [stats, hour, fare, speed, routes, distance, day] = await Promise.all([
        api.tripStats(f),
        api.tripsByHour(f),
        api.fareDistribution(f),
        api.speedByHour(f),
        api.topRoutes(f),
        api.distanceDistribution(f),
        api.tripsByDay(f),
    ]);
    setKpis(stats);
    charts.demandByHour(hour);
    charts.fareDistribution(fare);
    charts.speedByHour(speed);
    charts.distanceDistribution(distance);
    charts.tripsByDay(day);
    setTopRoutes(routes);
    await paint(f);
    endLoad();
}

// ── Borough filter chips ─────────────────────────────────────
async function buildFilters() {
    const boroughs = await api.boroughs();
    const wrap = document.getElementById("boroughChips");
    const mk = (label, value) => {
        const b = document.createElement("button");
        b.className = "chip" + (value === state.filters.pickup_borough ? " on" : "");
        b.textContent = label;
        b.onclick = () => {
            state.filters.pickup_borough = value;
            [...wrap.children].forEach(c => c.classList.remove("on"));
            b.classList.add("on");
            loadAll();
        };
        return b;
    };
    wrap.appendChild(mk("All NYC", null));
    boroughs.forEach(bo => wrap.appendChild(mk(bo, bo)));
}

// ── Trip explorer ────────────────────────────────────────────
function timeBucket(dateStr) {
    const h = Number(dateStr.slice(11, 13));
    if (h >= 5  && h < 12) return "morning";
    if (h >= 12 && h < 17) return "afternoon";
    if (h >= 17 && h < 22) return "evening";
    return "night";
}

let allTrips    = [];
let currentRows = [];
let pageIndex   = 0;
const PAGE_SIZE = 10;

function renderTrips() {
    const body  = document.getElementById("tripRows");
    const start = pageIndex * PAGE_SIZE;
    const slice = currentRows.slice(start, start + PAGE_SIZE);

    body.innerHTML = slice.length
        ? slice.map(t => `
            <tr>
                <td>${t.pickup_datetime}</td>
                <td>${t.pickup_zone  ?? "—"}</td>
                <td>${t.dropoff_zone ?? "—"}</td>
                <td>${Number(t.trip_distance).toFixed(2)} mi</td>
                <td>${Number(t.duration_minutes).toFixed(0)} min</td>
                <td>${Number(t.speed_mph).toFixed(1)} mph</td>
                <td>${fmt.fare(t.total_amount)}</td>
                <td class="${t.is_rush_hour ? "te-rush-yes" : "te-rush-no"}">
                    ${t.is_rush_hour ? "Yes" : "No"}
                </td>
            </tr>`).join("")
        : `<tr><td colspan="8" class="te-empty">No trips match these filters.</td></tr>`;

    const totalPages = Math.max(1, Math.ceil(currentRows.length / PAGE_SIZE));
    document.getElementById("pgInfo").textContent =
        `Page ${pageIndex + 1} of ${totalPages} · ${fmt.int(currentRows.length)} trips`;
    document.getElementById("pgPrev").disabled = pageIndex === 0;
    document.getElementById("pgNext").disabled = pageIndex >= totalPages - 1;
}

function applyTripFilters() {
    const minFare = parseFloat(document.getElementById("fMinFare").value);
    const maxFare = parseFloat(document.getElementById("fMaxFare").value);
    const time    = document.getElementById("fTime").value;
    const sortBy  = document.getElementById("fSort").value;

    currentRows = allTrips.filter(t => {
        if (!isNaN(minFare) && t.total_amount < minFare) return false;
        if (!isNaN(maxFare) && t.total_amount > maxFare) return false;
        if (time && timeBucket(t.pickup_datetime) !== time) return false;
        return true;
    });

    currentRows.sort((a, b) =>
        sortBy === "pickup_datetime"
            ? (a.pickup_datetime < b.pickup_datetime ? 1 : -1)
            : (b[sortBy] ?? 0) - (a[sortBy] ?? 0)
    );

    pageIndex = 0;
    renderTrips();
}

function resetTripFilters() {
    ["fMinFare", "fMaxFare"].forEach(id => (document.getElementById(id).value = ""));
    document.getElementById("fTime").value = "";
    document.getElementById("fSort").value = "pickup_datetime";
    applyTripFilters();
}

async function initTable() {
    document.getElementById("teStatus").textContent = "Loading trips…";
    // API returns {trips, page, per_page, total}; mock returns a plain array
    const result = await api.trips({ per_page: 100 });
    allTrips = Array.isArray(result) ? result : (result.trips ?? []);
    document.getElementById("teStatus").textContent = "";

    document.getElementById("fApply").onclick = applyTripFilters;
    document.getElementById("fReset").onclick  = resetTripFilters;
    document.getElementById("pgPrev").onclick  = () => { if (pageIndex > 0) { pageIndex--; renderTrips(); } };
    document.getElementById("pgNext").onclick  = () => { pageIndex++; renderTrips(); };

    ["fMinFare", "fTime", "fSort"].forEach(id =>
        document.getElementById(id).addEventListener("keydown", e => {
            if (e.key === "Enter") applyTripFilters();
        })
    );
    applyTripFilters();
}

// ── Boot ─────────────────────────────────────────────────────
(async function start() {
    await buildFilters();
    await initMap(state.filters);
    await loadAll();
    await initTable();
})();
