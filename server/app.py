from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_cors import CORS

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://mongo:27017/SteamDB"
mongo = PyMongo(app)
CORS(app)

@app.route('/games/add', methods=['POST'])
def add_game():
    game_name = request.json['name']
    mongo.db.games.insert_one({'name': game_name})
    return jsonify(message="Game added successfully"), 201

@app.route('/games/delete', methods=['POST'])
def delete_game():
    game_name = request.json['name']
    result = mongo.db.games.delete_one({'name': game_name})
    if result.deleted_count > 0:
        return jsonify(message="Game deleted successfully"), 200
    else:
        return jsonify(message="No game found with that name"), 404

@app.route('/games')
def get_games():
    games = mongo.db.games.find()
    games_list = [{'name': game['name']} for game in games]
    return jsonify(games_list)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')