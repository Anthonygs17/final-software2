import requests
import math
from flask import Flask, request, render_template
from geopy.distance import distance

app = Flask(__name__)


@app.route('/static/<content>')
def static_content(content):
    return render_template(content)

@app.route('/', methods = ['GET'])
def get_index():
    return render_template('index.html')


def getK_restaurants(lat, lon, topK):
    url_places = f'http://nominatim.openstreetmap.org/search?q=restaurant near [{lat},{lon}]&limit={topK}&format=json'
    r_places = requests.get(url_places)
    places_json = r_places.json()

    restaurants = []
    origin = (float(lat), float(lon))

    for element in places_json:
        result = {}
        elem_coord = (float(element['lat']), float(element['lon']))
        result['distance'] = round(distance(origin, elem_coord).meters, 2)
        tmp = element['display_name'].split(", ")
        result['name'] = tmp[0]
        if tmp[1].isnumeric():
            result['house_number'] = tmp[1]
            result['street'] = tmp[2]
        else:
            result['street'] = tmp[1]
        restaurants.append(result)

    return restaurants


def increase_bbox(min_lat, max_lat, min_lon, max_lon, increment):
    lat_increment = increment / 111.0
    lon_increment = increment / (111.0 * math.cos(math.radians((float(min_lat) + float(max_lat)) / 2.0)))

    newminLat = str(float(min_lat) - lat_increment)
    newmaxLat = str(float(max_lat) + lat_increment)
    newminLon = str(float(min_lon) - lon_increment)
    newmaxLon = str(float(max_lon) + lon_increment)
    
    return newminLat, newmaxLat, newminLon, newmaxLon

def get_restaurants_range(min_lat, max_lat, min_lon, max_lon):
    url_places = f'https://api.openstreetmap.org/api/0.6/map.json?bbox={min_lon},{min_lat},{max_lon},{max_lat}'
    r_places = requests.get(url_places)
    places_json = r_places.json()

    restaurants = []
    for element in places_json['elements']:
        if 'tags' in element:
            if 'amenity' in element['tags']:
                if element['tags']['amenity'] == 'restaurant':
                    result = {}
                    if 'name' in element['tags']:
                        result['name'] = element['tags']['name']
                    if 'addr:street' in element['tags']:
                        result['street'] = element['tags']['addr:street']
                    if 'addr:housenumber' in element['tags']:
                        result['house_number'] = element['tags']['addr:housenumber']
                    if 'amenity' in element['tags']:
                        result['amenity'] = element['tags']['amenity']
                    restaurants.append(result)
    
    return restaurants


@app.route('/<place>')
def get_solution(place):
    url = f'https://nominatim.openstreetmap.org/search?q={place}&format=json'
    r_coordinates = requests.get(url)
    jsonData = r_coordinates.json()
    if len(jsonData) == 0:
        return ""
    
    lat_res = jsonData[0]['lat']
    lon_res = jsonData[0]['lon']

    url_weather_daily = f'https://api.open-meteo.com/v1/forecast?latitude={lat_res}&longitude={lon_res}&forecast_days' \
                        f'=2&daily=temperature_2m_max,temperature_2m_min&timezone=GMT'
    
    r_weather = requests.get(url_weather_daily)
    weather_json = r_weather.json()

    response = {}

    temperature = {'max': weather_json['daily']['temperature_2m_max'][0],
                   'min': weather_json['daily']['temperature_2m_min'][0]}

    response['temperature'] = temperature

    if 'topK' in request.args:
        topK = int(request.args.get("topK"))
        response['restaurants'] = getK_restaurants(lat_res, lon_res, topK)
    elif 'radio' in request.args:
        radio = float(request.args.get("radio"))
        minLat = jsonData[0]['boundingbox'][0]
        maxLat = jsonData[0]['boundingbox'][1]
        minLon = jsonData[0]['boundingbox'][2]
        maxLon = jsonData[0]['boundingbox'][3]

        newminLat, newmaxLat, newminLon, newmaxLon = increase_bbox(minLat, maxLat, minLon, maxLon, radio)
        
        response['restaurants'] = get_restaurants_range(newminLat, newmaxLat, newminLon, newmaxLon)
    
    return response


if __name__ == "__main__":
    app.run(debug=False, port=5000)
