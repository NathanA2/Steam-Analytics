from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS

app = Flask(__name__)
#app.config["MONGO_URI"] = "mongodb://mongo:27017/SteamDB"
CORS(app)

#mongo = PyMongo(app)

@app.route('/')
def hello_world():
    return 'Hello, World from MongoDB!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')