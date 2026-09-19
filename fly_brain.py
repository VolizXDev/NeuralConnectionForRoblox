from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Brain retention memory storage
last_known_vector = [0.0, 0.0]
memory_retention_timer = 0

@app.route('/process_brain', methods=['POST'])
def process_brain():
    global last_known_vector, memory_retention_timer
    try:
        data = request.json or {}
        
        # Sensory Layer 1: 50x50 Retina Matrix
        visual_lock = data.get('has_visual_lock', False)
        dir_X = data.get('dir_to_player_X', 0)
        dir_Z = data.get('dir_to_player_Z', 0)
        eye_image = data.get('fly_eye_image', [])
        
        # Sensory Layer 2: Acoustic Channels (Chat & Game World)
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dist = data.get('chat_distance', 999)
        chat_dir_X = data.get('chat_dir_X', 0)
        chat_dir_Z = data.get('chat_dir_Z', 0)
        hearing_game = data.get('is_hearing_game', False)
        
        # Sensory Layer 3: Physical Tactile Collision
        is_stuck = data.get('is_stuck_in_wall', False)
        
        motor_X = 0.0
        motor_Z = 0.0
        escape_jump = False
        speech_text = ""
        
        player_pixels_detected = eye_image.count(2)
        
        # 🧠 TACTILE REFLEX ROADBLOCK CIRCUIT: Jump instantly if hitting a wall structure
        if is_stuck:
            escape_jump = True
            # Force the motor grid to change course drastically
            motor_X = random.choice([-1.0, 1.0])
            motor_Z = 1.0 # Back away from collision zone
            speech_text = "BZZT! Obstacle collision detected! Executing wall clearing jump!"
            print("[TACTILE REFLEX] Wall obstruction registered. Deploying jump force field.")
            
        # 🔊 STARTLE REFLEX CIRCUIT: Jump if someone yells close by in text chat
        elif hearing_chat and chat_dist < 12:
            escape_jump = True
            speech_text = "BZZT! Startled by chat wave frequency! *JUMP*"
            print("[ACOUSTIC REFLEX] Large chat decibel spike. Firing jump mechanism.")
            
        # 🧠 LOCOMOTION DECISION MATRICES
        elif visual_lock or player_pixels_detected > 0:
            motor_X = dir_X
            motor_Z = dir_Z
            last_known_vector = [dir_X, dir_Z]
            memory_retention_timer = 15
            if hearing_game and random.random() < 0.05:
                speech_text = "Bzz! I see you and hear your footsteps!"
                
        elif memory_retention_timer > 0:
            motor_X = last_known_vector
            motor_Z = last_known_vector
            memory_retention_timer -= 1
            
        elif hearing_chat:
            motor_X = chat_dir_X
            motor_Z = chat_dir_Z
            
        else:
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            if random.random() < 0.02:
                speech_text = "Bzzt... Space scan clear..."
                
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
