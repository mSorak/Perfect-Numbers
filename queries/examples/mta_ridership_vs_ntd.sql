-- Question: Do the MTA dashboard's monthly bus ridership totals agree with what MTA reports to the
--           National Transit Database?
-- Datasets: transit.mta_ridership_route_month (CX dashboard), transit.ntd_monthly
WITH cx AS (
    SELECT month, sum(riders) AS cx_bus_riders
    FROM transit.mta_ridership_route_month
    WHERE mode_id = 1            -- 'Core Bus' (local bus incl. CityLink/LocalLink) in the CX data model
    GROUP BY 1),
ntd AS (
    SELECT month, sum(unlinked_trips) AS ntd_bus_upt
    FROM transit.ntd_monthly
    WHERE ntd_id = '30034' AND mode = 'MB'
    GROUP BY 1)
SELECT month, cx_bus_riders, ntd_bus_upt, round(cx_bus_riders / ntd_bus_upt, 3) AS ratio
FROM cx JOIN ntd USING (month)
ORDER BY month DESC
LIMIT 24;
