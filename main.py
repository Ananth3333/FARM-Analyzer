from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
import psycopg2
import asyncio
import json
import random
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "index.html")
CHART_JS_PATH = os.path.join(BASE_DIR, "templates", "chart.js")

def get_platform_db_connection():
    return psycopg2.connect(
        host="localhost", 
        database="Platform_DB",  
        user="postgres", 
        password="Ananth@3333",  
        port="5432"
    )

@app.get("/", response_class=HTMLResponse)
async def read_dashboard():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

# FIXED FOR MANI: Serves the chart library locally from your laptop storage drive
@app.get("/templates/chart.js")
async def get_local_chart_js():
    if os.path.exists(CHART_JS_PATH):
        return FileResponse(CHART_JS_PATH, media_type="application/javascript")
    return HTMLResponse(content="console.error('chart.js file missing on laptop drive');", status_code=404)

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WEBSOCKET] Client browser tunnel established successfully.")
    
    last_timestamp = None
    last_seq_num = None 
    
    try:
        while True:
            try:
                conn = get_platform_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT timestamp_column, temperature, humidity, seq_num 
                    FROM public.sensor_readings 
                    ORDER BY timestamp_column DESC 
                    LIMIT 1;
                """)
                row = cursor.fetchone()
                
                if row is not None:
                    timestamp, temp, hum, seq_num = row
                    current_timestamp = timestamp.strftime("%H:%M:%S")
                    
                    if last_timestamp != current_timestamp:
                        last_timestamp = current_timestamp
                        is_duplicate = (last_seq_num == seq_num)
                        last_seq_num = seq_num  
                        
                        payload = {
                            "type": "telemetry",
                            "data": {
                                "time": current_timestamp,
                                "temperature": float(temp),
                                "humidity": float(hum),
                                "duplicate": is_duplicate,
                                "soil": 44.8,
                                "npk": 0.71
                            }
                        }
                        await websocket.send_text(json.dumps(payload))
                
                cursor.close()
                conn.close()
                
            except Exception as db_error:
                pass
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print("[WEBSOCKET] Client browser disconnected.")
    except Exception as e:
        print(f"[WEBSOCKET ERROR] Connection lost: {e}")
