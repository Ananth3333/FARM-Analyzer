import psycopg2
import time
import random

def get_db_connection():
    return psycopg2.connect(
        host="localhost", database="Platform_DB", user="postgres", password="Ananth@3333", port="5432"
    )

print("[SIMULATOR] Generating high-frequency metrics... Press Ctrl+C to halt.")

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    base_temp, base_hum = 25.0, 56.0
    
    # FIXED: Uses an ultra-high starting sequence to prevent database collision blocks!
    sequence = int(time.time()) - 1700000000 

    while True:
        sequence += 1
        current_temp = max(16.0, min(40.0, base_temp + random.uniform(-0.4, 0.4)))
        current_hum = max(25.0, min(90.0, base_hum + random.uniform(-0.7, 0.7)))
        base_temp, base_hum = current_temp, current_hum

        sql_query = """
            INSERT INTO public.sensor_readings (node_id, seq_num, temperature, humidity, hop_count)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (node_id, seq_num) DO NOTHING;
        """
        cursor.execute(sql_query, (1, sequence, round(current_temp, 2), round(current_hum, 2), 1))
        conn.commit()
        
        print(f"[DATA PACKET INJECTED] Seq: {sequence} | Temp: {current_temp:.2f}°C | Hum: {current_hum:.2f}%")
        time.sleep(200)
except KeyboardInterrupt:
    print("\n[SIMULATOR] Paused.")
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()
