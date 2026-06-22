# Urban Mobility Data Explorer

An interactive explorer for NYC Yellow Taxi trips — includes a Flask + SQLite backend
that ingests and cleans trip data, and a lightweight frontend for visualizing and
querying the data.

Quick start

1. Backend: install dependencies, ingest data, and start the API

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python pipeline.py    # ingest + build mobility.db
   python run.py         # start API at http://127.0.0.1:5000/api
   ```

2. Frontend: open the static site or serve it locally

   ```bash
   cd frontend
   # open index.html directly or run a simple server
   python -m http.server 8000
   # then visit http://localhost:8000
   ```

Project layout

- `backend/` — data ingestion pipeline, SQLite database, Flask API. See `backend/README.md`.
- `frontend/` — static frontend (HTML/CSS/JS) that talks to the backend API. See `frontend/README.md`.
- `data/` — expected location for raw data files and shapefiles. See `data/README.md`.

Where to go next

- To run the full demo: ingest backend data, start the API, then open the frontend in
  a browser and explore the visualizations and REST endpoints.

## Video walkthrough

- Watch a short walkthrough of the project: [YouTube walkthrough](https://youtu.be/v7I0ZpfNniw)
