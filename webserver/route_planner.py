from flask import Flask, request
from geopy.geocoders import Nominatim
from flask_cors import CORS
import redis
import json
import subprocess


app = Flask(__name__)
CORS(app, supports_credentials=True)
redis_server = redis.Redis(host="localhost")

geolocator = Nominatim(user_agent="my_request")
region = ", Lund, Skåne, Sweden"

@app.route('/planner', methods=['POST'])
def route_planner():
    Addresses =  json.loads(request.data.decode())
    ToAddress = Addresses['taddr']

    home_location = (float(redis_server.get('longitude')), float(redis_server.get('latitude')))
    print(home_location)
    to_location = geolocator.geocode(ToAddress + region)

    if home_location is None:
        message = 'Departure address not found, please input a correct address'
    elif to_location is None:
        message = 'Destination address not found, please input a correct address'
    else:
        message = 'Get address! Start moving'
        # Skickar task till redis
        redis_server.rpush('drone_tasks', json.dumps((to_location.longitude, to_location.latitude)))
    return message

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port='5002')
