const GREEN   = "#0a8f5a";
const GREEN_D  = "#07724a";
const TEAL     = "#0d9488";
const TEAL_L   = "rgba(13,148,136,.15)";
const GREEN_L  = "rgba(10,143,90,.12)";
const MUTED    = "#6b7280";
const GRID     = "rgba(0,0,0,.05)";

const instances = {};
let defaultsSet = false;

function setup() {
    if (defaultsSet) return;
    Chart.defaults.font.family = "'Inter', ui-sans-serif, system-ui, sans-serif";
    Chart.defaults.font.size   = 12;
    Chart.defaults.color       = MUTED;
    Chart.defaults.animation   = { duration: 500, easing: "easeOutQuart" };
    Chart.defaults.plugins.legend.display = false;
    Chart.defaults.plugins.tooltip.backgroundColor = "#1f2937";
    Chart.defaults.plugins.tooltip.titleColor       = "#f9fafb";
    Chart.defaults.plugins.tooltip.bodyColor        = "#d1d5db";
    Chart.defaults.plugins.tooltip.padding          = 10;
    Chart.defaults.plugins.tooltip.cornerRadius     = 8;
    Chart.defaults.plugins.tooltip.displayColors    = false;
    defaultsSet = true;
}

function upsert(id, cfg) {
    setup();
    const ctx = document.getElementById(id);
    if (!ctx) return;
    if (instances[id]) {
        instances[id].data    = cfg.data;
        instances[id].options = cfg.options ?? instances[id].options;
        instances[id].update("active");
    } else {
        instances[id] = new Chart(ctx, cfg);
    }
}

const scales = (yLabel) => ({
    x: {
        grid:  { display: false },
        ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12, color: MUTED },
        border: { display: false },
    },
    y: {
        grid:   { color: GRID },
        ticks:  { color: MUTED },
        border: { display: false },
        title:  { display: !!yLabel, text: yLabel, color: MUTED },
        beginAtZero: true,
    },
});

const tipCount = {
    plugins: {
        tooltip: {
            callbacks: {
                label: (c) => ` ${Number(c.parsed.y).toLocaleString()} trips`,
            },
        },
    },
};

export function demandByHour(rows) {
    upsert("chartDemand", {
        type: "bar",
        data: {
            labels: rows.map(d => `${d.hour}:00`),
            datasets: [{
                data: rows.map(d => d.trip_count),
                backgroundColor: rows.map(d =>
                    (d.hour >= 7 && d.hour <= 9) || (d.hour >= 16 && d.hour <= 18)
                        ? GREEN : "rgba(10,143,90,.45)"
                ),
                borderRadius: 5,
                maxBarThickness: 24,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            ...tipCount,
            scales: scales("Trips"),
        },
    });
}

export function fareDistribution(rows) {
    upsert("chartFare", {
        type: "bar",
        data: {
            labels: rows.map(d => `$${d.bucket}`),
            datasets: [{
                data: rows.map(d => d.count),
                backgroundColor: GREEN_D,
                borderRadius: 5,
                maxBarThickness: 32,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            ...tipCount,
            scales: scales("Trips"),
        },
    });
}

export function speedByHour(rows) {
    upsert("chartSpeed", {
        type: "line",
        data: {
            labels: rows.map(d => `${d.hour}:00`),
            datasets: [{
                data: rows.map(d => d.avg_speed_mph),
                borderColor: TEAL,
                backgroundColor: TEAL_L,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5,
                borderWidth: 2.5,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (c) => ` ${c.parsed.y.toFixed(1)} mph`,
                    },
                },
            },
            scales: scales("MPH"),
        },
    });
}

export function distanceDistribution(rows) {
    upsert("chartDistance", {
        type: "bar",
        data: {
            labels: rows.map(d => `${d.bucket} mi`),
            datasets: [{
                data: rows.map(d => d.count),
                backgroundColor: TEAL,
                borderRadius: 5,
                maxBarThickness: 32,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            ...tipCount,
            scales: scales("Trips"),
        },
    });
}

export function tripsByDay(rows) {
    upsert("chartDay", {
        type: "line",
        data: {
            labels: rows.map(d => d.date.slice(5)),
            datasets: [{
                data: rows.map(d => d.trip_count),
                borderColor: GREEN,
                backgroundColor: GREEN_L,
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                pointHoverRadius: 5,
                pointBackgroundColor: GREEN,
                borderWidth: 2.5,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            ...tipCount,
            scales: scales("Trips"),
        },
    });
}
