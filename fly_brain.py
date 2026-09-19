from flask import Flask, request, jsonify
import psycopg2
import random
import os

app = Flask(__name__)

# Hämtar din Neon.tech Connection String automatiskt från Render (DATABASE_URL)
DB_URL = os.environ.get('DATABASE_URL')

def init_online_database():
    """Skapar tabellen för självständig Q-learning i Neon.tech."""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fly_learning_matrix (
                state_id TEXT PRIMARY KEY,
                action_0_weight REAL,
                action_1_weight REAL,
                action_2_weight REAL
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("🧠 [DATABASE] Connected to Neon.tech Cloud Autonomous Learning Core Successfully!")
    except Exception as e:
        print(f"⚠️ [DATABASE ERROR] Neon Connection Failed: {e}")

if DB_URL:
    init_online_database()

# --- ⚙️ INSTÄLLNINGAR FÖR INLÄRNING ---
LEARNING_RATE = 0.25
DISCOUNT_FACTOR = 0.85
EPSILON = 0.20  # 20% utforskning (testa nya WASD-steg), 80% använda det den lärt sig
last_distance_register = 999

# --- 🧠 INTERNT MINNE OCH RÖRELSEREGISTER (RAM) ---
temp_path_memory = {
    "last_known_heading": [0.0, 0.0],
    "retention_ticks": 0,
    "current_walk_direction": [0.0, -1.0], 
    "walk_hold_frames": 0  # Hur länge den håller ner en "WASD-knapp"
}

# --- 💬 SJÄLVSTÄNDIGA AI-UTTRYCK (Den pratar om sina egna mål) ---
autonomous_thoughts = [
    "Bzzt... Exploring new sectors of this Roblox map.",
    "No player signals needed. Designing my own navigation path.",
    "Autonomous network matrix fully active. I go my own way.",
    "Analyzing world grid boundaries... bzzt.",
    "Mapping this room's geometry. Seems clear ahead.",
    "Bzzt... Learning how to navigate without crashing."
]
chat_stuck = ["Bro, who placed this wall here?", "Map geometry blocking my path smh.", "Tactical sidestep jump to clear the angle!"]

def get_brain_state(distance, wall_ahead, sound_active):
    """Kategoriserar omgivningen baserat på flugans egna sinnen."""
    if wall_ahead: return "stuck_near_obstacle"
    if sound_active and distance < 20: return "hearing_nearby_noise"
    if distance < 15: return "object_in_close_proximity"
    return "exploring_open_airspace"

def query_synapse_weights(state_id):
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT action_0_weight, action_1_weight, action_2_weight FROM fly_learning_matrix WHERE state_id = %s", (state_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row: return list(row)
    except Exception:
        pass
    return [0.0, 0.0, 0.0]

def update_synapse_weights(state_id, weights):
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO fly_learning_matrix (state_id, action_0_weight, action_1_weight, action_2_weight)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (state_id) DO UPDATE SET 
                action_0_weight = EXCLUDED.action_0_weight,
                action_1_weight = EXCLUDED.action_1_weight,
                action_2_weight = EXCLUDED.action_2_weight
        ''', (state_id, weights, weights, weights))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ [DATABASE UPDATE ERROR] {e}")

@app.route('/process_brain', methods=['POST'])
def process_brain():
    global temp_path_memory, last_distance_register
    try:
        data = request.json or {}
        
        # Sinnen laddas in i matrisen
        username = data.get('player_name', 'Player')
        visual_lock = data.get('has_visual_lock', False)
        dir_X = data.get('dir_to_player_X', 0.0)
        dir_Z = data.get('dir_to_player_Z', 0.0)
        eye_image = data.get('fly_eye_image', [])
        player_dist = data.get('player_distance', 999)
        hearing_chat = data.get('is_hearing_chat', False)
        hearing_game = data.get('is_hearing_game', False)
        wall_in_front = data.get('wall_directly_ahead', False)

        player_pixels_detected = eye_image.count(2)
        current_state = get_brain_state(player_dist, wall_in_front, hearing_chat or hearing_game)
        
        # Hämta sparade vikter från Neon.tech (Långtidsminne)
        q_values = query_synapse_weights(current_state)
        
        # Inlärningsval via Epsilon-Greedy
        if random.random() < EPSILON:
            action = random.choice() # 0 = Gå Rakt Fram, 1 = Gå Sidelängs (Strafe), 2 = Taktiskt Hopp/Backa
        else:
            action = q_values.index(max(q_values))

        motor_X, motor_Z = 0.0, 0.0
        escape_jump = False
        speech_text = ""

        # --- WASD RÖRELSEMATRIS (Går som en självständig människa) ---
        if action == 0: # GE SIG UT OCH GÅ RAKT FRAM
            if temp_path_memory["walk_hold_frames"] <= 0:
                # Välj en helt egen, självständig kompassriktning och håll den i några sekunder
                temp_path_memory["current_walk_direction"] = [random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0)]
                temp_path_memory["walk_hold_frames"] = random.randint(20, 45)
            
            motor_X = temp_path_memory["current_walk_direction"] * 1.2
            motor_Z = temp_path_memory["current_walk_direction"] * 1.2
            temp_path_memory["walk_hold_frames"] -= 1
            
        elif action == 1: # SIDELÄNGS STRAFE (Undvika objekt / testa nya vinklar)
            motor_X = random.choice([-2.0, 2.0])
            motor_Z = random.uniform(-0.1, 0.1)
            
        else: # TACTICAL BACKUP & JUMP (Frigöra sig från hinder)
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = 1.3 # Backa (S)
            if wall_in_front: escape_jump = True

        # Spara till temporärt minne om den upptäcker ett rörligt objekt (t.ex. dig)
        if visual_lock or player_pixels_detected > 0:
            temp_path_memory["last_known_heading"] = [dir_X, dir_Z]
            temp_path_memory["retention_ticks"] = 25 # Uppmärksamma i ca 5 sekunder innan den går vidare

        # --- 💥 BELÖNINGSSYSTEM FÖR SJÄLVSTÄNDIGHET (REWARDS) ---
        reward = 0
        
        if wall_in_front:
            # Bestraffa hårt om den kraschar, belöna om den hoppar/backar bort (Action 2) för att rensa vägen
            reward = 35 if action == 2 else -45
            escape_jump = True
            if random.random() < 0.25: speech_text = random.choice(chat_stuck)
        else:
            # 🚀 BELÖNING FÖR ATT UTFORSKA FRIA YTOR:
            # Den får högst belöning för att hålla sig i rörelse och gå rakt fram (Action 0) på tomma ytor!
            if action == 0:
                reward = 25  # "Bra, du utforskar och går din egen väg!"
            else:
                reward = 5   # Mindre belöning för att bara stå still och strafa på samma ställe
                
            if random.random() < 0.015: 
                speech_text = random.choice(autonomous_thoughts)

        # Uppdatera Q-värdet (Bellmans ekvation)
        next_q_values = query_synapse_weights(current_state)
        old_val = q_values[action]
        q_values[action] = (1 - LEARNING_RATE) * old_val + LEARNING_RATE * (reward + DISCOUNT_FACTOR * max(next_q_values))
        
        # Spara de självständiga erfarenheterna i Neon permanent
        update_synapse_weights(current_state, q_values)

        last_distance_register = player_dist
        return jsonify({"motor_X": motor_X, "motor_Z": motor_Z, "escape_jump": escape_jump, "speech_text": speech_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
