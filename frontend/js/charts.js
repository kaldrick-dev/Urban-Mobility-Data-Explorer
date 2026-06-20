const GREEN = "#0a8f5a", GREEN_D = "#0a7d4f", TEAL = "#14b8a6";
const MUTED = "#5a6b62", GRID = "rgba(21,32,27,.07)";
const PIE = ["#0fae6e", "#0a7d4f", "#7cd0a8", "#cbe8d8"];

const charts ={};
let defaultsSet = false;
function upsert(id, cfg) {
    if (!defaultsSet) {
    Chart.defaults.font.family = "ui-sans-serif, system-ui, -apple-system, sans-serif";
    Chart.defaults.color = MUTED;
    Chart.defaults.plugins.legend.labels.boxWidth = 12;
    defaultsSet = true;
  }
    const ctx = document.getElementById(id);
    if (charts[id]) {
        charts[id].data=cfg.data;
        charts[id].options=cfg.options;
        charts[id].update();
     }
      else {
        charts[id] = new Chart(ctx, cfg);

    }
}
const baseScales =(yTitle) => ({
    x: {
        grid: {display: false},
        ticks: {maxRotation: 0, autoSkip: true, maxTicksLimit: 12},
        },
    y: {
        grid: {color: GRID},
        title: {display: !!yTitle, text: yTitle},
        color: MUTED,
        beginAtZero: true},
    });
    const noLegend = {plugins: {legend: {display: false}}};

export function demandByHour(rows){
    upsert("chartDemand", {
        type: "bar",
        data: {
            labels: rows.map(d => `${d.hour}:00`),
            datasets: [{
                label: "TRIPS",
                data: rows.map(d => d.trip_count),
                borderColor: GREEN,
                borderRadius: 4,
                backgroundColor: GREEN_D,
                maxBarThickness: 22,
                tension: 0.4
            }],
            },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...noLegend,
            scales: baseScales("Trips")
            },
        });
}
export function fareDistribution(rows) {
    upsert("chartFare", {
        type: "bar",
        data: {
            labels: rows.map(d => `$${d.bucket}`),
            datasets: [{
                label: "TRIPS",
                data: rows.map(d => d.count),
                borderColor: GREEN,
                borderRadius: 4,
                backgroundColor: GREEN_D
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...noLegend,
            scales: baseScales("Trips")
        },
    });
}
export function speedByHour(rows) {
    upsert("chartSpeed", {
        type: "line",
        data: {
            labels: rows.map(d => `${d.hour}:00`),
            datasets: [{
                label: "AVG SPEED (MPH)",
                data: rows.map(d => d.avg_speed_mph),
                borderColor: TEAL,
                backgroundColor: "rgba(20,184,166,.12)",
                fill: true,
                tension: .35,
                pointRadius: 0,
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...noLegend,
            scales: baseScales("MPH")
        },
    });
}
export function paymentBreakdown(rows) {
    upsert("chartPayment", {
        type: "doughnut",
        data: {
            labels: rows.map(d => d.payment_type),
            datasets: [{
                data: rows.map(d => d.count),
                backgroundColor: PIE,
                borderWidth: 2,
                borderColor: "#fff",
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "62%",
            plugins: {
                legend: {
                    position: "bottom",
                }
        }
    }
    });
}
