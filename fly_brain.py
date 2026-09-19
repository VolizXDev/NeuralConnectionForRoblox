from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# 🧠 BRAIN MEMORY REGISTERS
# Stores the last heading direction when the player was visible
last_known_vector = [0.0, 0.0]
memory_retention_timer = 0  # How many frames it remembers your path

@app.route('/process_brain', methods=['POST'])
def process_brain():
    global last_known_vector, memory_retention_timer
    try:
        data = request.json or {}
        
        visual_lock = data.get('has_visual_lock', False)
        dir_X = data.get('dir_to_player_X', 0)
        dir_Z = data.get('dir_to_player_Z', 0)
        
        motor_X = 0.0
        motor_Z = 0.0
        speech_text = ""
        
        if visual_lock:
            # SENSE 1: You are fully visible. Update memory logs.
            motor_X = dir_X
            motor_Z = dir_Z
            
            # Save this exact trajectory path into memory
            last_known_vector = [dir_X, dir_Z]
            memory_retention_timer = 15  # Remember this path for the next 15 processing steps (~3 seconds)
            
            print("[SIGHT] Target visible. Updating path memory.")
            
        elif memory_retention_timer > 0:
            # SENSE 2: You just hid! Bypasses wandering and uses PATH MEMORY to hunt you down
            motor_X = last_known_vector[0]
            motor_Z = last_known_vector[1]
            
            # Count down the memory retention timer
            memory_retention_timer -= 1
            
            if random.random() < 0.20:
                speech_text = "Bzz! I remember where you ran! Searching last known path..."
            print(f"[MEMORY RETENTION] Target hidden. Executing path memory search. Time left: {memory_retention_timer}")
            
        else:
            # SENSE 3: Memory has faded completely. Revert to standard wandering.
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            print("[IDLE] No visual input and memory cleared. Wandering.")
            
        return jsonify({
            "motor_X": motor_X,
            "motor_Z": motor_Z,
            "speech_text": speech_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
