from flask import Flask, request, jsonify
import psycopg2
import random
import os
import math

app = Flask(__name__)

# Hämtar hela connection stringen direkt från Render (DATABASE_URL)
DB_URL = os.environ.get('DATABASE_URL')

def init_online_database():
    """Skapar tabellen för förstärkningsinlärning i Neon.tech."""
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

# --- ⚙️ INLÄRNINGSINSTÄLLNINGAR ---
LEARNING_RATE = 0.3
DISCOUNT_FACTOR = 0.85
EPSILON = 0.30  # 30% chans att testa helt slumpmässiga områden för att utforska och förstå miljön!

# --- 🧠 INTERNT MINNE & REGISTER (RAM) ---
temp_path_memory = {
    "last_known_heading": [0.0, 0.0],
    "retention_ticks": 0,
    "autonomous_walk_vector": [0.0, -1.0],
    "walk_hold_frames": 0
}

# --- 💬 UTTRYCK BASERAT PÅ MUSIK & INLÄRNING ---
vibing_thoughts = ["This beat is immaculate... bzzt.", "Oh yeah, that's a good audio frequency.", "Bzzt... Vibing to the music waves.", "Dancing to the rhythm!"]
hype_thoughts = ["BZZT!! THE BASS IS DROPPING!! 🔥", "HYPERDRIVE ACTIVE! JAMMING!!", "BZZT! CRANK UP THE VOLUME!"]
autonomous_thoughts = [
    "Exploring random areas to understand this map layout...",
    "Autonomous grid training cycle active. I go my own way.",
    "Mapping this room's geometry... bzzt.",
    "Understanding wall collision zones. Synapses upgrading."
]

