from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/process_brain', methods=['GET', 'POST'])
def process_brain():
    if request.method == 'GET':
        return jsonify({"message": "40x40 High-Resolution Matrix Server Active!"})

    try:
        data = request.json or {}
        visual_lock = data.get('has_visual_lock', False)
        player_dist = data.get('player_distance', 999)
        dir_X = data.get('dir_to_player_X', 0)
        dir_Z = data.get('dir_to_player_Z', 0)
        eye_image = data.get('fly_eye_image', [])
        
        motor_X = 0.0
        motor_Z = 0.0
        
        # Teller hvor mange piksler av de 1600 totale som ser spilleren
        player_pixels_detected = eye_image.count(2)
        
        if visual_lock or player_pixels_detected > 0:
            # ULTRA-FOKUSERT JAKTKRETS:
            # Jo flere piksler fluen ser av deg, jo mer nøyaktig og aggressivt låser den retningen
            wobble_reduction = max(0.01, 0.05 - (player_pixels_detected * 0.005))
            
            motor_X = dir_X + random.uniform(-wobble_reduction, wobble_reduction)
            motor_Z = dir_Z + random.uniform(-wobble_reduction, wobble_reduction)
            
            print(f"[HD 40x40 LOCK] Target tracking matrix active. Detected pixels: {player_pixels_detected}/1600. SPRINTING!")
        else:
            # SØKEKRETS: Tilfeldig surring i rommet
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            print("[HD 40x40 WANDERING] 1600 pixel grid empty. Searching for target context...")
            
        return jsonify({"motor_X": motor_X, "motor_Z": motor_Z})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
