from flask import Flask, jsonify, request, redirect, url_for
from flask_pymongo import PyMongo
from flask_cors import CORS
from requests.exceptions import Timeout, RequestException
import requests
import logging
import time
from threading import Thread
from flask import session

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO)

steam_api_key = '2220FF15666E1F4D56AD642BACA6A786'

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://mongo:27017/SteamDB"
app.config['SECRET_KEY'] = 'your_secret_key'
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

# Fetch and store all Steam games in MongoDB
def fetch_all_steam_games():
    logging.info("Starting to fetch all Steam games...")
    response = requests.get(f'http://api.steampowered.com/ISteamApps/GetAppList/v2/')
    if response.status_code == 200:
        all_games_data = response.json()['applist']['apps']
        for game in all_games_data:
            # Only insert if the game is not already in the database
            if not mongo.db.all_games.find_one({'appid': game['appid']}):
                mongo.db.all_games.insert_one({'appid': game['appid'], 'name': game['name'], 'details_fetched': False})
        logging.info("All Steam games have been fetched and stored in MongoDB.")
    else:
        logging.error(f"Failed to fetch all games, status code: {response.status_code}")

@app.route('/steam/fetch_all_games', methods=['GET'])
def fetch_all_games():
    # Trigger the function manually
    fetch_all_steam_games()
    return jsonify({"status": "success"}), 200

# Fetch details for games one by one
def fetch_game_details_continuously():
    count = 0
    while True:
        game = mongo.db.all_games.find_one_and_update({'details_fetched': False}, {'$set': {'details_fetched': True}})
        if game:
            appid = game['appid']
            game_details = fetch_game_details(appid)
            if game_details and game_details[str(appid)]['success']:
                if(game_details[str(appid)]['data'] != []):
                    genres = [genre['description'] for genre in game_details[str(appid)]['data'].get('genres', [])]
                    # Update the game details in the DB
                    mongo.db.all_games.update_one(
                        {'appid': appid},
                        {'$set': {'genres': genres}}
                    )
                    logging.info(f"Fetched and updated details for game {game['name']} (AppID: {appid})")
                else:
                    logging.info(f"No genre data found for game {game['name']} (AppID: {appid})")
            else:
                logging.error(f"Failed to fetch details for game {game['name']} (AppID: {appid})")
            
            count += 1
            if count % 10 == 0:
                total_games = mongo.db.all_games.count_documents({'details_fetched': True})
                logging.info(f"Total games with details fetched in MongoDB: {total_games}")
        else:
            logging.info("No more games to process.")
        time.sleep(2)  # Wait for 2 seconds before fetching the next game's details

# Run the continuous processing in a separate thread (currently disabled)
if __name__ == '__main__':
    # background_thread = Thread(target=fetch_game_details_continuously)
    # background_thread.daemon = True
    # background_thread.start()
    app.run(debug=True, host='0.0.0.0')