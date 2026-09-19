from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Development baseline text arrays
passive_observations = [
    "Bzzt... Observing environment structure...",
    "Scanning 40x40 pixel horizons...",
    "Bzz... Listening to ambient sound frequencies."
]

@app.route('/process_brain', methods=['GET', 'POST'])
def process_brain():
    try:
        data = request.json or {}
        
        # Sensory Breakdown
        username = data.get('player_name', 'None')
        visual_lock = data.get('has_visual_lock', False)
        player_dist = data.get('player_distance', 999)
        dir_X = data.get('dir_to_player_X', 0)
        dir_Z = data.get('dir_to_player_Z', 0)
        
        hearing_chat = data.get('is_hearing_chat', False)
        chat_dir_X = data.get('chat_dir_X', 0)
        chat_dir_Z = data.get('chat_dir_Z', 0)
        
        motor_X, motor_Z = 0.0, 0.0
        speech_text = ""
        
        # 🧠 COGNITIVE MATRIX DEVELOPMENT AREA
        if visual_lock:
            # NORMAL OBSERVER REFLEX: Move close to check out the player, but don't sprint or attack
            if player_dist > 12:
                motor_X = dir_X
                motor_Z = dir_Z
            else:
                # Hover calmly and maintain distance once close enough to watch
                motor_X = random.uniform(-0.2, 0.2)
                motor_Z = random.uniform(-0.2, 0.2)
                
            if random.random() < 0.08:
                speech_text = f"Hello {username}. I am processing your avatar structure."
                
        elif hearing_chat:
            # ACOUSTIC INTEREST CIRCUIT: Walk toward the chat coordinates curiously
            motor_X = chat_dir_X
            motor_Z = chat_dir_Z
            if random.random() < 0.20:
                speech_text = "Bzzt! Detecting text data waves."
                
        else:
            # BASELINE WANDERING MODE
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            if random.random() < 0.03:
                speech_text = random.choice(passive_observations)
                
        return jsonify({
            "motor_X": motor_X,
            "motor_Z": motor_Z,
            "speech_text": speech_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Multi-sensory fly development server running stably on port 5000.")
    app.run(host='0.0.0.0', port=5000, debug=True)
