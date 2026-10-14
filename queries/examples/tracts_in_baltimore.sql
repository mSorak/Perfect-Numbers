-- Question: How many census tracts are in Baltimore City, and what is their total land area?
-- Datasets: geo.tract (TIGER/Line 2024). Use aland_m2 (land), never polygon area (includes water).
SELECT count(*) AS n_tracts, round(sum(aland_m2) / 1e6, 1) AS land_km2
FROM geo.tract
WHERE county_geoid = '24510';
