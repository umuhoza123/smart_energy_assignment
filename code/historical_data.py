import os
from datetime import datetime, timedelta
import random
import csv

# ---------------- CONFIG ----------------
NUM_METERS = 1042                 # ≈ 4.2M rows total
DAYS_OF_DATA = 14
INTERVAL_MINUTES = 5

MAX_CSV_ROWS = 1_000_000          # rows per CSV file
EXPORT_DIR = r"C:\Users\SURFACE\Desktop\datanifi\smart_energy\csv_exports"

HEADERS = [
    "meter_id",
    "timestamp",
    "power",
    "voltage",
    "current",
    "frequency",
    "energy"
]

os.makedirs(EXPORT_DIR, exist_ok=True)
# ----------------------------------------


def generate_meter_ids(n):
    return [str(1000000000 + i).zfill(10) for i in range(n)]


def get_realistic_power(hour):
    if 6 <= hour < 9:
        return random.uniform(1500, 2200)
    elif 17 <= hour < 22:
        return random.uniform(1800, 2500)
    elif hour < 5:
        return random.uniform(300, 600)
    return random.uniform(800, 1500)


def generate_row(meter_id, ts):
    power = get_realistic_power(ts.hour)
    voltage = random.uniform(220, 240)
    current = power / voltage
    frequency = random.uniform(49.5, 50.5)
    energy = (power / 1000) * (INTERVAL_MINUTES / 60)

    return [
        meter_id,
        ts.strftime("%Y-%m-%d %H:%M:%S"),   # PostgreSQL-safe timestamp
        round(power, 2),
        round(voltage, 2),
        round(current, 2),
        round(frequency, 2),
        round(energy, 4)
    ]


def export_to_csv():
    meters = generate_meter_ids(NUM_METERS)
    start = datetime.now() - timedelta(days=DAYS_OF_DATA)
    end = datetime.now()

    file_index = 1
    rows_in_file = 0
    total_rows = 0

    def open_new_file(index):
        path = os.path.join(EXPORT_DIR, f"energy_readings_{index:03d}.csv")
        f = open(path, mode="w", newline="", encoding="utf-8")
        w = csv.writer(f)
        w.writerow(HEADERS)
        return f, w

    csv_file, writer = open_new_file(file_index)

    ts = start
    while ts < end:
        for meter in meters:
            writer.writerow(generate_row(meter, ts))
            rows_in_file += 1
            total_rows += 1

            if rows_in_file >= MAX_CSV_ROWS:
                csv_file.close()
                print(f"Saved energy_readings_{file_index:03d}.csv ({rows_in_file:,} rows)")

                file_index += 1
                rows_in_file = 0
                csv_file, writer = open_new_file(file_index)

        ts += timedelta(minutes=INTERVAL_MINUTES)

    csv_file.close()
    print(f"\nDONE — Total rows generated: {total_rows:,}")


if __name__ == "__main__":
    export_to_csv()
