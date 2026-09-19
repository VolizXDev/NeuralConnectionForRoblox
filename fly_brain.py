from flask import Flask, request, jsonify
import psycopg2
import random
import os

app = Flask(__name__)

# Hämtar hela anslutningssträngen automatiskt från Render (DATABASE_URL)
DB_URL = os.environ.get('DATABASE_URL')

def init_online_database():
    """Skapar tabellen för Q-learning i Neon.tech om den inte redan finns."""
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
        print("🧠 [DATABASE] Connected to Neon.tech Cloud Learning Core Successfully!")
    except Exception as e:
        print(f"⚠️ [DATABASE ERROR] Neon Connection Failed: {e}")

if DB_URL:
    init_online_database()

# --- ⚙️ INSTÄLLNINGAR FÖR HUMAN INLÄRNING ---
LEARNING_RATE = 0.25
DISCOUNT_FACTOR = 0.85
EPSILON = 0.20  # 20% utforskning (slumpmässiga WASD-tryck), 80% utnyttjande av inlärda mänskliga stigar
last_distance_register = 999

# --- 🧠 KORTTIDSMINNE OCH RÖRELSEREGISTER (RAM) ---
temp_path_memory = {
    "last_known_heading": [0.0, 0.0],
    "retention_ticks": 0,
    "current_walk_direction": [0.0, -1.0], 
    "walk_hold_frames": 0  # Hur många frames "människan" håller ner en tangent
}

# --- 🎮 MÄNSKLIGA CHATTUTTRYCK ---
chat_patrol = ["Let's go find some loot.", "Bro, this server is kinda quiet.", "Heading to the next zone.", "Checking the perimeter."]
chat_combat = ["Ayo I see you! Don't run!", "Target locked on my 50x50 retina!", "Bruh, stop camping behind that wall!", "Going aggressive, watch out."]
chat_stuck = ["Bro, who placed this wall here?", "Map geometry blocking my path smh.", "Tactical sidestep jump to clear the angle!", "Lag spike pushed me into a brick."]

def get_brain_state(distance, wall_ahead, sound_active):
    """Kategoriserar 3D-världen till diskreta tillstånd för maskininlärningen."""
    if wall_ahead: return "human_stuck_wall"
    if sound_active and distance > 40: return "hearing_noise_far"
    if distance < 8: return "human_close_combat"
    if distance < 25: return "human_near_target"
    if distance < 65: return "human_searching_target"
    return "human_patrol_void"

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
        
        # SANS 1: Identitet & Syn (50x50 rutenett = 2500 piksler)
        username = data.get('player_name', 'Player')
        visual_lock = data.get('has_visual_lock', False)
        dir_X = data.get('dir_to_player_X', 0.0)
        dir_Z = data.get('dir_to_player_Z', 0.0)
        eye_image = data.get('fly_eye_image', [])
        player_dist = data.get('player_distance', 999)
        
        # SANS 2: Hörsel (Chat + Fotsteg i Roblox)
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dir_X = data.get('chat_dir_X', 0.0)
        chat_dir_Z = data.get('chat_dir_Z', 0.0)
        hearing_game = data.get('is_hearing_game', False)
        
        # SANS 3: Taktil (Känner av väggar framför sig)
        wall_in_front = data.get('wall_directly_ahead', False)

        player_pixels_detected = eye_image.count(2)
        current_state = get_brain_state(player_dist, wall_in_front, hearing_chat or hearing_game)
        
        # Hämta sparade Q-värden från Neon
        q_values = query_synapse_weights(current_state)
        
        # Mänskligt val via Epsilon-Greedy (Utforska eller använd minne)
        if random.random() < EPSILON:
            action = random.choice() # 0 = Gå Rakt (W), 1 = Strafe Sidleds (A/D), 2 = Taktiskt Hopp/Backa (S+Space)
        else:
            action = q_values.index(max(q_values))

        motor_X, motor_Z = 0.0, 0.0
        escape_jump = False
        speech_text = ""

        # Översätt inlärda beslut till raka, kontrollerade tangentbordsrörelser
        if action == 0: # GÅ RAKT (W)
            if visual_lock:
                motor_X = dir_X * 1.5
                motor_Z = dir_Z * 1.5
            elif hearing_chat:
                motor_X = chat_dir_X * 1.4
                motor_Z = chat_dir_Z * 1.4
            else:
                # Patrullera i en rak linje i flera frames (Gå som en människa)
                if temp_path_memory["walk_hold_frames"] <= 0:
                    temp_path_memory["current_walk_direction"] = [random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0)]
                    temp_path_memory["walk_hold_frames"] = random.randint(15, 35)
                motor_X = temp_path_memory["current_walk_direction"] * 0.8
                motor_Z = temp_path_memory["current_walk_direction"] * 0.8
                temp_path_memory["walk_hold_frames"] -= 1
        elif action == 1: # STRAFE (Sidledsrörelse A / D)
            motor_X = random.choice([-2.0, 2.0])
            motor_Z = random.uniform(-0.1, 0.1)
        else: # BACKA OCH HOPPA (S + Space)
            motor_X = -dir_X if visual_lock else random.uniform(-1.0, 1.0)
            motor_Z = 1.2
            if wall_in_front: escape_jump = True

        # Spara till temporärt korttidsminne (RAM) om du syns
        if visual_lock or player_pixels_detected > 0:
            temp_path_memory["last_known_heading"] = [dir_X, dir_Z]
            temp_path_memory["retention_ticks"] = 35 # Kommer ihåg stigen i ca 7 sekunder

        # Använd temporärt minne (Stisporing runt hörn)
        if not visual_lock and player_pixels_detected == 0 and temp_path_memory["retention_ticks"] > 0:
            motor_X = temp_path_memory["last_known_heading"] * 1.3
            motor_Z = temp_path_memory["last_known_heading"] * 1.3
            temp_path_memory["retention_ticks"] -= 1

        # --- 💥 REINFORCEMENT LEARNING REWARD MATRIS ---
        reward = 0
        if wall_in_front:
            # Belöna flugan stort om den lär sig att STRAFA (Action 1) eller HOPPA (Action 2) runt väggar
            reward = 25 if (action == 1 or action == 2) else -35
            escape_jump = True
            if random.random() < 0.20: speech_text = random.choice(chat_stuck)
        elif visual_lock or player_pixels_detected > 0:
            if player_dist < last_distance_register:
                reward = 15  # Belöning för att minska avståndet till dig (W-press)
            else:
                reward = -10
            if player_dist < 8:
                reward = 60  # Jackpot! Den nådde mänsklig närstrid
                if random.random() < 0.05: speech_text = random.choice(combat_chat)
        else:
            if random.random() < 0.01: speech_text = random.choice(chat_patrol)

        # Bellman Optimeringsekvation
        next_q_values = query_synapse_weights(current_state)
        old_val = q_values[action]
        q_values[action] = (1 - LEARNING_RATE) * old_val + LEARNING_RATE * (reward + DISCOUNT_FACTOR * max(next_q_values))
        
        # Spara vikterna i Neon permanent!
        update_synapse_weights(current_state, q_values)

        last_distance_register = player_dist
        return jsonify({"motor_X": motor_X, "motor_Z": motor_Z, "escape_jump": escape_jump, "speech_text": speech_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
