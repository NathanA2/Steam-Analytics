from flask import Flask, jsonify, request, redirect, url_for
from flask_pymongo import PyMongo
from flask_cors import CORS
from requests.exceptions import Timeout, RequestException
import requests
import logging
from flask import session
import numpy as np
import pandas as pd
import time
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

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
    try:
        response = requests.get(f'http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={steam_api_key}&steamid={steam_id}&format=json')
        response.raise_for_status()
        games_data = response.json().get('response', {}).get('games', [])
        return jsonify(games_data)
    except RequestException as e:
        logging.error(f"Failed to fetch recently played games for Steam ID {steam_id}, Error: {e}")
        return jsonify({"error": "Failed to fetch recently played games."}), 500

def fetch_genre_details(appid):
    url = f'http://store.steampowered.com/api/appdetails?appids={appid}&filters=genres'
    while True:
        try:
            response = requests.get(url, timeout=10)  # 10 seconds timeout
            response.raise_for_status()
            return response.json()
        except Timeout:
            logging.error(f"Request timed out for AppID: {appid}")
        except RequestException as e:
            if '429 Client Error: Too Many Requests' in str(e):
                logging.warning(f"Too Many Requests for AppID: {appid}, retrying...")
                time.sleep(20)
                continue
            logging.error(f"Request failed for AppID: {appid}, Error: {e}")
        return None

def fetch_review_details(appid):
    url = f'https://store.steampowered.com/appreviews/{appid}?json=1&language=all'
    while True:
        try:
            response = requests.get(url, timeout=10)  # 10 seconds timeout
            response.raise_for_status()
            return response.json()
        except Timeout:
            logging.error(f"Request timed out for AppID: {appid}")
        except RequestException as e:
            if '429 Client Error: Too Many Requests' in str(e):
                logging.warning(f"Too Many Requests for AppID: {appid}, retrying...")
                time.sleep(20)
                continue
            logging.error(f"Request failed for AppID: {appid}, Error: {e}")
        return None

@app.route('/steam/all_games_genres/<steam_id>')
def get_games_genres(steam_id):
    try:
        games_response = requests.get(f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_api_key}&steamid={steam_id}&include_appinfo=true&format=json')
        games_response.raise_for_status()
        games_data = [game for game in games_response.json().get('response', {}).get('games', []) if game['appid'] % 10 == 0]
    except RequestException as e:
        logging.error(f"Failed to fetch owned games for Steam ID {steam_id}, Error: {e}")
        return jsonify({"error": "Failed to fetch owned games."}), 500

    games_with_genres = []
    for game in games_data:
        try:
            appid = game['appid']
            logging.info(f"Processing game {game['name']} (AppID: {appid})")

            # Check if appid is in the error log collection
            error_record = mongo.db.error_games.find_one({'appid': appid})
            if error_record:
                logging.info(f"Skipping game {game['name']} (AppID: {appid}) due to previous errors")
                continue

            game_record = mongo.db.games.find_one({'appid': appid})
            if game_record and 'genres' in game_record and game_record['genres'] != ['Unknown'] and 'review_score' in game_record:
                logging.info(f"Pulled data from database for game {game['name']} (AppID: {appid})")
                game['genres'] = game_record['genres']
                game['review_score'] = game_record['review_score']
            else:
                logging.info(f"Fetching new data from API for game {game['name']} (AppID: {appid})")
                # Fetch genre details
                genres_details = fetch_genre_details(appid)
                if genres_details and genres_details.get(str(appid), {}).get('success', False):
                    genres = [genre['description'] for genre in genres_details[str(appid)]['data'].get('genres', [])]
                else:
                    genres = ['Unknown']

                # Fetch review details
                review_details = fetch_review_details(appid)
                if review_details and review_details.get('success', 0) == 1:
                    total_positive = review_details['query_summary'].get('total_positive', 0)
                    total_reviews = review_details['query_summary'].get('total_reviews', 1)  # Avoid division by zero
                    review_score = round((total_positive / total_reviews) * 100, 2)
                    game['review_score'] = f'{review_score}%' if total_reviews > 1 else 'N/A'
                else:
                    game['review_score'] = 'N/A'

                game['genres'] = genres
                # Update the database with new information
                mongo.db.games.update_one({'appid': appid}, {'$set': {'genres': genres, 'review_score': game['review_score']}}, upsert=True)

            games_with_genres.append(game)
        except KeyError as e:
            logging.error(f"Missing key in game data for AppID: {game.get('appid', 'Unknown')}, Error: {e}")
            mongo.db.error_games.update_one({'appid': appid}, {'$set': {'error': str(e)}}, upsert=True)
        except Exception as e:
            logging.error(f"Unexpected error while processing game {game.get('name', 'Unknown')} (AppID: {game.get('appid', 'Unknown')}), Error: {e}")
            if 'division by zero' in str(e).lower() or "'list' object has no attribute 'get'" in str(e).lower():
                mongo.db.error_games.update_one({'appid': appid}, {'$set': {'error': str(e)}}, upsert=True)

    logging.info(f"Finished Processing Games")
    return jsonify(games_with_genres)

