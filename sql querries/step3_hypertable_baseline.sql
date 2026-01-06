--1. Convert your PostgreSQL table to a TimescaleDB hypertable with exactly these commands:
SELECT create_hypertable('energy_readings', 'timestamp',
chunk_time_interval => INTERVAL '1 day');

---- CORRECT ---

-- Step 1: Rename old table
ALTER TABLE energy_readings RENAME TO energy_readings_old;

-- Step 2: Create new table with TEXT type
CREATE TABLE energy_readings (
    meter_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    power DECIMAL(10, 2) NOT NULL,
    voltage DECIMAL(6, 2) NOT NULL,
    current DECIMAL(8, 2) NOT NULL,
    frequency DECIMAL(5, 2) NOT NULL,
    energy DECIMAL(10, 4) NOT NULL

);

-- Step 3: Convert to hypertable FIRST (before inserting data)
SELECT create_hypertable('energy_readings', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    migrate_data => true);

-- Step 4: Migrate data from old table
INSERT INTO energy_readings (meter_id, timestamp, power, voltage, current, frequency, energy)
SELECT 
    meter_id::TEXT,
    timestamp::TIMESTAMPTZ,
    power,
    voltage,
    current,
    frequency,
    energy

FROM energy_readings_old;

-- Step 5: Verify migration
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT meter_id) as unique_meters,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest
FROM energy_readings;

-- Step 6: Create indexes
CREATE INDEX idx_meter_id ON energy_readings(meter_id, timestamp DESC);
CREATE INDEX idx_timestamp ON energy_readings(timestamp DESC);

-- Step 7: Drop old table (after verifying data)
DROP TABLE energy_readings_old;

-- Verify hypertable
SELECT * FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'energy_readings';