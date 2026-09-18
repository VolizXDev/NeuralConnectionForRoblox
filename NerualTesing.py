from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# --- Q-LEARNING / TRAINING CONFIGURATION ---
# Simple reinforcement learning lookup matrix for the fly's brain state
q_table = {} 
learning_rate = 0.2
discount_factor = 0.9
epsilon = 0.3 # Exploration rate: chance the fly does a random movement to learn

# Keep track of the last distance to calculate rewards
last_distance = 999

def get_state(distance):
    # Categorize distances into simple brain states
    if distance < 5: return "touching"
    if distance < 15: return "near"
    if distance < 40: return "far"
    return "blind"

@app.route('/process_brain', methods=['GET', 'POST'])
def process_brain():
    global last_distance, epsilon
    
    if request.method == 'GET':
        return jsonify({"message": "Brain training lab is online!"})

    try:
        data = request.json or {}
        visual_lock = data.get('has_visual_lock', False)
        player_dist = data.get('player_distance', 999)
        dir_X = data.get('dir_to_player_X', 0)
        dir_Z = data.get('dir_to_player_Z', 0)
        
        state = get_state(player_dist)
        
        # Decide action: 0 = Charge Forward, 1 = Move Randomly, 2 = Back Away
        if random.uniform(0, 1) < epsilon:
            action = random.choice([0, 1, 2]) # Explore random choices
        else:
            # Choose the action that the fly thinks will give the highest reward
            if state not in q_table:
                q_table[state] = [0.0, 0.0, 0.0]
            action = q_table[state].index(max(q_table[state]))
            
        # Execute the chosen action into motor movements
        if action == 0: # Charge target
            motor_X = dir_X + random.uniform(-0.02, 0.02)
            motor_Z = dir_Z + random.uniform(-0.02, 0.02)
        elif action == 1: # Random twitching
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
        else: # Retreat circuit
            motor_X = -dir_X
            motor_Z = -dir_Z

        # --- REINFORCEMENT LEARNING LOGIC (The Training) ---
        if visual_lock and player_dist != 999:
            # Reward calculation: Positive if it got closer, negative if it got farther away
            if player_dist < last_distance:
                reward = 10  # Positive reinforcement!
            elif player_dist > last_distance:
                reward = -5  # Negative reinforcement!
            else:
                reward = 0
                
            if player_dist < 5:
                reward = 50 # Massive jackpot reward for hitting the player!
                
            # Update the Q-table (the fly's memory bank)
            if state not in q_table:
                q_table[state] = [0.0, 0.0, 0.0]
                
            next_state = get_state(player_dist)
            if next_state not in q_table:
                q_table[next_state] = [0.0, 0.0, 0.0]
                
            old_value = q_table[state][action]
            next_max = max(q_table[next_state])
            
            # Bellman equation formula to update neural connections
            q_table[state][action] = (1 - learning_rate) * old_value + learning_rate * (reward + discount_factor * next_max)
            
            # Slowly reduce randomness as it gets smarter
            if epsilon > 0.05:
                epsilon -= 0.001
                
            print(f"[TRAINING] State: {state} | Action Chosen: {action} | Reward Given: {reward} | Brain Smartness: {q_table[state]}")

        last_distance = player_dist
        return jsonify({"motor_X": motor_X, "motor_Z": motor_Z})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
