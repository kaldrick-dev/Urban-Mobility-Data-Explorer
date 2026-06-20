import { api } from "./api.js"
import * as charts from "./charts.js";
import {initMap, paint} from "./map.js";

const state = { filters: { pickup_borough: null } };
const fmtInt = (n) => n.toLocaleString("en-US")
const fmtUsd = (n) => "$" + Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 });

function setKpis(s) {
    const el = (id, v) =>(document.getElementById(id).textContent = v); 
    el("kpiTrips",  fmtInt(s.total_trips));
    el("kpiRevenue", fmtUsd(s.total_revenue));
    el("kpiFare", "$" + s.avg_fare.toFixed(2));
    el("kpiDistance", s.avg_distance.toFixed(1) + " mi");
    el("kpiTip", "$" + s.avg_tip_count.toFixed(2));
    el("kpiSpeed", s.avg_speed_mph.toFixed(1));
}
function setTopRoutes(rows){
    const max = Math.max(...rows.map(r => r.trip_count));
    document.getElementById("routeList").innerHTML = rows.map(r => `
        <div class="route">
        <div class "route-od">
        <span class="rz">${r.pickup_zone}</span> 
        <span class="arrow">→</span>
        <span class="rz">${r.dropoff_zone}</span>
        </div>
        <div class="route-bar"><span style="width:${Math.round(r.trip_count / max * 100)}%"></span></div>
        <div class="route-meta">${fmtInt(r.trip_count)} trips, $${r.avg_fare.toFixed(2)} avg</div>
        </div>
    `).join("");
}
async function loadAll(){
    const f = state.filters;
    const [stats, hour, fare, speed, pay, routes] = await Promise.all([
        api.tripStats(f), api.tripsByHour(f), api.fareDistribution(f), api.speedByHour(f), api.paymentBreakdown(f), api.topRoutes(f),
    ]);
    setKpis(stats);
    charts.demandByHour(hour);
    charts.fareDistribution(fare);
    charts.speedByHour(speed);
    charts.paymentBreakdown(pay);
    setTopRoutes(routes);
    paint(f);
}
async function buildFilters() {
    const boroughs = await api.boroughs();
    const wrap = document.getElementById("boroughChips");
    const mk = (label, value) => {
        const b = document.createElement("button");
        b.className = "chip" + (value === state.filters.pickup_borough ? " on": "");
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
function timeBucket(dateStr) {
    const h = Number(dateStr.slice(11, 13));
    if (h >= 5 && h < 12) return "morning";
    if (h >= 12 && h < 17) return "afternoon";
    if (h >= 17 && h < 22) return "evening";
    return "night";
}
let allTrips =[];
let currentRows = [];
let pageIndex = 0;
const PAGE_SIZE = 5;

function renderTrips() {
    const body = document.getElementById("tripRows");
    const start = pageIndex * PAGE_SIZE;
    const pageRows = currentRows.slice(start, start + PAGE_SIZE);

    if (!pageRows.length) {
        body.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--muted);padding:20px">No trips match these filters.</td></tr>`;
    } else {
        body.innerHTML = pageRows.map(t =>
            `<tr>
            <td>${t.pickup_datetime}</td>
            <td>${t.pickup_zone}</td>
            <td>${t.dropoff_zone}</td>
            <td>${t.trip_distance} mi</td>
            <td>${t.duration_minutes} min</td>
            <td>${t.speed_mph} mph</td>
            <td>$${t.total_amount.toFixed(2)}</td>
            <td>${t.payment_type}</td>
            <td class="${t.is_rush_hour ? "te-rush-yes" : "te-rush-no"}">${t.is_rush_hour ? "Yes" : "No"}</td>
            </tr>`).join("");
    }

    const totalPages = Math.max(1, Math.ceil(currentRows.length / PAGE_SIZE));
    document.getElementById("pgInfo").textContent = `Page ${pageIndex + 1} of ${totalPages} (${currentRows.length} trips)`;
    document.getElementById("pgPrev").disabled = pageIndex === 0;
    document.getElementById("pgNext").disabled = pageIndex >= totalPages - 1;
}

function applyTripFilters() {
    const minFare = parseFloat(document.getElementById("fMinFare").value);
    const maxFare = parseFloat(document.getElementById("fMaxFare").value);
    const time = document.getElementById("fTime").value;
    const sortBy = document.getElementById("fSort").value;

    currentRows = allTrips.filter(t => {
        if (!isNaN(minFare) && t.total_amount < minFare) return false;
        if (!isNaN(maxFare) && t.total_amount > maxFare) return false;
        if (time && timeBucket(t.pickup_datetime) !== time) return false;
        return true;
    });

    currentRows.sort((a, b) => {
        if (sortBy === "pickup_datetime") return a.pickup_datetime < b.pickup_datetime ? 1 : -1;
        return b[sortBy] - a[sortBy];
    });

    pageIndex = 0;
    renderTrips();
}

function resetTripFilters() {
    document.getElementById("fMinFare").value = "";
    document.getElementById("fMaxFare").value = "";
    document.getElementById("fTime").value = "";
    document.getElementById("fSort").value = "pickup_datetime";
    applyTripFilters();
}
async function initTable() {
    allTrips = await api.trips({});
    document.getElementById("fApply").onclick = applyTripFilters;
    document.getElementById("fReset").onclick = resetTripFilters;
    document.getElementById("pgPrev").onclick = () => { if (pageIndex > 0) { pageIndex--; renderTrips(); } };
    document.getElementById("pgNext").onclick = () => { pageIndex++; renderTrips(); };
    ["fMinFare", "fTime", "fSort"].forEach(id =>{
        document.getElementById(id).addEventListener("keydown", (e) => {
            if (e.key === "Enter") applyTripFilters();
        });
    });
    applyTripFilters();
}

(async function start(){
    await buildFilters();
    await initMap(state.filters);
    await loadAll();
    await initTable();
}) ();