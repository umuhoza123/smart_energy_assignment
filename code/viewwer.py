import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected! Subscribing to energy/meters/#")
    client.subscribe("energy/meters/#")

def on_message(client, userdata, msg):
    print(f"\n{'='*60}")
    print(f"Topic: {msg.topic}")
    print(f"{'='*60}")
    
    # Parse and pretty-print JSON
    try:
        data = json.loads(msg.payload.decode())
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error parsing message: {e}")
        print(f"Raw payload: {msg.payload}")

# Use the new API version
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
print("MQTT Message Viewer - Waiting for messages...")
print("Press Ctrl+C to stop\n")
client.loop_forever()