@app.route('/steam/all_steam_games_genres')
def get_all_steam_games_genres():
    try:
        games_response = requests.get('http://api.steampowered.com/ISteamApps/GetAppList/v2/')
        games_response.raise_for_status()
        games_data = [game for game in games_response.json().get('applist', {}).get('apps', []) if game['appid'] % 10 == 0]
    except RequestException as e:
        logging.error(f"Failed to fetch all Steam games, Error: {e}")
        return jsonify({"error": "Failed to fetch all Steam games."}), 500

    games_with_genres = []
    for game in games_data:
        try:
            appid = game['appid']
            logging.info(f"Processing game {game['name']} (AppID: {appid})")

            # Check if appid is in the error log collection
            error_record = mongo.db.error_games.find_one({'appid': appid})
            if error_record:
                logging.info(f"Skipping game {game['name']} (AppID: {appid}) due to previous errors")
                continue

            game_record = mongo.db.games.find_one({'appid': appid})
            if game_record and 'genres' in game_record and game_record['genres'] != ['Unknown'] and 'review_score' in game_record:
                logging.info(f"Pulled data from database for game {game['name']} (AppID: {appid})")
                game['genres'] = game_record['genres']
                game['review_score'] = game_record['review_score']
            else:
                logging.info(f"Fetching new data from API for game {game['name']} (AppID: {appid})")
                # Fetch genre details
                genres_details = fetch_genre_details(appid)
                if genres_details and genres_details.get(str(appid), {}).get('success', False):
                    genres = [genre['description'] for genre in genres_details[str(appid)]['data'].get('genres', [])]
                else:
                    genres = ['Unknown']

                # Fetch review details
                review_details = fetch_review_details(appid)
                if review_details and review_details.get('success', 0) == 1:
                    total_positive = review_details['query_summary'].get('total_positive', 0)
                    total_reviews = review_details['query_summary'].get('total_reviews', 1)  # Avoid division by zero
                    review_score = round((total_positive / total_reviews) * 100, 2)
                    game['review_score'] = f'{review_score}%' if total_reviews > 1 else 'N/A'
                else:
                    game['review_score'] = 'N/A'

                game['genres'] = genres
                # Update the database with new information
                mongo.db.games.update_one({'appid': appid}, {'$set': {'genres': genres, 'review_score': game['review_score']}}, upsert=True)

            games_with_genres.append(game)
        except KeyError as e:
            logging.error(f"Missing key in game data for AppID: {game.get('appid', 'Unknown')}, Error: {e}")
            mongo.db.error_games.update_one({'appid': appid}, {'$set': {'error': str(e)}}, upsert=True)
        except Exception as e:
            logging.error(f"Unexpected error while processing game {game.get('name', 'Unknown')} (AppID: {game.get('appid', 'Unknown')}), Error: {e}")
            if 'division by zero' in str(e).lower() or "'list' object has no attribute 'get'" in str(e).lower():
                mongo.db.error_games.update_one({'appid': appid}, {'$set': {'error': str(e)}}, upsert=True)

    logging.info(f"Finished Processing All Steam Games")
    return jsonify(games_with_genres)

