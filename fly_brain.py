from flask import Flask, request, jsonify
import psycopg2
import random
import os

app = Flask(__name__)

# 🔗 KOBLE TIL DIN GRATIS ONLINE DATABASE (SUPABASE)
# Lim inn din Connection URI fra Supabase her (eller sett den som Environment Variable i Render)
DB_URL = os.environ.get('DATABASE_URL', 'LIM_INN_DIN_SUPABASE_CONNECTION_URI_HER')

def init_online_database():
    """Oppretter tabellen for langtidshukommelse i skyen hvis den ikke finnes."""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fly_long_term_memory (
                username TEXT PRIMARY KEY,
                curiosity_score REAL,
                total_interactions INTEGER
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("🧠 [DATABASE] Koblet til Supabase Cloud Memory permanent.")
    except Exception as e:
        print(f"⚠️ [DATABASE FEIL] Klarte ikke koble til skyen: {e}")

# Start databasen med en gang serveren booter
init_online_database()

# --- midlertidig korttidshukommelse (Lagres i RAM-cache for stisporing) ---
temp_path_memory = {
    "last_known_heading": [0.0, 0.0],
    "retention_ticks": 0
}

def sync_cloud_memory(username, visual_active, audio_active):
    """Henter og oppdaterer langtidshukommelsen i skyen (Supabase)."""
    if username == "None": 
        return {"curiosity_score": 0.0, "total_interactions": 0}
        
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    cursor.execute("SELECT curiosity_score, total_interactions FROM fly_long_term_memory WHERE username = %s", (username,))
    row = cursor.fetchone()
    
    if row:
        score, counts = row[0], row[1]
    else:
        score, counts = 0.0, 0
        
    # Hvis det er aktiv interaksjon i denne framen, oppdaterer vi langtidshukommelsen
    if visual_active or audio_active:
        counts += 1
        score = min(100.0, score + (2.5 if audio_active else 0.1))
        
        cursor.execute('''
            INSERT INTO fly_long_term_memory (username, curiosity_score, total_interactions)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) 
            DO UPDATE SET curiosity_score = EXCLUDED.curiosity_score, total_interactions = EXCLUDED.total_interactions
        ''', (username, score, counts))
        conn.commit()
        
    cursor.close()
    conn.close()
    return {"curiosity_score": score, "total_interactions": counts}

@app.route('/process_brain', methods=['POST'])
def process_brain():
    global temp_path_memory
    try:
        data = request.json or {}
        
        # SANS 1: Syn og identitet (50x50 rutenett)
        username = data.get('player_name', 'None')
        visual_lock = data.get('has_visual_lock', False)
        dir_X = data.get('dir_to_player_X', 0.0)
        dir_Z = data.get('dir_to_player_Z', 0.0)
        eye_image = data.get('fly_eye_image', [])
        
        # SANS 2: Hørsel (Chat og i-spillet lyder)
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dir_X = data.get('chat_dir_X', 0.0)
        chat_dir_Z = data.get('chat_dir_Z', 0.0)
        hearing_game = data.get('is_hearing_game', False)
        
        # SANS 3: Taktil (Føler gjenstander/vegger foran seg)
        wall_in_front = data.get('wall_directly_ahead', False)

        player_pixels_detected = eye_image.count(2)
        
        # 📂 SYNKRONISER LANGTIDSHUKOMMELSEN MED SKYEN
        cloud_data = sync_cloud_memory(username, visual_lock or player_pixels_detected > 0, hearing_chat)
        
        motor_X, motor_Z = 0.0, 0.0
        escape_jump = False
        speech_text = ""

        # --- HJERNEKRETSENES PRIORITERINGSHIERARKI ---
        
        # 1. TAKTIL KRETS: Føler vegg foran seg -> HOPP I STEDET FOR Å GÅ INN I DEN
        if wall_in_front:
            escape_jump = True
            motor_X = random.choice([-1.0, 1.0])
            motor_Z = 1.0  # Tvinger fluen til å hoppe bakover og styre unna veggen
            speech_text = "BZZT! Object detected in front! Activating obstacle-clearing jump circuit!"
            print("[TAKTIL SANS] Føler vegg foran seg. Utfører unnavikende hopp.")

        # 2. SYNSKRETS: Aktiv sporing via 50x50 rutenettet
        elif visual_lock or player_pixels_detected > 0:
            motor_X = dir_X
            motor_Z = dir_Z
            
            # Lagre til MIDLERTIDIG KORTTIDSHUKOMMELSE (RAM-cache for stisporing)
            temp_path_memory["last_known_heading"] = [dir_X, dir_Z]
            temp_path_memory["retention_ticks"] = 35  # Husker retningen i ca 7 sekunder etter du forsvinner
            
            if random.random() < 0.03:
                speech_text = f"Observing {username}. Long-term cloud score: {round(cloud_data['curiosity_score'], 1)}%"

        # 3. BRUK MIDLERTIDIG KORTTIDSHUKOMMELSE HVIS BLIND (Stisporing bak vegger)
        elif temp_path_memory["retention_ticks"] > 0:
            motor_X = temp_path_memory["last_known_heading"][0]
            motor_Z = temp_path_memory["last_known_heading"][1]
            temp_path_memory["retention_ticks"] -= 1  # Minnet svekkes for hver frame
            
            if random.random() < 0.05:
                speech_text = f"Target lost. Running temporary short-term memory traces for {username}..."
                print(f"[KORTTIDSHUKOMMELSE] Følger stien til {username}. Ticks igjen: {temp_path_memory['retention_ticks']}")

        # 4. HØRSELSKRETS: Reagerer på chat-meldinger
        elif hearing_chat:
            motor_X = chat_dir_X
            motor_Z = chat_dir_Z
            
        else:
            # Baseline rolig modus (Tilfeldig surring)
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            if hearing_game and random.random() < 0.05:
                speech_text = "Bzz... I can hear movement vibrations in the game..."
            
        return jsonify({
            "motor_X": motor_X,
            "motor_Z": motor_Z,
            "escape_jump": escape_jump,
            "speech_text": speech_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
