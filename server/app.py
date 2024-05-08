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
    response = requests.get(f'http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={steam_api_key}&steamid={steam_id}&format=json')
    games_data = response.json()['response']['games']
    return jsonify(games_data)

@app.route('/steam/all_games_genres/<steam_id>')
def get_games_genres(steam_id):
    # Fetch all games owned by the user
    games_response = requests.get(f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_api_key}&steamid={steam_id}&include_appinfo=true&format=json')
    print("Games Retrieved")
    games_data = games_response.json()['response']['games']

    # Fetch genres for each game using Steam's store API
    games_with_genres = []
    for game in games_data:
        # Check if detailed game information including genres is already included
        if 'genre' in game:
            genres = game['genre']
        else:
            # Fetch additional game details to get the genres
            game_details_response = requests.get(f'http://store.steampowered.com/api/appdetails?appids={game["appid"]}&filters=genres')
            game_details = game_details_response.json()[str(game["appid"])]
            if game_details['success']:
                genres = [genre['description'] for genre in game_details['data'].get('genres', [])]
            else:
                genres = ['Unknown']
        
        game['genres'] = genres
        games_with_genres.append(game)

    return jsonify(games_with_genres)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')