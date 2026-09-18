from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Basic storage for fly reinforcement learning values
q_table = {}
learning_rate = 0.2
discount_factor = 0.9
epsilon = 0.3
last_distance = 999

def get_state(distance):
    if distance < 5: return "touching"
    if distance < 15: return "near"
    if distance < 40: return "far"
    return "blind"

@app.route('/')
def dashboard():
    return "🧠 Fruit Fly Lab Server is running smoothly on the web!"

@app.route('/process_brain', methods=['GET', 'POST'])
def process_brain():
    global last_distance, epsilon
    
    if request.method == 'GET':
        return jsonify({"message": "Server is actively hunting!"})

    try:
        data = request.json or {}
        visual_lock = data.get('has_visual_lock', False)
        player_dist = data.get('player_distance', 999)
        dir_X = data.get('dir_to_player_X', 0)
        dir_Z = data.get('dir_to_player_Z', 0)
        
        state = get_state(player_dist)
        
        # Action selector mechanics
        if random.uniform(0, 1) < epsilon:
            # Pick a random fallback action path
            action = random.choice([0, 1, 2])
        else:
            if state not in q_table:
                q_table[state] = [0.0, 0.0, 0.0]
            action = q_table[state].index(max(q_table[state]))
            
        # Translate matrix weights into actual direction vectors
        if action == 0:
            motor_X = dir_X + random.uniform(-0.02, 0.02)
            motor_Z = dir_Z + random.uniform(-0.02, 0.02)
        elif action == 1:
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
        else:
            motor_X = -dir_X
            motor_Z = -dir_Z

        # Brain adjustment reward protocols
        if visual_lock and player_dist != 999:
            reward = 10 if player_dist < last_distance else -5
            if player_dist < 5: reward = 50
                
            if state not in q_table:
                q_table[state] = [0.0, 0.0, 0.0]
                
            next_state = get_state(player_dist)
            if next_state not in q_table:
                q_table[next_state] = [0.0, 0.0, 0.0]
                
            old_val = q_table[state][action]
            next_max = max(q_table[next_state])
            
            q_table[state][action] = (1 - learning_rate) * old_val + learning_rate * (reward + discount_factor * next_max)
            
            if epsilon > 0.05:
                epsilon -= 0.001

        last_distance = player_dist
        return jsonify({"motor_X": motor_X, "motor_Z": motor_Z})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
