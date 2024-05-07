from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_cors import CORS
import requests

steam_api_key = '2220FF15666E1F4D56AD642BACA6A786'

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://mongo:27017/SteamDB"
mongo = PyMongo(app)
CORS(app)

@app.route('/steam/recently_played/<steam_id>')
def get_recently_played(steam_id):
    url = f'http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={steam_api_key}&steamid={steam_id}&format=json'
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Failed to fetch data'}), response.status_code

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')