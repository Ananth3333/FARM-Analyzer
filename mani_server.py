import socket
import struct
import psycopg2
from datetime import datetime

# =====================================================================
# 1. NETWORK CAPTURE BOUNDARIES & FILTER STORAGE
# =====================================================================
SERVER_IP = "0.0.0.0"       # Listen on all local and external interfaces
SERVER_PORT = 5005          # UDP port matching your RW612 transmitter
EXPECTED_SIZE = 12          # Strict boundary: 12-byte packed framework packet size

last_seen_sequences = {}

# =====================================================================
# 2. SYSTEM DATABASE INITIALIZATION & SCHEMA BOOTSTRAP
# =====================================================================
def initialize_mani_storage():
    print("[MANI SYSTEM] Activating data warehouse bootloader...")
    
    # FIXED DEFINITIVELY: Uses template1 to bypass the missing postgres container issue
    admin_conn = psycopg2.connect(
        host="localhost", 
        database="template1", 
        user="postgres", 
        password="Ananth@3333", 
        port="5432"
    )
    admin_conn.autocommit = True
    admin_cursor = admin_conn.cursor()
    
    # Check and generate containers matching your case-sensitive pgAdmin names
    for db_name in ["Platform_DB", "VLM_DB"]:
        admin_cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
        if not admin_cursor.fetchone():
            admin_cursor.execute(f'CREATE DATABASE "{db_name}";')
            print(f"[DATABASE] Container '{db_name}' successfully verified/created.")
            
    admin_cursor.close()
    admin_conn.close()

    # Define optimized single-precision schemas matching your 12-byte raw frame
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS public.sensor_readings (
        timestamp_column TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        node_id INT NOT NULL,               
        seq_num INT NOT NULL,               
        temperature REAL NOT NULL,          
        humidity REAL NOT NULL,             
        hop_count INT NOT NULL,             
        CONSTRAINT pk_node_sequence PRIMARY KEY (node_id, seq_num)
    );
    CREATE INDEX IF NOT EXISTS idx_mani_time ON public.sensor_readings (timestamp_column DESC);
    """

    # Apply database schema structures directly to both target containers
    for db_target in ["Platform_DB", "VLM_DB"]:
        conn = psycopg2.connect(host="localhost", database=db_target, user="postgres", password="Ananth@3333", port="5432")
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        cursor.close()
        conn.close()
        
    print("[MANI SYSTEM] Telemetry schemas cleanly integrated across databases.\n")

# =====================================================================
# 3. CORE RECEIVE, VALIDATE, DECODE, & UPDATE PIPELINE
# =====================================================================
def run_processing_pipeline():
    initialize_mani_storage()
    
    # Explicitly connect to your case-sensitive pgAdmin storage layers
    conn_platform = psycopg2.connect(host="localhost", database="Platform_DB", user="postgres", password="Ananth@3333", port="5432")
    cursor_platform = conn_platform.cursor()
    
    conn_vlm = psycopg2.connect(host="localhost", database="VLM_DB", user="postgres", password="Ananth@3333", port="5432")
    cursor_vlm = conn_vlm.cursor()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    
    print(f"🚀 MANI Core Engine Active! Listening for data bytes on port {SERVER_PORT}...")
    
    while True:
        try:
            raw_bytes, addr = server_socket.recvfrom(1024)
            
            if len(raw_bytes) != EXPECTED_SIZE:
                continue
                
            format_mask = '<B H f f B'
            node_id, seq_num, temperature, humidity, hop_count = struct.unpack(format_mask, raw_bytes)
            
            if node_id in last_seen_sequences and seq_num <= last_seen_sequences[node_id]:
                continue
            last_seen_sequences[node_id] = seq_num 
            
            if not (-40.0 <= temperature <= 85.0) or not (0.0 <= humidity <= 100.0):
                continue
                
            sql_insert_query = """
                INSERT INTO public.sensor_readings (node_id, seq_num, temperature, humidity, hop_count)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (node_id, seq_num) DO NOTHING;
            """
            payload = (node_id, seq_num, round(temperature, 2), round(humidity, 2), hop_count)
            
            cursor_platform.execute(sql_insert_query, payload)
            conn_platform.commit() 
            
            cursor_vlm.execute(sql_insert_query, payload)
            conn_vlm.commit()
            
            print(f"[DUAL UPDATE SUCCESS] Frame {seq_num} logged -> Platform_DB & VLM_DB | Temp: {temperature:.1f}°C")
            
        except Exception as error:
            print(f"[CRITICAL ERROR] Pipeline fault: {error}")
            conn_platform.rollback()
            conn_vlm.rollback()

if __name__ == "__main__":
    run_processing_pipeline()
