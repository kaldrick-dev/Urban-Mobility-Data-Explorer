Urban Mobility Data Explorer — Frontend

Simple static frontend that consumes the backend API and provides maps and charts
for exploring taxi trip patterns.

Files of interest

- `index.html` — main page and app mount point
- `styles.css` — visual styles
- `taxi_zones.geojson` — zone boundaries used for the map
- `js/` — frontend logic
  - `config.js` — API base URL and configuration
  - `api.js` — wrappers for calling backend endpoints
  - `app.js` — initialization and UI glue
  - `map.js`, `charts.js` — visualization helpers

Running locally

1. Start a simple HTTP server from the `frontend` directory:

```bash
cd frontend
python -m http.server 8000
# open http://localhost:8000 in your browser
```

2. Ensure the backend is running at the URL configured in `js/config.js` (default: `http://127.0.0.1:5000/api`).

Development tips

- Use your browser devtools to inspect network requests to `/api` endpoints.
- To change the backend target, edit `js/config.js`.
