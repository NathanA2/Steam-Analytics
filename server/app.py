from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_cors import CORS
from requests.exceptions import Timeout, RequestException
import requests
import logging

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO)

steam_api_key = '2220FF15666E1F4D56AD642BACA6A786'

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://mongo:27017/SteamDB"
mongo = PyMongo(app)
CORS(app)

@app.route('/steam/recently_played/<steam_id>')
def get_recently_played(steam_id):
    response = requests.get(f'http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={steam_api_key}&steamid={steam_id}&format=json')
    games_data = response.json()['response']['games']
    return jsonify(games_data)

def fetch_game_details(appid):
    url = f'http://store.steampowered.com/api/appdetails?appids={appid}&filters=genres'
    try:
        response = requests.get(url, timeout=10)  # 10 seconds timeout
        response.raise_for_status()
        return response.json()
    except Timeout:
        logging.error(f"Request timed out for AppID: {appid}")
    except RequestException as e:
        logging.error(f"Request failed for AppID: {appid}, Error: {e}")
    return None

@app.route('/steam/all_games_genres/<steam_id>')
def get_games_genres(steam_id):
    games_response = requests.get(f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_api_key}&steamid={steam_id}&include_appinfo=true&format=json')
    games_data = games_response.json()['response']['games']

    games_with_genres = []
    for game in games_data:
        logging.info(f"Processing game {game['name']} (AppID: {game['appid']})")
        game_record = mongo.db.games.find_one({'appid': game['appid']})
        if game_record:
            game['genres'] = game_record['genres']
        else:
            game_details = fetch_game_details(game['appid'])
            if game_details and game_details[str(game['appid'])]['success']:
                if(game_details[str(game['appid'])]['data'] != []):
                    genres = [genre['description'] for genre in game_details[str(game['appid'])]['data'].get('genres', [])]
                    game['genres'] = genres
                    mongo.db.games.insert_one({'appid': game['appid'], 'genres': genres})
            else:
                game['genres'] = ['Unknown']
        games_with_genres.append(game)
    logging.info(f"Finished Processing Games")
    return jsonify(games_with_genres)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')