"""
Step 1: MQTT Subscriber for Energy Readings
This program subscribes to energy/meters/# topic and stores data in PostgreSQL
"""

import json
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'dbname': 'smart_energy_grid',
    'user': 'postgres',
    'password': 'postgres123',  # Change this!
    'host': 'localhost',
    'port': 5432
}

# MQTT configuration
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC = 'energy/meters/#'

class EnergyDataSubscriber:
    def __init__(self):
        self.db_conn = None
        self.db_cursor = None
        self.connect_db()
        self.mqtt_client = mqtt.Client()
        self.setup_mqtt()
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            self.db_cursor = self.db_conn.cursor()
            print("✓ Connected to PostgreSQL database")
        except Exception as e:
            print(f"✗ Database connection error: {e}")
            raise
    
    def setup_mqtt(self):
        """Setup MQTT client callbacks"""
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe(MQTT_TOPIC)
            print(f"✓ Subscribed to topic: {MQTT_TOPIC}")
        else:
            print(f"✗ Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        print(f"⚠ Disconnected from MQTT broker (code: {rc})")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            # Parse JSON message
            data = json.loads(msg.payload.decode())
            
            # Extract meter_id from topic
            topic_parts = msg.topic.split('/')
            meter_id = topic_parts[-1]
            
            # Insert data into database
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
            self.db_conn.commit()
            
            print(f"✓ Stored data from meter {meter_id} - Power: {data.get('power')} W")
            
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
        except Exception as e:
            print(f"✗ Error processing message: {e}")
            self.db_conn.rollback()
    
    def start(self):
        """Start the subscriber"""
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print("\n📡 Energy Data Subscriber Started")
            print("Waiting for messages... (Press Ctrl+C to stop)\n")
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            print("\n⚠ Stopping subscriber...")
            self.stop()
        except Exception as e:
            print(f"✗ Error: {e}")
            self.stop()
    
    def stop(self):
        """Clean shutdown"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_conn:
            self.db_conn.close()
        print("✓ Subscriber stopped")

if __name__ == '__main__':
    subscriber = EnergyDataSubscriber()
    subscriber.start()