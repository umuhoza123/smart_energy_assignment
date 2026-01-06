"""
Enhanced MQTT Subscriber for Energy Readings
Fixed keep-alive timeout issues
"""

import json
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'dbname': 'smart_energy_grid',
    'user': 'postgres',
    'password': 'postgres123',
    'host': 'localhost',
    'port': 5432
}

# MQTT configuration
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC = 'energy/meters/#'
MQTT_KEEPALIVE = 3600  # 1 hour (increased from default 60 seconds)

class EnergyDataSubscriber:
    def __init__(self):
        self.db_conn = None
        self.db_cursor = None
        self.message_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
        self.reconnect_count = 0
        self.connect_db()
        # Fix deprecation warning and set client ID
        self.mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="energy_subscriber"
        )
        self.setup_mqtt()
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            self.db_cursor = self.db_conn.cursor()
            # Enable autocommit for better performance
            self.db_conn.autocommit = True
            
            print("=" * 70)
            print("📡 ENERGY DATA SUBSCRIBER - ENHANCED VERSION v2")
            print("=" * 70)
            print("✓ Connected to PostgreSQL database")
            
            # Check current count
            self.db_cursor.execute("SELECT COUNT(*) FROM energy_readings")
            count = self.db_cursor.fetchone()[0]
            print(f"✓ Current records in database: {count:,}")
        except Exception as e:
            print(f"✗ Database connection error: {e}")
            raise
    
    def setup_mqtt(self):
        """Setup MQTT client callbacks"""
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe(MQTT_TOPIC)
            print(f"✓ Subscribed to topic: {MQTT_TOPIC}")
            if self.reconnect_count > 0:
                print(f"✓ Reconnected (reconnection #{self.reconnect_count})")
            print("=" * 70)
            print("📊 Waiting for messages... (Press Ctrl+C to stop)")
            print("=" * 70)
            print()
        else:
            print(f"✗ Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, flags, rc, properties=None):
        """Callback when disconnected from MQTT broker"""
        if rc != 0:
            self.reconnect_count += 1
            print(f"\n⚠ Disconnected from MQTT broker (code: {rc})")
            print(f"⟳ Auto-reconnecting... (attempt #{self.reconnect_count})")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            # Parse JSON message
            data = json.loads(msg.payload.decode())
            
            # Get meter_id from JSON payload
            meter_id = data.get('meter_id')
            
            if not meter_id:
                print(f"✗ Missing meter_id in message")
                self.error_count += 1
                return
            
            # Insert data into database (autocommit is enabled)
            insert_query = """
                INSERT INTO energy_readings 
                (meter_id, timestamp, power, voltage, current, frequency, energy)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                meter_id,
                data.get('timestamp', datetime.now()),
                data.get('power'),
                data.get('voltage'),
                data.get('current'),
                data.get('frequency'),
                data.get('energy')
            )
            
            self.db_cursor.execute(insert_query, values)
            # No need to commit - autocommit is enabled
            
            self.message_count += 1
            
            # Progress updates
            if self.message_count % 1000 == 0:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate = self.message_count / elapsed if elapsed > 0 else 0
                print(f"📊 Progress: {self.message_count:,} messages | "
                      f"Rate: {rate:.1f} msg/sec | "
                      f"Errors: {self.error_count} | "
                      f"Reconnects: {self.reconnect_count}")
            elif self.message_count % 100 == 0:
                print(f"✓ {self.message_count:,} messages stored", end='\r')
            
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON decode error: {e}")
            self.error_count += 1
        except Exception as e:
            print(f"\n✗ Error processing message: {e}")
            self.error_count += 1
    
    def start(self):
        """Start the subscriber"""
        try:
            # Connect with extended keep-alive timeout
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            print(f"✓ MQTT keep-alive timeout: {MQTT_KEEPALIVE} seconds")
            
            # Enable automatic reconnection
            self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)
            
            self.mqtt_client.loop_forever(retry_first_connection=True)
        except KeyboardInterrupt:
            print("\n\n⚠ Stopping subscriber...")
            self.stop()
        except Exception as e:
            print(f"\n✗ Error: {e}")
            self.stop()
    
    def stop(self):
        """Clean shutdown with statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"Messages stored: {self.message_count:,}")
        print(f"Errors encountered: {self.error_count}")
        print(f"Reconnections: {self.reconnect_count}")
        print(f"Runtime: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        
        if elapsed > 0:
            print(f"Average rate: {self.message_count / elapsed:.1f} messages/second")
        
        # Get final database count
        try:
            self.db_cursor.execute("SELECT COUNT(*) FROM energy_readings")
            final_count = self.db_cursor.fetchone()[0]
            print(f"Total in database: {final_count:,}")
        except:
            pass
        
        print("=" * 70)
        
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_conn:
            self.db_conn.close()
            
        print("✓ Subscriber stopped cleanly")

if __name__ == '__main__':
    subscriber = EnergyDataSubscriber()
    subscriber.start()