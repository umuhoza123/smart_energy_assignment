"""
Step 3: Historical Data Loader
Generates 2 weeks of historical smart meter data and loads directly into PostgreSQL
This is FASTER than using MQTT and is meant for bulk data loading
"""

import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timedelta
import random
import math

# Database configuration
DB_CONFIG = {
    'dbname': 'smart_energy_grid',
    'user': 'postgres',
    'password': 'postgres123',  # Change this!
    'host': 'localhost',
    'port': 5432
}

# Configuration
NUM_METERS = 500
REPORTING_INTERVAL_MINUTES = 5
DAYS_OF_DATA = 14

class HistoricalDataLoader:
    def __init__(self):
        self.num_meters = NUM_METERS
        self.meters = self.generate_meter_ids()
        self.db_conn = None
        self.db_cursor = None
        
    def generate_meter_ids(self):
        """Generate unique 10-digit meter IDs"""
        meters = []
        for i in range(self.num_meters):
            meter_id = str(1000000000 + i).zfill(10)
            meters.append(meter_id)
        return meters
    
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            self.db_cursor = self.db_conn.cursor()
            print("✓ Connected to PostgreSQL database")
        except Exception as e:
            print(f"✗ Database connection error: {e}")
            raise
    
    def get_realistic_power(self, hour, meter_id):
        """
        Generate realistic power consumption based on time of day
        Higher usage during morning (6-9) and evening (17-22)
        Lower usage at night (23-5)
        """
        base_power = 1000  # Base power in watts
        
        # Time-based pattern
        if 6 <= hour < 9:  # Morning peak
            time_factor = 1.8 + random.uniform(-0.2, 0.2)
        elif 17 <= hour < 22:  # Evening peak
            time_factor = 2.0 + random.uniform(-0.2, 0.2)
        elif 23 <= hour or hour < 5:  # Night low
            time_factor = 0.4 + random.uniform(-0.1, 0.1)
        else:  # Mid-day
            time_factor = 1.2 + random.uniform(-0.2, 0.2)
        
        # Add some randomness per meter (consistent for each meter)
        meter_variation = 1 + (hash(meter_id) % 40 - 20) / 100  # ±20% variation
        
        # Add random noise
        noise = random.uniform(0.9, 1.1)
        
        power = base_power * time_factor * meter_variation * noise
        return max(100, power)  # Minimum 100W
    
    def generate_reading(self, meter_id, timestamp):
        """Generate a complete meter reading"""
        hour = timestamp.hour
        
        # Generate power
        power = self.get_realistic_power(hour, meter_id)
        
        # Generate voltage (around 230V ± 5%)
        voltage = 230 + random.uniform(-11.5, 11.5)
        
        # Calculate current from power and voltage (P = V * I)
        current = power / voltage
        
        # Frequency (50Hz ± 0.5Hz)
        frequency = 50 + random.uniform(-0.5, 0.5)
        
        # Energy in kWh for 5-minute interval
        energy = (power / 1000) * (REPORTING_INTERVAL_MINUTES / 60)
        
        return (
            meter_id,
            timestamp,
            round(power, 2),
            round(voltage, 2),
            round(current, 2),
            round(frequency, 2),
            round(energy, 4)
        )
    
    def verify_hypertable(self):
        """Check if energy_readings is a hypertable"""
        self.db_cursor.execute("""
            SELECT COUNT(*) 
            FROM timescaledb_information.hypertables 
            WHERE hypertable_name = 'energy_readings'
        """)
        is_hypertable = self.db_cursor.fetchone()[0] > 0
        
        if not is_hypertable:
            print("\n⚠ WARNING: energy_readings is not a hypertable!")
            print("Please run the following SQL first:")
            print("  SELECT create_hypertable('energy_readings', 'timestamp',")
            print("      chunk_time_interval => INTERVAL '1 day');")
            print()
            response = input("Continue anyway? (yes/no): ").strip().lower()
            if response != 'yes':
                raise Exception("Please convert to hypertable first")
        else:
            print("✓ Verified: energy_readings is a hypertable")
    
    def clear_existing_data(self):
        """Option to clear existing data"""
        self.db_cursor.execute("SELECT COUNT(*) FROM energy_readings")
        existing_rows = self.db_cursor.fetchone()[0]
        
        if existing_rows > 0:
            print(f"\n⚠ Found {existing_rows:,} existing rows in energy_readings")
            response = input("Delete existing data? (yes/no): ").strip().lower()
            if response == 'yes':
                print("Deleting existing data...")
                self.db_cursor.execute("TRUNCATE energy_readings")
                self.db_conn.commit()
                print("✓ Existing data cleared")
            else:
                print("Keeping existing data - new data will be appended")
    
    def generate_historical_data(self, days=14):
        """
        Generate and load historical data directly into database
        For 500 meters reporting every 5 minutes for 14 days:
        500 * 288 readings/day * 14 days = 2,016,000 readings
        """
        print(f"\n{'='*60}")
        print(f"HISTORICAL DATA LOADER")
        print(f"{'='*60}")
        print(f"Meters: {self.num_meters}")
        print(f"Period: {days} days")
        print(f"Interval: {REPORTING_INTERVAL_MINUTES} minutes")
        
        readings_per_day = (24 * 60) // REPORTING_INTERVAL_MINUTES  # 288
        total_expected = self.num_meters * readings_per_day * days
        print(f"Expected rows: {total_expected:,}")
        print(f"{'='*60}\n")
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        print(f"Time range: {start_time} to {end_time}")
        print(f"Starting data generation...\n")
        
        # Prepare insert query
        insert_query = """
            INSERT INTO energy_readings 
            (meter_id, timestamp, power, voltage, current, frequency, energy)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        # Generate and insert data in batches
        batch_size = 10000  # Insert 10,000 rows at a time
        batch = []
        total_inserted = 0
        current_time = start_time
        
        try:
            while current_time < end_time:
                # Generate readings for all meters at this timestamp
                for meter_id in self.meters:
                    reading = self.generate_reading(meter_id, current_time)
                    batch.append(reading)
                    
                    # Insert batch when it reaches batch_size
                    if len(batch) >= batch_size:
                        execute_batch(self.db_cursor, insert_query, batch)
                        self.db_conn.commit()
                        total_inserted += len(batch)
                        
                        # Progress update
                        progress = (total_inserted / total_expected) * 100
                        print(f"Progress: {progress:6.2f}% | Inserted: {total_inserted:,} rows | "
                              f"Current time: {current_time.strftime('%Y-%m-%d %H:%M')}")
                        
                        batch = []
                
                # Move to next interval
                current_time += timedelta(minutes=REPORTING_INTERVAL_MINUTES)
            
            # Insert remaining batch
            if batch:
                execute_batch(self.db_cursor, insert_query, batch)
                self.db_conn.commit()
                total_inserted += len(batch)
            
            print(f"\n{'='*60}")
            print(f"✓ DATA LOADING COMPLETE!")
            print(f"{'='*60}")
            print(f"Total rows inserted: {total_inserted:,}")
            print(f"Expected rows: {total_expected:,}")
            print(f"{'='*60}\n")
            
            # Verify final count
            self.verify_data_loaded()
            
        except Exception as e:
            print(f"\n✗ Error during data loading: {e}")
            self.db_conn.rollback()
            raise
    
    def verify_data_loaded(self):
        """Verify data was loaded correctly"""
        print("Verifying data...")
        
        # Total count
        self.db_cursor.execute("SELECT COUNT(*) FROM energy_readings")
        total_count = self.db_cursor.fetchone()[0]
        print(f"  Total rows: {total_count:,}")
        
        # Date range
        self.db_cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp) 
            FROM energy_readings
        """)
        min_date, max_date = self.db_cursor.fetchone()
        print(f"  Date range: {min_date} to {max_date}")
        
        # Unique meters
        self.db_cursor.execute("""
            SELECT COUNT(DISTINCT meter_id) 
            FROM energy_readings
        """)
        unique_meters = self.db_cursor.fetchone()[0]
        print(f"  Unique meters: {unique_meters}")
        
        # Sample data
        self.db_cursor.execute("""
            SELECT meter_id, timestamp, power, voltage, current, frequency, energy
            FROM energy_readings
            ORDER BY timestamp DESC
            LIMIT 3
        """)
        print(f"\n  Sample readings:")
        for row in self.db_cursor.fetchall():
            print(f"    {row}")
        
        # Check chunks
        self.db_cursor.execute("""
            SELECT COUNT(*) 
            FROM timescaledb_information.chunks 
            WHERE hypertable_name = 'energy_readings'
        """)
        chunk_count = self.db_cursor.fetchone()[0]
        print(f"\n  Number of chunks created: {chunk_count}")
        
        print("\n✓ Verification complete!")
    
    def cleanup(self):
        """Clean shutdown"""
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_conn:
            self.db_conn.close()
        print("\n✓ Database connection closed")

def main():
    loader = HistoricalDataLoader()
    
    try:
        # Connect to database
        loader.connect_db()
        
        # Verify hypertable exists
        loader.verify_hypertable()
        
        # Option to clear existing data
        loader.clear_existing_data()
        
        # Confirm before proceeding
        print(f"\nReady to generate {DAYS_OF_DATA} days of historical data")
        print(f"This will insert approximately 2 million rows")
        print(f"Estimated time: 5-10 minutes\n")
        
        response = input("Proceed? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Cancelled by user")
            return
        
        # Generate and load data
        loader.generate_historical_data(days=DAYS_OF_DATA)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Data loading interrupted by user")
        loader.db_conn.rollback()
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        loader.cleanup()

if __name__ == '__main__':
    main()