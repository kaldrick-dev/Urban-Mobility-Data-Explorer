# Urban Mobility Data Explorer - Database Schema

## Overview

The database uses a **normalized relational design** with two main tables optimized for trip analytics and geographic queries.

---

## Schema Design

### Table 1: `taxi_zones` (Master Dimension Table)

**Purpose:** Store NYC taxi zone reference data with geographic boundaries.

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `zone_id` | INTEGER | PRIMARY KEY | Unique zone identifier (1-265) |
| `borough` | TEXT | NULL | NYC borough name (Manhattan, Bronx, Queens, Brooklyn, Staten Island, EWR) |
| `zone` | TEXT | NULL | Zone name (e.g., "Alphabet City", "Jamaica Bay") |
| `service_zone` | TEXT | NULL | Service classification (Yellow Zone, Green Zone, Boro Zone, Airports, etc.) |
| `geometry` | TEXT | NULL | GeoJSON-formatted polygon boundary (WGS84 EPSG:4326) |

**Row Count:** 265

**Indexes:** PRIMARY KEY on `zone_id`

**Normalization:** 1NF (atomic values), 2NF (depends only on zone_id), 3NF (no transitive dependencies)

---

### Table 2: `trips` (Fact Table)

**Purpose:** Store individual trip records with computed metrics for analytics.

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `trip_id` | INTEGER | PRIMARY KEY | Auto-increment unique trip identifier |
| `pickup_datetime` | TEXT | NOT NULL | ISO 8601 format pickup timestamp |
| `dropoff_datetime` | TEXT | NOT NULL | ISO 8601 format dropoff timestamp |
| `passenger_count` | INTEGER | NULL | Number of passengers (1-6+) |
| `trip_distance` | REAL | NULL | Distance in miles (validated > 0) |
| `pulocation_id` | INTEGER | NULL | Pickup zone ID (FK → taxi_zones.zone_id) |
| `dolocation_id` | INTEGER | NULL | Dropoff zone ID (FK → taxi_zones.zone_id) |
| `fare_amount` | REAL | NULL | Base fare in USD (validated > 0) |
| `tip_amount` | REAL | NULL | Tip amount in USD (≥ 0) |
| `total_amount` | REAL | NULL | Total fare in USD (validated > 0) |
| `average_speed_mph` | REAL | NULL | Computed: trip_distance / duration_hours |
| `tip_percentage` | REAL | NULL | Computed: (tip_amount / fare_amount) * 100 |
| `rush_hour_flag` | INTEGER | NULL | Computed: 1 if weekday 07:00-10:00 or 16:00-19:00, else 0 |
| `payment_type` | INTEGER | NULL | Payment method (1=Credit, 2=Cash, 3=No Charge, 4=Dispute) |

**Row Count:** 7,606,112

**Indexes:**
- `idx_trips_pickup_datetime` on `pickup_datetime` (range queries)
- `idx_trips_pulocation_id` on `pulocation_id` (joins & filtering)
- `idx_trips_dolocation_id` on `dolocation_id` (joins & filtering)

**Normalization:** 1NF (atomic), 2NF (all non-key depend on trip_id), 3NF (no transitive deps)

---

## Data Integrity Constraints

### Referential Integrity
- **Foreign Keys (implicit):**
  - `trips.pulocation_id` → `taxi_zones.zone_id`
  - `trips.dolocation_id` → `taxi_zones.zone_id`

### Data Quality Rules (Applied During ETL)
1. **Temporal:** `dropoff_datetime > pickup_datetime`
2. **Distance:** `trip_distance > 0`
3. **Fare:** `fare_amount > 0 AND total_amount > 0`
4. **DateTime:** Both timestamps valid and non-NULL
5. **Location IDs:** Both IDs ≤ 265 (valid zone IDs)

### Records Removed During Cleaning
- ~54,770 rows with trip_distance ≤ 0
- ~9,557 rows with fare_amount ≤ 0
- ~8,545 rows with total_amount ≤ 0
- ~11,192 rows with invalid datetime or reverse timestamps

**Final Dataset:** 7,606,112 valid trips (~99% of raw data)

---

## Query Optimization Strategy

### Index Usage Patterns

| Query Type | Index | Use Case |
|-----------|-------|----------|
| Time range filter | `idx_trips_pickup_datetime` | "All trips on 2019-01-15" |
| Zone analytics | `idx_trips_pulocation_id`, `idx_trips_dolocation_id` | "Busiest pickup zones" |
| Zone joins | Both location indexes | "Trips from Manhattan to outer boroughs" |
| Speed analysis | None (sequential scan on `average_speed_mph`) | "Trips with avg_speed > 20 mph" |

### Recommended Additional Indexes (MySQL Migration)
```sql
CREATE INDEX idx_trips_payment_type ON trips(payment_type);
CREATE INDEX idx_trips_rush_hour_flag ON trips(rush_hour_flag);
CREATE INDEX idx_trips_pickup_dropoff ON trips(pulocation_id, dolocation_id, pickup_datetime);
```

---

## Normalization Analysis

### Current Design
✅ **Third Normal Form (3NF):**
- No repeating groups (1NF)
- All non-key attributes depend on the entire primary key (2NF)
- No transitive dependencies (3NF)
- Fact table separated from dimensions

✅ **Advantages:**
- No data redundancy
- Minimal storage footprint
- Easy to maintain data consistency
- Efficient for analytical queries with JOINs

### Alternative: Denormalized (Not Used)
❌ Would duplicate zone info on every trip row:
- Storage: +6 GB (adding borough, zone names to 7.6M rows)
- Maintenance: Complex updates if zone names change
- Benefit: Slightly faster for single-table queries (negligible)

---

## Cardinality & Statistics

| Metric | Value |
|--------|-------|
| Total trips | 7,606,112 |
| Unique zones | 265 |
| Unique pickup locations | 262 |
| Unique dropoff locations | 263 |
| Date range | 2019-01-01 to 2019-01-31 |
| Avg trips per day | ~245,357 |
| Avg trip distance | 3.5 miles |
| Avg fare | $13.50 |
| Avg tip % | 12.3% |

---

## Database Files

- **SQLite:** `backend/mobility.db` (~850 MB)
- **Log:** `backend/data_cleaning_log.txt` (summary of filtered records)

