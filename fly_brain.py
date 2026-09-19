from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/process_brain', methods=['GET', 'POST'])
def process_brain():
    if request.method == 'GET':
        return jsonify({"message": "20x20 Biological Eye Server is live!"})

    try:
        data = request.json or {}
        visual_lock = data.get('has_visual_lock', False)
        player_dist = data.get('player_distance', 999)
        eye_image = data.get('fly_eye_image', [])
        
        # Sjekk at vi faktisk fikk 400 piksler (20x20)
        if len(eye_image) == 400:
            print("\n--- 👁️ FLUE-REMS LIVE BILDE (20x20 piksler) ---")
            for i in range(0, 400, 20):
                row = []
                for pixel in eye_image[i:i+20]:
                    if pixel == 2:
                        row.append("🎯") # Fluen ser DEG (Rødt/mål)
                    elif pixel == 1:
                        row.append("█") # Fluen ser en vegg (Grå/hindring)
                    else:
                        row.append(".") # Åpen luft (Ingenting)
                print("".join(row))
            print("-----------------------------------------------")

        # Nevrale kretsers beslutning basert på bildet
        motor_X = 0.0
        motor_Z = 0.0
        
        # Teller hvor mange piksler av spilleren fluen ser totalt
        player_pixels = eye_image.count(2)
        
        if player_pixels > 0:
            # Jakt-refleks: Beveg deg i retning av der flest spiller-piksler er registrert
            # Enkelt sagt: Søk mot målet
            motor_X = random.uniform(-0.1, 0.1)
            # Hvis spilleren er langt unna, gå framover
            motor_Z = -0.8
            print(f"[HJERNE] Ser spilleren i {player_pixels} piksler! Angriper.")
        else:
            # Spontan vandring hvis bildet er tomt for spillere
            motor_X = random.uniform(-1.0, 1.0)
            motor_Z = random.uniform(-1.0, 1.0)
            print("[HJERNE] Ingen spiller funnet i 20x20-matrisen. Vandrer.")
            
        return jsonify({"motor_X": motor_X, "motor_Z": motor_Z})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
