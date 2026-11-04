import os
from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    # Denna enkla proxy skickar vidare allt den får till httpbin.org som ett test
    target_url = f"http://roblox.com{path}"
    
    # Skicka vidare förfrågan med rätt metod, data och headers
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    
    # Skicka tillbaka svaret till användaren
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    
    return Response(resp.content, resp.status_code, headers)

if __name__ == '__main__':
    # Render kräver att du lyssnar på porten de tilldelar via os.environ
    port = int(os.environ.get('PORT', 10000))
    # Lyssna på 0.0.0.0 så att appen är nåbar utifrån
    app.run(host='0.0.0.0', port=port)
