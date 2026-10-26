# Data Source Audit

> **Audit date:** 2026-10-18
> **Geographic scope:** Rajasthan, India (with Indian origin cities for transport)
> **Status:** Initial feasibility assessment — datasets not yet downloaded

---

## A. Destination and Attraction Data

### A1. OpenStreetMap via Overpass API

| Field | Value |
|---|---|
| **Dataset name** | OpenStreetMap POI data (tourism, historic, leisure tags) |
| **URL** | https://overpass-turbo.eu / https://overpass-api.de/api/interpreter |
| **Provider** | OpenStreetMap Foundation |
| **Licence** | ODbL (Open Database License) |
| **Geographic coverage** | Global; Rajasthan has reasonable POI coverage |
| **Time coverage** | Current snapshot (continuously updated) |
| **Estimated records** | ~500–2000 tourism-tagged POIs in Rajasthan (to be verified) |
| **Available columns** | name, lat, lon, tourism/historic/leisure tags, opening_hours, fee, website, wikidata |
| **Missing values** | opening_hours (~80% missing), fee (~90% missing), descriptions (not in OSM) |
| **Access requirements** | Free, no API key; rate limits on public server |
| **Data type** | Observed (community-contributed geographic data) |
| **Suitability** | **HIGH** — primary source for attraction locations and categories |

### A2. Wikidata / Wikipedia

| Field | Value |
|---|---|
| **Dataset name** | Wikidata entities for Rajasthan tourist attractions |
| **URL** | https://query.wikidata.org |
| **Provider** | Wikimedia Foundation |
| **Licence** | CC0 (public domain) |
| **Geographic coverage** | Global; good coverage for notable Rajasthan landmarks |
| **Available columns** | name, description, coordinates, image, heritage status, inception date |
| **Data type** | Observed (crowd-sourced encyclopaedic data) |
| **Suitability** | **MEDIUM** — useful for enriching descriptions and images |

---

## B. Transportation Data

### B1. OpenRouteService (ORS) Directions API

| Field | Value |
|---|---|
| **Dataset name** | OpenRouteService routing |
| **URL** | https://openrouteservice.org/dev/#/api-docs |
| **Provider** | HeiGIT (Heidelberg Institute for Geoinformation Technology) |
| **Licence** | Free tier: 40 directions requests/min, 2000/day |
| **Transport modes** | Car, bicycle, foot, wheelchair |
| **Available columns** | distance (m), duration (s), geometry |
| **Missing** | No train or flight routing; no cost estimates |
| **Access requirements** | Free API key required |
| **Data type** | Computed from OSM road network |
| **Suitability** | **MEDIUM** — good for road distances; must supplement with train/flight data |

### B2. Indian Railways Data (via IRCTC/RailAPI estimates)

| Field | Value |
|---|---|
| **Dataset name** | Indian Railways route distances and durations |
| **URL** | Various; no single authoritative open API |
| **Provider** | Indian Railways / community datasets |
| **Missing** | No official open API for programmatic access |
| **Data type** | Would need manual compilation or community dataset |
| **Suitability** | **LOW-MEDIUM** — will use curated distance table for major routes |

### B3. CO₂ Emission Factors

| Field | Value |
|---|---|
| **Dataset name** | India-specific transport emission factors |
| **URL** | WRI India / India GHG Program: https://indiaghgp.org |
| **Provider** | WRI India, TERI, Shakti Foundation |
| **Licence** | Free for research use |
| **Emission factors** | Train: ~17 g CO₂/pkm, Bus: ~40 g CO₂/pkm, Car: ~150 g CO₂/pkm, Flight: ~130 g CO₂/pkm |
| **Data type** | Estimated (national averages from published methodology) |
| **Suitability** | **HIGH** — well-documented India-specific factors |

**Note:** These are national average estimates. Actual emissions depend on vehicle occupancy, fuel type, route, and electricity grid mix. We document these factors clearly in the application.

### B4. Great-Circle Distance for Flights

| Field | Value |
|---|---|
| **Dataset name** | Haversine formula for air distances |
| **Provider** | Standard geodetic calculation |
| **Data type** | Computed estimate |
| **Suitability** | **HIGH** — standard approach for flight emission estimation |

---

## C. Popularity Data

### C1. OSM Tag Counts and Metadata

| Field | Value |
|---|---|
| **Dataset name** | OSM POI metadata richness as popularity proxy |
| **Description** | Number of tags, presence of Wikipedia/Wikidata links, review tags |
| **Data type** | Heuristic proxy (not direct measure of visitor volume) |
| **Suitability** | **LOW-MEDIUM** — indirect indicator; better than nothing |

### C2. Google Trends (via pytrends)

| Field | Value |
|---|---|
| **Dataset name** | Google search interest index |
| **URL** | https://trends.google.com |
| **Provider** | Google |
| **Licence** | Free for personal use; ToS restrict automated bulk scraping |
| **Available columns** | Relative search interest (0–100) by region and time |
| **Data type** | Observed search behaviour (normalised index, not absolute counts) |
| **Suitability** | **MEDIUM** — useful as relative popularity signal; must respect rate limits |

### C3. Ministry of Tourism — Monument-wise Visitor Data (ASI)