@app.route('/steam/predict_games/<steam_id>', methods=['GET'])
def predict_game_recommendations(steam_id):
    try:
        # Step 1: Fetch user games data from MongoDB
        logging.info("Step 1: Fetching user games data from MongoDB")
        user_games = list(mongo.db.games.find({}))
        if not user_games:
            logging.info("No games found in database")
            return jsonify({"error": "No games found in database."}), 404

        # Convert to DataFrame
        user_games_df = pd.DataFrame(user_games)
        logging.info("User games data converted to DataFrame")

        # Step 2: Fetch playtime data from Steam API for the user
        logging.info("Step 2: Fetching playtime data from Steam API")
        response = requests.get(f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_api_key}&steamid={steam_id}&include_appinfo=true&format=json')
        response.raise_for_status()
        games_data = response.json().get('response', {}).get('games', [])

        # Add playtime data to DataFrame
        playtime_dict = {game['appid']: game['playtime_forever'] for game in games_data}
        user_games_df['playtime_forever'] = user_games_df['appid'].apply(lambda x: playtime_dict.get(x, 0))
        logging.info("Playtime data added to DataFrame")

        user_games_df = user_games_df[~user_games_df['genres'].str.contains('Unknown', na=False)]
        user_games_df = user_games_df.dropna(subset=['review_score'])
        user_games_df = user_games_df[user_games_df['review_score'].str.match(r'^\d+(\.\d+)?%$', na=False)]
        user_games_df = user_games_df.drop(['_id'], axis=1)
        user_games_df['review_score'] = user_games_df['review_score'].str.replace('%', '').astype(float)

        # Step 3: Preprocess Data (One-Hot Encode genres)
        logging.info("Step 3: Preprocessing data")
        # One-Hot Encoding genres
        if 'genres' in user_games_df.columns:
            genres = user_games_df['genres'].apply(lambda x: x if isinstance(x, list) else ['Unknown'])
            user_games_df = user_games_df.join(pd.get_dummies(genres.apply(pd.Series).stack()).groupby(level=0).max())
        else:
            logging.warning("'genres' column missing. Defaulting to 'Unknown' for all games.")
            user_games_df['Unknown'] = 1

        logging.info(f"Data after One-Hot Encoding genres and processing review_score: {user_games_df}")

        # Create a backup of the full dataset before removing games with zero playtime
        full_games_df = user_games_df.copy()
        full_games_df = full_games_df[full_games_df['playtime_forever'] == 0]

        # Step 4: Filter games with non-zero playtime
        user_games_df = user_games_df[user_games_df['playtime_forever'] > 0]
        logging.info(f"Filtered games with non-zero playtime: {len(user_games_df)} games remaining")

        # Check if there are enough games to proceed
        if user_games_df.empty:
            logging.error("No games with non-zero playtime available for training.")
            return jsonify({"error": "No games with non-zero playtime available for training."}), 400

        # Debugging: Log available columns
        logging.info(f"Available columns in user_games_df: {user_games_df.columns.tolist()}")

        # Step 5: Prepare Features and Target
        logging.info("Step 5: Preparing features and target")
        # Create a copy of the DataFrame without non-relevant columns
        train_df = user_games_df.drop(columns=['appid', 'genres', 'playtime_forever'])

        features = [col for col in train_df.columns if col != 'review_score']
        X = train_df[features + ['review_score']]
        y = user_games_df['playtime_forever']
        logging.info(f"Features: {X.head()}\nTarget: {y.head()}")
        logging.info("Features and target prepared")

        # Step 6: Train-Test Split
        logging.info("Step 6: Splitting data into training and testing sets")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        logging.info(f"X_train: {X_train.head()}\nX_test: {X_test.head()}")
        logging.info("Data split into training and testing sets")

        # Step 7: Setup Pipeline and Train Model
        logging.info("Step 7: Setting up pipeline and training model")
        preprocessor = ColumnTransformer(
            transformers=[
                ('review_score', StandardScaler(), ['review_score'])
            ],
            remainder='passthrough'
        )

        model_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', RandomForestRegressor(n_estimators=100, random_state=42))
        ])
        
        # Fitting the model
        try:
            model_pipeline.fit(X_train, y_train)
            logging.info("Model trained successfully")
        except Exception as e:
            logging.error(f"Error during model training: {e}")
            return jsonify({"error": "Error during model training."}), 500

        # Step 8: Predict and Evaluate
        logging.info("Step 8: Predicting and evaluating model")
        try:
            y_pred = model_pipeline.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            logging.info(f"Mean Squared Error for predictions: {mse}")
        except Exception as e:
            logging.error(f"Error during prediction: {e}")
            return jsonify({"error": "Error during prediction."}), 500

        # Step 9: Get recommendations (use the trained model to predict playtime)
        logging.info("Step 9: Getting recommendations")
        try:
            X_full = full_games_df.drop(columns=['appid', 'genres', 'playtime_forever'])
            X_transformed = model_pipeline.named_steps['preprocessor'].transform(X_full)
            logging.info(f"Columns after StandardScaler (full dataset): {X_transformed[:5]}")
            recommendations = full_games_df.copy()
            recommendations['predicted_playtime'] = model_pipeline.predict(X_full)
            recommendations = recommendations.sort_values(by='predicted_playtime', ascending=False)
            logging.info("Recommendations generated")
        except Exception as e:
            logging.error(f"Error during recommendation generation: {e}")
            return jsonify({"error": "Error during recommendation generation."}), 500

        # Step 10: Retrieve game names via API call and format the response
        logging.info("Step 10: Retrieving game names and formatting response")
        recommended_games = []
        for index, row in recommendations.head(5).iterrows():
            appid = row['appid']
            try:
                game_details_response = requests.get(f'https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic')
                game_details_response.raise_for_status()
                game_details = game_details_response.json().get(str(appid), {}).get('data', {})
                game_name = game_details.get('name', 'Unknown Game')
                recommended_games.append({
                    'name': game_name,
                    'predicted_playtime': row['predicted_playtime']
                })
                logging.info(f"Retrieved game name for AppID {appid}: {game_name}")
            except RequestException as e:
                logging.error(f"Failed to fetch game details for AppID {appid}, Error: {e}")
                recommended_games.append({
                    'name': 'Unknown Game',
                    'predicted_playtime': row['predicted_playtime']
                })

        logging.info("Response ready to be sent")
        return jsonify(recommended_games)
    except RequestException as e:
        logging.error(f"Failed to predict games for Steam ID {steam_id}, Error: {e}")
        return jsonify({"error": "Failed to predict games."}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500
    
# Function to clean up MongoDB entries
@app.route('/steam/cleanup_games', methods=['POST'])
def cleanup_games():
    try:
        logging.info("Cleaning up games in MongoDB")
        result = mongo.db.games.delete_many({
            "$or": [
                {"review_score": {"$not": {"$type": "string"}}},
                {"review_score": {"$not": {"$regex": r'^\d+(\.\d+)?%$'}}},
                {"genres": {"$size": 1, "$in": ["Unknown"]}}
            ]
        })
        logging.info(f"Deleted {result.deleted_count} entries from MongoDB")
        return jsonify({"message": f"Deleted {result.deleted_count} invalid entries from the database."})
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
        return jsonify({"error": "An unexpected error occurred during cleanup."}), 500

# Run the continuous processing in a separate thread (currently disabled)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')