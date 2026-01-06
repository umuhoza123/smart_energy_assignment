-- Step 4: Chunk Interval Experimentation

-- 1. Create additional test tables with different chunk intervals

-- 3-hour chunks table
CREATE TABLE energy_readings_3h (LIKE energy_readings INCLUDING ALL);

SELECT create_hypertable('energy_readings_3h', 'timestamp',
    chunk_time_interval => INTERVAL '3 hours');

-- 1-week chunks table
CREATE TABLE energy_readings_week (LIKE energy_readings INCLUDING ALL);

SELECT create_hypertable('energy_readings_week', 'timestamp',
    chunk_time_interval => INTERVAL '1 week');

-- 2. Copy data from original table to test tables
-- This will take some time...

INSERT INTO energy_readings_3h 
SELECT * FROM energy_readings;

INSERT INTO energy_readings_week 
SELECT * FROM energy_readings;

-- Verify data copied
SELECT 'energy_readings' as table_name, COUNT(*) as row_count FROM energy_readings
UNION ALL
SELECT 'energy_readings_3h', COUNT(*) FROM energy_readings_3h
UNION ALL
SELECT 'energy_readings_week', COUNT(*) FROM energy_readings_week;



3: -- Query 1: Average power consumption per hour today
SELECT time_bucket('1 hour', timestamp) AS hour,
       AVG(power) as avg_power
FROM energy_readings_3h
WHERE timestamp >= DATE_TRUNC('day', NOW())
GROUP BY hour ORDER BY hour

-- Query 2: Find peak consumption periods in the past week
SELECT time_bucket('15 minutes', timestamp) AS period,
       AVG(power) as avg_power
FROM energy_readings_3h
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY period ORDER BY avg_power DESC LIMIT 10;

-- Query 3: Monthly consumption per meter
SELECT meter_id,
       DATE_TRUNC('month', timestamp) as month,
       SUM(energy) as total_energy
FROM energy_readings_3h
GROUP BY meter_id, month
ORDER BY month, total_energy DESC;

-- Query 4: Full dataset scan
SELECT COUNT(*), AVG(power), MAX(power), MIN(power)
FROM energy_readings_3h;  


-- weely 

SELECT time_bucket('1 hour', timestamp) AS hour,
       AVG(power) AS avg_power
FROM energy_readings_week
WHERE timestamp >= DATE_TRUNC('day', NOW())
GROUP BY hour
ORDER BY hour;
-- Query 2: Find peak consumption periods in the past week
SELECT time_bucket('15 minutes', timestamp) AS period,
       AVG(power) AS avg_power
FROM energy_readings_week
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY period
ORDER BY avg_power DESC
LIMIT 10;

-- Query 3: Monthly consumption per meter
SELECT meter_id,
       DATE_TRUNC('month', timestamp) AS month,
       SUM(energy) AS total_energy
FROM energy_readings_week
GROUP BY meter_id, month
ORDER BY month, total_energy DESC;

-- Query 4: Full dataset scan

SELECT COUNT(*) AS total_rows,
       AVG(power) AS avg_power,
       MAX(power) AS max_power,
       MIN(power) AS min_power
FROM energy_readings_week;




-- 3. View chunk distribution for each hypertable

-- 3-hour chunks
SELECT 'energy_readings_3h' as hypertable,
       chunk_schema, 
       chunk_name, 
       range_start, 
       range_end,
       pg_size_pretty(pg_total_relation_size(format('%I.%I',
           chunk_schema, chunk_name)::regclass)) as chunk_size
FROM timescaledb_information.chunks
WHERE hypertable_name = 'energy_readings_3h'
ORDER BY range_start;

-- 1-day chunks
SELECT 'energy_readings' as hypertable,
       chunk_schema, 
       chunk_name, 
       range_start, 
       range_end,
       pg_size_pretty(pg_total_relation_size(format('%I.%I',
           chunk_schema, chunk_name)::regclass)) as chunk_size
FROM timescaledb_information.chunks
WHERE hypertable_name = 'energy_readings'
ORDER BY range_start;

-- 1-week chunks
SELECT 'energy_readings_week' as hypertable,
       chunk_schema, 
       chunk_name, 
       range_start, 
       range_end,
       pg_size_pretty(pg_total_relation_size(format('%I.%I',
           chunk_schema, chunk_name)::regclass)) as chunk_size
FROM timescaledb_information.chunks
WHERE hypertable_name = 'energy_readings_week'
ORDER BY range_start;

-- Count chunks for each hypertable
SELECT hypertable_name, COUNT(*) as num_chunks
FROM timescaledb_information.chunks
GROUP BY hypertable_name
ORDER BY hypertable_name;










-- Query 1: Average power consumption per hour today
SELECT time_bucket('1 hour', timestamp) AS hour,
AVG(power) as avg_power
FROM energy_readings
WHERE timestamp >= DATE_TRUNC('day', NOW())
GROUP BY hour ORDER BY hour;
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
-- Query 4: Full dataset scan
SELECT COUNT(*), AVG(power), MAX(power), MIN(power)
FROM energy_readings;