| Field | Value |
|---|---|
| **Dataset name** | ASI Centrally Protected Ticketed Monuments visitor counts |
| **URL** | https://tourism.gov.in / India Tourism Data Compendium |
| **Provider** | Archaeological Survey of India via Ministry of Tourism |
| **Available columns** | Monument name, domestic visitors, foreign visitors (annual) |
| **Coverage** | ~100 centrally protected monuments nationally; ~10–15 in Rajasthan |
| **Data type** | Observed (official ticket sales data) |
| **Suitability** | **HIGH** — real visitor counts, but limited to ASI-ticketed monuments |

---

## D. Seasonal Tourism Data

### D1. Ministry of Tourism — State-wise Tourist Visits

| Field | Value |
|---|---|
| **Dataset name** | State-wise Domestic and Foreign Tourist Visits |
| **URL** | https://data.tourism.gov.in / https://tourism.gov.in |
| **Provider** | Ministry of Tourism, Government of India |
| **Licence** | Open Government Data |
| **Geographic coverage** | All Indian states including Rajasthan |
| **Temporal granularity** | Annual (some quarters available in compendium) |
| **Available columns** | State, year, domestic tourist visits, foreign tourist arrivals |
| **Data type** | Observed (official statistics) |
| **Suitability** | **MEDIUM** — annual data; monthly breakdown limited |

### D2. Rajasthan Tourism Department

| Field | Value |
|---|---|
| **Dataset name** | Rajasthan state tourism statistics |
| **URL** | https://tourism.rajasthan.gov.in |
| **Provider** | Department of Tourism, Government of Rajasthan |
| **Available** | Annual reports, some district-wise breakdowns |
| **Data type** | Observed |
| **Suitability** | **MEDIUM** — useful for state-level patterns |

### D3. Seasonal Demand Heuristic (Derived)

| Field | Value |
|---|---|
| **Description** | Monthly demand index derived from: (a) known peak/off-peak seasons from tourism literature, (b) weather comfort index, (c) holiday calendar |
| **Data type** | Heuristic estimate (explicitly labelled) |
| **Suitability** | **HIGH as documented heuristic** — transparent seasonal proxy |

---

## E. Weather and Calendar Data

### E1. Open-Meteo Historical Weather API

| Field | Value |
|---|---|
| **Dataset name** | ERA5/ERA5-Land historical weather reanalysis |
| **URL** | https://archive-api.open-meteo.com/v1/archive |
| **Provider** | Open-Meteo (backed by ECMWF ERA5) |
| **Licence** | Free for non-commercial use, no API key required |
| **Geographic coverage** | Global |
| **Temporal coverage** | 1940–present, hourly/daily resolution |
| **Available columns** | temperature_max, temperature_min, precipitation_sum, etc. |
| **Data type** | Observed (satellite/station reanalysis) |
| **Suitability** | **HIGH** — excellent free weather data for seasonal comfort index |

### E2. Indian Holiday Calendar

| Field | Value |
|---|---|
| **Dataset name** | Indian national and Rajasthan state holidays |
| **Provider** | Government gazette / compiled lists |
| **Data type** | Observed (official calendar) |
| **Suitability** | **HIGH** — straightforward to compile |

---

## F. Timestamped Crowd Data (Optional Extension)

### F1. Assessment

| Field | Value |
|---|---|
| **Status** | **No suitable open dataset found** |
| **Detail** | No publicly available attraction-level timestamped visitor count data for Indian attractions. ASI provides annual aggregates only. OBMS (Rajasthan) manages ticketing but does not publish time-series data. |
| **Decision** | Crowd forecasting will be marked as a **future extension**. Seasonal heuristics will be used as a transparent proxy. |

---

## Summary: Data Availability Matrix

| Data Category | Primary Source | Availability | Quality | Action |
|---|---|---|---|---|
| Attractions (location, category) | OSM Overpass API | ✅ Available | Good | Download via Overpass query |
| Attraction descriptions | Wikidata | ✅ Available | Partial | Enrich via Wikidata SPARQL |
| Road distances & times | OpenRouteService | ✅ Available | Good | Query ORS API (rate-limited) |
| Train distances & times | Manual compilation | ⚠️ Partial | Moderate | Compile for major routes |
| Flight distances | Haversine calculation | ✅ Available | Good | Compute from coordinates |
| CO₂ emission factors | WRI India / IEA | ✅ Available | Good | Use published factors |
| Popularity (visitor counts) | ASI / Ministry of Tourism | ⚠️ Partial | Good for covered monuments | Extract from compendium |
| Popularity (search interest) | Google Trends | ⚠️ Partial | Moderate | Query top attractions |
| Seasonal demand | Ministry of Tourism | ⚠️ Annual only | Moderate | Combine with seasonal heuristic |
| Weather | Open-Meteo | ✅ Available | Excellent | Query historical API |
| Holidays | Government calendar | ✅ Available | Excellent | Compile manually |
| Real-time crowd data | None found | ❌ Not available | — | Mark as future extension |

---

## Recommended Initial Data Pipeline

1. **Overpass API** → Extract ~100–200 major Rajasthan attractions with coordinates and categories
2. **Manual curation** → Add missing categories, descriptions, and interest tags for top attractions
3. **ORS + Haversine** → Compute distances from 5–6 major Indian cities to Rajasthan attraction clusters
4. **Emission factors** → Apply India-specific g CO₂/pkm by transport mode
5. **Open-Meteo** → Fetch monthly temperature and rainfall averages for Rajasthan cities
6. **Seasonal heuristic** → Define monthly demand index from tourism literature + weather comfort
7. **ASI data** → Extract annual visitor counts for ticketed Rajasthan monuments
