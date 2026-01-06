SELECT 
    hypertable_name,
    pg_size_pretty(hypertable_size(format('%I', hypertable_name)::regclass)) as size
FROM timescaledb_information.hypertables
WHERE hypertable_name LIKE 'energy_readings%'
ORDER BY hypertable_name;

SELECT 
    time_bucket('15 minutes', timestamp) AS period,
    AVG(power) as avg_power
FROM energy_readings_week
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY period 
ORDER BY avg_power DESC 
LIMIT 10;

SELECT meter_id,
DATE_TRUNC('month', timestamp) as month,
SUM(energy) as total_energy
FROM energy_readings_week
GROUP BY meter_id, month
ORDER BY month, total_energy DESC;

--each table

SELECT hypertable_name,
pg_size_pretty(hypertable_size(format('%I',
hypertable_name)::regclass))
FROM timescaledb_information.hypertables;



-- Query 2: Find peak consumption periods in the past week
SELECT time_bucket('15 minutes', timestamp) AS period,
AVG(power) as avg_power
FROM energy_readings
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY period ORDER BY avg_power DESC LIMIT 10;
-- Query 3: Monthly consumption per meter
SELECT meter_id,
DATE_TRUNC('month', timestamp) as month,
SUM(energy) as total_energy
FROM energy_readings
GROUP BY meter_id, month
ORDER BY month, total_energy DESC;

SELECT remove_compression_policy('energy_readings');
SELECT decompress_chunk(show_chunks)
FROM show_chunks('energy_readings', older_than => INTERVAL '0');


SELECT chunk_name, is_compressed
FROM timescaledb_information.chunks
WHERE hypertable_name = 'energy_readings';



ALTER TABLE energy_readings
SET (
  timescaledb.compress,
  timescaledb.compress_orderby = 'timestamp DESC',
  timescaledb.compress_segmentby = 'meter_id'
);

-- 5. Re-add policy
SELECT add_compression_policy('energy_readings', INTERVAL '24 hours');


---2----


ALTER TABLE energy_readings_3h
SET (
  timescaledb.compress,
  timescaledb.compress_orderby = 'timestamp DESC',
  timescaledb.compress_segmentby = 'meter_id'
);

SELECT add_compression_policy('energy_readings_3h', INTERVAL '24 hours');




-----3---

ALTER TABLE energy_readings_week
SET (
  timescaledb.compress,
  timescaledb.compress_orderby = 'timestamp DESC',
  timescaledb.compress_segmentby = 'meter_id'
);

SELECT add_compression_policy('energy_readings_week', INTERVAL '24 hours');






SELECT hypertable_name,
       pg_size_pretty(hypertable_size(format('%I', hypertable_name)::regclass)) AS total_size
FROM timescaledb_information.hypertables
WHERE hypertable_name IN ('energy_readings','energy_readings_3h','energy_readings_week')
ORDER BY hypertable_name;






-- For the 1-day chunk hypertable
ALTER TABLE energy_readings SET (timescaledb.compress,
timescaledb.compress_orderby = 'timestamp DESC');
SELECT add_compression_policy('energy_readings', INTERVAL '24
hours');
-- Do the same for the other two hypertables

