from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# 🧠 BIOLOGICAL MEMORY REGISTERS
last_known_vector = [0.0, 0.0]
memory_retention_timer = 0  # Number of processing frames to remember a hidden target

@app.route('/process_brain', methods=['GET', 'POST'])
def process_brain():
    global last_known_vector, memory_retention_timer
    
    if request.method == 'GET':
        return jsonify({"message": "Permanent Multi-Sensory Memory Brain Active!"})

    try:
        data = request.json or {}
        
        # Sense Layer 1: 40x40 Optical Grid Matrix
        visual_lock = data.get('has_visual_lock', False)
        dir_X = data.get('dir_to_player_X', 0)
        dir_Z = data.get('dir_to_player_Z', 0)
        eye_image = data.get('fly_eye_image', [])
        
        # Sense Layer 2: Acoustic Audio Waves
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dist = data.get('chat_distance', 999)
        chat_dir_X = data.get('chat_dir_X', 0)
        chat_dir_Z = data.get('chat_dir_Z', 0)
        
        # Output States Initialization
        motor_X = 0.0
        motor_Z = 0.0
        should_jump = False
        speech_text = ""
        
        player_pixels_detected = eye_image.count(2)
        
        # 🔊 HOPPING SENSORY NEURON: Startle reflex triggers a jump if sound is very close
        if hearing_chat and chat_dist < 15:
            should_jump = True
            speech_text = "BZZT! Startle acoustic reflex! *JUMP*"
            print("[REFLEX] Jump circuit activated via nearby chat sound proximity.")
            
        # 🧠 BEHAVIORAL PATTERN HIERARCHY MATRICES:
        if visual_lock or player_pixels_detected > 0:
            # Hierarchy 1: Player is visible on the 40x40 retina layout array
            motor_X = dir_X
            motor_Z = dir_Z
            
            # Continuously update long-term location path retention memory
            last_known_vector = [dir_X, dir_Z]
            memory_retention_timer = 15  # Retain path coordinates for roughly 3 seconds
            print(f"[VISION LOCK] Tracking path directly. Pixels: {player_pixels_detected}/1600")
            
        elif memory_retention_timer > 0:
            # Hierarchy 2: Player hid! Execute short-term path retention tracking loop
            motor_X = last_known_vector[0]
            motor_Z = last_known_vector[1]
            memory_retention_timer -= 1
            
            if random.random() < 0.15:
                speech_text = "Bzzt... Searching last known memory coordinates..."
            print(f"[PATH RETENTION] Blind to target. Navigating memory matrix. Steps remaining: {memory_retention_timer}")
            
        elif hearing_chat:
            # Hierarchy 3: Blind and no vision memory, but tracking new chat sound waves
            motor_X = chat_dir_X
            motor_Z = chat_dir_Z
            print(f"[ACOUSTIC TRACKING] Snapping motor heading vectors toward chat audio coordinates.")
            
        else:
            # Hierarchy 4: Quiet environment, empty canvas mapping. Wander freely.
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            if random.random() < 0.02:
                speech_text = "Bzzt... Scanning environment open airspace..."
                
        return jsonify({
            "motor_X": motor_X,
            "motor_Z": motor_Z,
            "should_jump": should_jump,
            "speech_text": speech_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
