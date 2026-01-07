"""
Step 2: Smart Meter Data Simulator
Generates realistic energy consumption daata for 500+ meters
"""

import json
import random
import time
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import math

# Configuration
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
NUM_METERS = 5000
REPORTING_INTERVAL = 300  # 5 minutes in seconds

class SmartMeterSimulator:
    def __init__(self, num_meters=500):
        self.num_meters = num_meters
        self.meters = self.generate_meter_ids()
        self.mqtt_client = mqtt.Client()
        self.connect_mqtt()
        
    def generate_meter_ids(self):
        """Generate unique 10-digit meter IDs"""
        meters = []
        for i in range(self.num_meters):
            # Generate 10-digit number (e.g., 1234567890)
            meter_id = str(1000000000 + i).zfill(10)
            meters.append(meter_id)
        return meters
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        except Exception as e:
            print(f"✗ MQTT connection error: {e}")
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
        
        # Add some randomness per meter
        meter_variation = 1 + (hash(meter_id) % 40 - 20) / 100  # ±20% variation
        
        # Add random noise
        noise = random.uniform(0.9, 1.1)
        
        power = base_power * time_factor * meter_variation * noise
        return max(100, power)  # Minimum 100W
    
    def generate_reading(self, meter_id, timestamp):
        """Generate a complete meter reading - INCLUDES meter_id in JSON"""
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
        energy = (power / 1000) * (5 / 60)  # Convert to kWh
        
        return {
            'meter_id': meter_id,  # ✓ IMPORTANT: Include meter_id in JSON payload
            'timestamp': timestamp.isoformat(),
            'power': round(power, 2),
            'voltage': round(voltage, 2),
            'current': round(current, 2),
            'frequency': round(frequency, 2),
            'energy': round(energy, 4)
        }
    
    def publish_reading(self, meter_id, reading):
        """Publish reading to MQTT"""
        topic = f'energy/meters/{meter_id}'
        payload = json.dumps(reading)
        self.mqtt_client.publish(topic, payload)
    
    def simulate_realtime(self, duration_hours=1):
        """
        Simulate real-time data generation for specified duration
        For testing: 1 hour = 12 readings per meter
        """
        print(f"\n Starting real-time simulation for {duration_hours} hour(s)")
        print(f"N1umber of meters: {self.num_meters}")
        print(f"Reporting interval: {REPORTING_INTERVAL} seconds (5 minutes)")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        current_time = start_time
        
        reading_count = 0
        
        while current_time < end_time:
            print(f"\n Generating readings for {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            for meter_id in self.meters:
                reading = self.generate_reading(meter_id, current_time)
                self.publish_reading(meter_id, reading)
                reading_count += 1
            
            print(f"✓ Published {len(self.meters)} readings (Total: {reading_count})")
            
            # Move to next interval
            current_time += timedelta(seconds=REPORTING_INTERVAL)
            
            # Wait for next interval (for real-time simulation)
            # Comment out time.sleep() for faster historical data generation
            if current_time < end_time:
                time.sleep(5)  # Wait 5 seconds instead of 300 for faster testing
        
        print(f"\n✓ Simulation complete! Total readings: {reading_count}")
    
    def generate_historical_data(self, days=14):
        """
        Generate historical data for specified number of days
        For 500 meters reporting every 5 minutes for 14 days:
        500 * 288 readings/day * 14 days = 2,016,000 readings
        """
        print(f"\n Generating {days} days of historical data")
        print(f"Number of meters: {self.num_meters}")
        print(f"Expected readings: ~{self.num_meters * 288 * days:,}")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        current_time = start_time
        
        reading_count = 0
        batch_size = 1000
        
        while current_time < end_time:
            for meter_id in self.meters:
                reading = self.generate_reading(meter_id, current_time)
                self.publish_reading(meter_id, reading)
                reading_count += 1
                
                # Progress update
                if reading_count % batch_size == 0:
                    progress = ((current_time - start_time) / (end_time - start_time)) * 100
                    print(f"Progress: {progress:.1f}% - {reading_count:,} readings")
            
            current_time += timedelta(seconds=REPORTING_INTERVAL)
            time.sleep(0.01)  # Small delay to prevent overwhelming the broker
        
        print(f"\n✓ Historical data generation complete!")
        print(f"Total readings generated: {reading_count:,}")
    
    def cleanup(self):
        """Clean shutdown"""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        print("Simulator stopped")

def main():
    print("=" * 60)
    print("SMART METER DATA SIMULATOR")
    print("=" * 60)
    
    simulator = SmartMeterSimulator(num_meters=NUM_METERS)
    
    print("\nSelect mode:")
    print("1. Real-time simulation (1 hour for testing)")
    print("2. Generate historical data (14 days)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    try:
        if choice == '1':
            simulator.simulate_realtime(duration_hours=1)
        elif choice == '2':
            simulator.generate_historical_data(days=28)
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\n\n⚠ Simulation interrupted by user")
    finally:
        simulator.cleanup()

if __name__ == '__main__':
    main()