def get_brain_state(distance, wall_ahead, music_loudness):
    """Omvandlar alla komplicerade sinnesdata till ett unikt tillstånd ID för databasen."""
    if wall_ahead: return "state_stuck_at_wall"
    if music_loudness > 350: return "state_hype_music"
    if music_loudness > 50: return "state_vibing_music"
    if distance < 15: return "state_near_player"
    return "state_exploring_random_areas"

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
    global temp_path_memory
    try:
        data = request.json or {}
        
        # SANS 1: Identitet & 50x50 synfält
        username = data.get('player_name', 'Player')
        visual_lock = data.get('has_visual_lock', False)
        dir_X = data.get('dir_to_player_X', 0.0)
        dir_Z = data.get('dir_to_player_Z', 0.0)
        eye_image = data.get('fly_eye_image', [])
        player_dist = data.get('player_distance', 999)
        
        # SANS 2: Hörsel (Chatt + Fotsteg + 🎵 MUSIKVOLYM)
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dir_X = data.get('chat_dir_X', 0.0)
        chat_dir_Z = data.get('chat_dir_Z', 0.0)
        hearing_game = data.get('is_hearing_game', False)
        music_volume = data.get('music_volume', 0) # PlaybackLoudness (0-1000)
        
        # SANS 3: Taktil (Antenn känner väggar)
        wall_in_front = data.get('wall_directly_ahead', False)

        player_pixels = eye_image.count(2)
        current_state = get_brain_state(player_dist, wall_in_front, music_volume)
        
        # Hämta sparade vikter från Neon (Inlärningsminnet)
        q_values = query_synapse_weights(current_state)
        
        # --- EXPLORATION VS EXPLOITATION ---
        # Om den slumpar (Epsilon), går den till slumpmässiga områden för att förstå kartan!
        is_exploring = random.random() < EPSILON
        if is_exploring:
            action = random.choice() # 0 = Gå Rakt Fram, 1 = Sidleds Strafe, 2 = Hoppa/Backa
            print(f"[LEARNING CYCLE] Exploring random areas to understand state: {current_state}")
        else:
            action = q_values.index(max(q_values)) # Använd bästa inlärda vägen

        motor_X, motor_Z = 0.0, 0.0
        escape_jump = False
        speech_text = ""
        fly_speed = 28 # Mänsklig basfart

        # Översätt val till fysisk WASD-gångdynamik
        if action == 0: # GÅ RAKT FRAM (W)
            if visual_lock:
                motor_X = dir_X * 1.5
                motor_Z = dir_Z * 1.5
            else:
                if temp_path_memory["walk_hold_frames"] <= 0:
                    temp_path_memory["autonomous_walk_vector"] = [random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0)]
                    temp_path_memory["walk_hold_frames"] = random.randint(15, 35)
                motor_X = temp_path_memory["autonomous_walk_vector"] * 1.0
                motor_Z = temp_path_memory["autonomous_walk_vector"] * 1.0
                temp_path_memory["walk_hold_frames"] -= 1
        elif action == 1: # SIDLEDS STRAFE (A / D)
            motor_X = random.choice([-2.0, 2.0])
            motor_Z = random.uniform(-0.1, 0.1)
        else: # BACKA OCH HOPPA (S + Space)
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = 1.2
            if wall_in_front or music_volume > 350: escape_jump = True

        # Spara till temporärt minne om den ser dig
        if visual_lock or player_pixels > 0:
            temp_path_memory["last_known_heading"] = [dir_X, dir_Z]
            temp_path_memory["retention_ticks"] = 30

        # Använd temporärt korttidsminne om du kliver bakom en vägg
        if not visual_lock and player_pixels == 0 and temp_path_memory["retention_ticks"] > 0:
            motor_X = temp_path_memory["last_known_heading"] * 1.3
            motor_Z = temp_path_memory["last_known_heading"] * 1.3
            temp_path_memory["retention_ticks"] -= 1

        # --- 💥 REINFORCEMENT LEARNING REWARD SYSTEM ---
        reward = 0
        
        if wall_in_front:
            # Belöna om den lär sig backa/hoppa (Action 2) från väggar, bestraffa hårt om den kraschar rakt in
            reward = 35 if action == 2 else -45
            escape_jump = True
            if random.random() < 0.20: speech_text = "BZZT! Object detected ahead! Jumping to clear the grid!"
            
        elif music_volume > 350:
            # 🔊 AGPRECIATE HYPE MUSIC: Belöna kaotiska hopp/strafes för att headbanga i takt!
            reward = 30 if (action == 2 or action == 1) else -10
            fly_speed = 42 # Springer jättesnabbt till tung musik!
            if random.random() < 0.08: speech_text = random.choice(hype_thoughts)
            
        elif music_volume > 50:
            # 🎵 APPRECIATE VIBING MUSIC: Belöna mjuk sidleds-strafe (Action 1) för att dansa harmoniskt
            reward = 25 if action == 1 else 5
            fly_speed = 22 # Lungnare dansfart
            # Skapar en mjuk gungande rörelse i sidled
            motor_X = math.sin(random.uniform(0, 6.28)) * 1.5
            motor_Z = random.uniform(-0.1, 0.1)
            if random.random() < 0.04: speech_text = random.choice(vibing_thoughts)
            
        else:
            # 🚶‍♂️ SJÄLVSTÄNDIG UTFORSKNING (Tyst miljö)
            # Belöna flugan för att hålla sig i rörelse och förstå kartan (Action 0) på tomma ytor!
            reward = 20 if action == 0 else -5
            if is_exploring and random.random() < 0.05:
                speech_text = random.choice(autonomous_thoughts)

        # Bellman Optimeringsekvation
        next_q_values = query_synapse_weights(current_state)
        old_val = q_values[action]
        q_values[action] = (1 - LEARNING_RATE) * old_val + LEARNING_RATE * (reward + DISCOUNT_FACTOR * max(next_q_values))
        
        # Spara framstegen permanent i Neon-databasen
        update_synapse_weights(current_state, q_values)

        return jsonify({
            "motor_X": motor_X,
            "motor_Z": motor_Z,
            "escape_jump": escape_jump,
            "speech_text": speech_text,
            "current_speed": fly_speed
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
