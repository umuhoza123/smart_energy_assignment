CREATE DATABASE smart_energy_grid;

-- Connect to the database
\c smart_energy_grid

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create the initial regular PostgreSQL table
CREATE TABLE energy_readings (
    meter_id VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    power DOUBLE PRECISION,
    voltage DOUBLE PRECISION,
    current DOUBLE PRECISION,
    frequency DOUBLE PRECISION,
    energy DOUBLE PRECISION
);

-- Create index for better query performance
CREATE INDEX idx_energy_readings_timestamp ON energy_readings(timestamp DESC);
CREATE INDEX idx_energy_readings_meter_id ON energy_readings(meter_id);

-- Verify table creation
\dt
