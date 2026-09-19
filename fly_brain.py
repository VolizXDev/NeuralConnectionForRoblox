from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/process_brain', methods=['GET', 'POST'])
def process_brain():
    if request.method == 'GET':
        return jsonify({"message": "40x40 High-Resolution Multi-Sensory Server Active!"})

    try:
        data = request.json or {}
        
        # SENSE LAYER 1: Optical 40x40 Matrix
        visual_lock = data.get('has_visual_lock', False)
        player_dist = data.get('player_distance', 999)
        dir_X = data.get('dir_to_player_X', 0)
        dir_Z = data.get('dir_to_player_Z', 0)
        eye_image = data.get('fly_eye_image', [])
        
        # SENSE LAYER 2: Acoustic Sound Waves
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dist = data.get('chat_distance', 999)
        chat_dir_X = data.get('chat_dir_X', 0)
        chat_dir_Z = data.get('chat_dir_Z', 0)
        
        motor_X = 0.0
        motor_Z = 0.0
        
        # Count how many target pixels out of 1,600 register the player
        player_pixels_detected = eye_image.count(2)
        
        # BRAIN HIERARCHY LOGIC:
        if visual_lock or player_pixels_detected > 0:
            # High Priority: Target is directly seen on the 40x40 retina layout matrix
            # Reduce motor randomness (wobble) the more pixels of the target it processes
            wobble_reduction = max(0.01, 0.05 - (player_pixels_detected * 0.005))
            
            motor_X = dir_X + random.uniform(-wobble_reduction, wobble_reduction)
            motor_Z = dir_Z + random.uniform(-wobble_reduction, wobble_reduction)
            print(f"[OPTICAL LOCK] Target profile acquired ({player_pixels_detected}/1600 pixels). Sprinting to hit!")
            
        elif hearing_chat:
            # Medium Priority: Blind to target, but tracking chat audio wave oscillations!
            motor_X = chat_dir_X
            motor_Z = chat_dir_Z
            print(f"[ACOUSTIC REFLEX] Caught audio wave chat signals at distance {chat_dist}! Intercepting sound source.")
            
        else:
            # Low Priority: No inputs. Wandering.
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            print("[IDLE NETWORK] Environment completely silent. Wandering.")
            
        return jsonify({"motor_X": motor_X, "motor_Z": motor_Z})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
