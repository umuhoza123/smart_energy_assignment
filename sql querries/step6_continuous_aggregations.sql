DROP MATERIALIZED VIEW IF EXISTS energy_readings_15min CASCADE;

CREATE MATERIALIZED VIEW energy_readings_15min
WITH (timescaledb.continuous) AS
SELECT 
    meter_id,
    time_bucket('15 minutes', timestamp) AS bucket,
    AVG(power) as avg_power,
    MAX(power) as max_power,
    MIN(power) as min_power,
    SUM(energy) as total_energy,
    COUNT(*) as reading_count
FROM energy_readings
GROUP BY meter_id, bucket
WITH NO DATA;



DROP MATERIALIZED VIEW IF EXISTS energy_readings_hourly CASCADE;

CREATE MATERIALIZED VIEW energy_readings_hourly
WITH (timescaledb.continuous) AS
SELECT 
    meter_id,
    time_bucket('1 hour', timestamp) AS bucket,
    AVG(power) as avg_power,
    MAX(power) as max_power,
    MIN(power) as min_power,
    SUM(energy) as total_energy,
    COUNT(*) as reading_count
FROM energy_readings
GROUP BY meter_id, bucket
WITH NO DATA;


DROP MATERIALIZED VIEW IF EXISTS energy_readings_daily CASCADE;

CREATE MATERIALIZED VIEW energy_readings_daily
WITH (timescaledb.continuous) AS
SELECT 
    meter_id,
    time_bucket('1 day', timestamp) AS bucket,
    AVG(power) as avg_power,
    MAX(power) as max_power,
    MIN(power) as min_power,
    SUM(energy) as total_energy,
    COUNT(*) as reading_count
FROM energy_readings
GROUP BY meter_id, bucket
WITH NO DATA;


SELECT add_continuous_aggregate_policy('energy_readings_15min',
start_offset => INTERVAL '3 days',
end_offset => INTERVAL '1 hour',
schedule_interval => INTERVAL '15 minutes');



SELECT meter_id, time_bucket('15 minutes', timestamp) AS bucket,
AVG(power) as avg_power
FROM energy_readings
WHERE timestamp >= NOW() - INTERVAL '1 day'
AND meter_id = '1000000058'
GROUP BY meter_id, bucket
ORDER BY bucket;

SELECT meter_id, bucket, avg_power
FROM energy_readings_15min
WHERE bucket >= NOW() - INTERVAL '1 day'
AND meter_id = '1000000058'
ORDER BY bucket;



CALL refresh_continuous_aggregate('energy_readings_15min', NULL, NULL);
CALL refresh_continuous_aggregate('energy_readings_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('energy_readings_daily', NULL, NULL);

