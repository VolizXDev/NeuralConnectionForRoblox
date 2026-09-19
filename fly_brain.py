from flask import Flask, request, jsonify
import random
import json
import os

app = Flask(__name__)

# 💾 FILE STORAGE CONSTANTS FOR PERMANENT MEMORY
MEMORY_FILE = "fly_biological_memory.json"

# Load structural memory charts by construction on startup
if os.path.exists(MEMORY_FILE):
    try:
        with open(MEMORY_FILE, "r") as f:
            fly_long_term_memory = json.load(f)
        print("🧠 [DATABASE] Permanent long-term memory matrix successfully restored from disk!")
    except Exception:
        print("⚠️ [DATABASE] Memory file corrupted. Initializing fresh structure.")
        fly_long_term_memory = {"entities": {}, "world_obstructions": []}
else:
    fly_long_term_memory = {
        "entities": {},        # Long-term behavioral profiles per username
        "world_obstructions": [] # Coordinate grids where the fly has historically crashed
    }

def commit_memory_to_disk():
    """Flushes active RAM memory maps into a permanent JSON file layout."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(fly_long_term_memory, f, indent=4)
    except Exception as e:
        print(f"⚠️ [DATABASE Error] Failed to write memory to disk: {e}")

@app.route('/process_brain', methods=['POST'])
def process_brain():
    try:
        data = request.json or {}
        
        # Identity & Kinematic Tracking Profiles
        username = data.get('player_name', 'None')
        visual_lock = data.get('has_visual_lock', False)
        player_dist = data.get('player_distance', 999)
        dir_X = data.get('dir_to_player_X', 0.0)
        dir_Z = data.get('dir_to_player_Z', 0.0)
        eye_image = data.get('fly_eye_image', [])
        
        # Acoustic Vectors (Multi-Modal Channels)
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dist = data.get('chat_distance', 999)
        chat_dir_X = data.get('chat_dir_X', 0.0)
        chat_dir_Z = data.get('chat_dir_Z', 0.0)
        hearing_game = data.get('is_hearing_game', False)
        
        # Tactile & Collision Data matrices
        is_stuck = data.get('is_stuck_in_wall', False)
        fly_position = data.get('fly_position', [0.0, 0.0, 0.0])
        
        # Count target elements on the 50x50 retina grid layer (2,500 total elements)
        player_pixels_detected = eye_image.count(2)
        
        # --- 🏗️ STRUCTURAL PROFILE RETENTION INITIALIZATION ---
        if username != "None" and username not in fly_long_term_memory["entities"]:
            fly_long_term_memory["entities"][username] = {
                "total_frames_observed": 0,
                "total_acoustic_signals": 0,
                "times_collided_near_target": 0,
                "last_known_heading": [0.0, 0.0],
                "memory_retention_frames": 0,
                "curiosity_score": 0.0
            }
            
        profile = fly_long_term_memory["entities"].get(username, None)
        
        # Update behavioral memory matrices dynamically
        if profile:
            if visual_lock or player_pixels_detected > 0:
                profile["total_frames_observed"] += 1
                profile["last_known_heading"] = [dir_X, dir_Z]
                profile["memory_retention_frames"] = 40  # Remembers target vector heading trail for ~8 seconds
                profile["curiosity_score"] = min(100.0, profile["curiosity_score"] + 0.1)
            elif profile["memory_retention_frames"] > 0:
                profile["memory_retention_frames"] -= 1
                
            if hearing_chat:
                profile["total_acoustic_signals"] += 1
                profile["curiosity_score"] = min(100.0, profile["curiosity_score"] + 2.5) # Auditory surprise increases memory focus
                
            if hearing_game and visual_lock:
                profile["curiosity_score"] = min(100.0, profile["curiosity_score"] + 0.05)
                
        # Structural Environmental Mapping: Record crash sectors to long term database
        if is_stuck:
            rounded_coord = [round(fly_position[0], 1), round(fly_position[2], 1)]
            if rounded_coord not in fly_long_term_memory["world_obstructions"]:
                fly_long_term_memory["world_obstructions"].append(rounded_coord)
                if profile: profile["times_collided_near_target"] += 1

        # --- MOTOR NEURON ROUTING MATRIX ---
        motor_X = 0.0
        motor_Z = 0.0
        escape_jump = False
        speech_text = ""
        
        if is_stuck:
            escape_jump = True
            motor_X = random.choice([-1.0, 1.0])
            motor_Z = 1.0
            speech_text = "BZZT! Wall collision obstacle mapped to structural long term memory!"
            
        elif hearing_chat and chat_dist < 12:
            escape_jump = True
            speech_text = f"BZZT! High chat decibel burst from {username}! Startle reflex triggered!"
            
        elif visual_lock or player_pixels_detected > 0:
            motor_X = dir_X
            motor_Z = dir_Z
            if random.random() < 0.02:
                speech_text = f"Observing '{username}'. Long-term focus metric: {round(profile['curiosity_score'], 1)}%"
                
        elif profile and profile["memory_retention_frames"] > 0:
            # 🧠 PROCESS LONG-TERM OBJECT PERMANENCE RETENTION
            motor_X = profile["last_known_heading"][0]
            motor_Z = profile["last_known_heading"][1]
            if random.random() < 0.04:
                speech_text = f"Target '{username}' obstructed. Navigating saved history coordinates..."
                
        elif hearing_chat:
            motor_X = chat_dir_X
            motor_Z = chat_dir_Z
            
        else:
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            if random.random() < 0.01:
                speech_text = "Bzzt... Baseline environment quiet. Memory arrays fully structural."
                
        # Commit all memory structural configurations to file storage permanently
        commit_memory_to_disk()
        
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
