from flask import Flask, request, jsonify
import psycopg2
import random
import os

app = Flask(__name__)

# --- FIXAT ANPRÖVNINGS-FORMAT (Ingen länk, skickar parametrar separat) ---
DB_HOST = "db.svvqditsloucflenpuog.supabase.co"
DB_PORT = "6543"  # Ändrat till 6543 för att lösa "Network is unreachable" via IPv4 Pooler
DB_NAME = "postgres"
DB_USER = "postgres"
# Hämtar ditt lösenord säkert från Renders miljövariabler (DATABASE_PASSWORD)
DB_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'DITT_LÖSENORD_HÄR')

def init_online_database():
    """Skapar tabellen för Q-learning i Supabase om den inte redan finns."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
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
        print("🧠 [DATABASE] Connected to Supabase Cloud Q-Learning Core Network Successfully.")
    except Exception as e:
        print(f"⚠️ [DATABASE ERROR] Cloud Connection Failed: {e}")

# Kör databasinitieringen direkt vid boot
init_online_database()

# --- INSTÄLLNINGAR FÖR Q-LEARNING / INLÄRNING ---
LEARNING_RATE = 0.3
DISCOUNT_FACTOR = 0.8
EPSILON = 0.20  # 20% chans till slumpmässig handling för att lära sig, 80% att använda bästa spår
last_distance_register = 999

# --- TEMPORÄRT KORTTIDSMINNE (RAM-cache för stisporing) ---
temp_path_memory = {
    "last_known_heading": [0.0, 0.0],
    "retention_ticks": 0
}

def get_brain_state(distance, wall_ahead, sound_active):
    if wall_ahead: return "stuck_near_object"
    if sound_active and distance > 40: return "hearing_noise_far"
    if distance < 8: return "touching_player"
    if distance < 25: return "near_player"
    if distance < 65: return "far_player"
    return "searching_empty_void"

def query_synapse_weights(state_id):
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
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
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO fly_learning_matrix (state_id, action_0_weight, action_1_weight, action_2_weight)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (state_id) DO UPDATE SET 
                action_0_weight = EXCLUDED.action_0_weight,
                action_1_weight = EXCLUDED.action_1_weight,
                action_2_weight = EXCLUDED.action_2_weight
        ''', (state_id, weights[0], weights[1], weights[2]))
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
        
        # SANS 2: Hørsel (Chat + Fotsteg i Roblox)
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dir_X = data.get('chat_dir_X', 0.0)
        chat_dir_Z = data.get('chat_dir_Z', 0.0)
        hearing_game = data.get('is_hearing_game', False)
        
        # SANS 3: Taktil (Känner av väggar framför sig)
        wall_in_front = data.get('wall_directly_ahead', False)

        player_pixels_detected = eye_image.count(2)
        current_state = get_brain_state(player_dist, wall_in_front, hearing_chat or hearing_game)
        
        # Hämta sparad matris från Supabase
        q_values = query_synapse_weights(current_state)
        
        # Inlärningsval (Epsilon-Greedy)
        if random.random() < EPSILON:
            action = random.choice([0, 1, 2])
        else:
            action = q_values.index(max(q_values))

        motor_X, motor_Z = 0.0, 0.0
        escape_jump = False
        speech_text = ""

        # Översätt val till rörelser
        if action == 0:
            motor_X = dir_X if visual_lock else (chat_dir_X if hearing_chat else random.uniform(-0.5, 0.5))
            motor_Z = dir_Z if visual_lock else (chat_dir_Z if hearing_chat else -0.5)
        elif action == 1:
            motor_X = random.choice([-1.5, 1.5])
            motor_Z = random.uniform(-0.2, 0.2)
        else:
            motor_X = -dir_X if visual_lock else random.uniform(-1.0, 1.0)
            motor_Z = 1.0
            if wall_in_front or hearing_chat: escape_jump = True

        # Spara till temporärt korttidsminne (RAM) om du syns
        if visual_lock or player_pixels_detected > 0:
            temp_path_memory["last_known_heading"] = [dir_X, dir_Z]
            temp_path_memory["retention_ticks"] = 35 # Kommer ihåg stigen i ca 7 sekunder

        # Använd temporärt minne om du gömmer dig
        if not visual_lock and player_pixels_detected == 0 and temp_path_memory["retention_ticks"] > 0:
            motor_X = temp_path_memory["last_known_heading"][0]
            motor_Z = temp_path_memory["last_known_heading"][1]
            temp_path_memory["retention_ticks"] -= 1

        # --- BELÖNINGSSYSTEM FÖR INLÄRNING ---
        reward = 0
        if wall_in_front:
            # Belöna flugan om den hoppar/backar från väggen, bestraffa om den kraschar in
            reward = 20 if action == 2 else -30 
        elif visual_lock or player_pixels_detected > 0:
            if player_dist < last_distance_register:
                reward = 12 # Positiv belöning för att gå mot dig
            elif player_dist > last_distance_register:
                reward = -10
            if player_dist < 8:
                reward = 50 # Jackpot! Den hittade dig

        # Uppdatera Q-värdet (Bellmans ekvation)
        next_q_values = query_synapse_weights(current_state)
        old_val = q_values[action]
        q_values[action] = (1 - LEARNING_RATE) * old_val + LEARNING_RATE * (reward + DISCOUNT_FACTOR * max(next_q_values))
        
        # Spara vikterna i Supabase-molnet permanent!
        update_synapse_weights(current_state, q_values)
        
        if wall_in_front:
            escape_jump = True
            speech_text = "BZZT! Object detected! Executing wall-clearing jump circuit!"

        last_distance_register = player_dist
        return jsonify({"motor_X": motor_X, "motor_Z": motor_Z, "escape_jump": escape_jump, "speech_text": speech_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
