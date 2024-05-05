from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
import math

app = Flask(__name__)

@app.route('/')
def index():
    default_settings = {
        'address': '1600 Amphitheatre Parkway, Mountain View, CA',
        'calibers': [
            {'caliber': '5.56', 'bullet_weight': 3.56, 'muzzle_velocity': 990, 'color': 'red'},
            {'caliber': '7.62', 'bullet_weight': 9.33, 'muzzle_velocity': 838, 'color': 'green'},
            {'caliber': '0.308', 'bullet_weight': 10.0, 'muzzle_velocity': 800, 'color': 'blue'}
        ],
        'wind_speed': 5,
        'wind_direction': 180,
        'temperature': 15,
        'humidity': 50,
        'pressure': 1013
    }
    return render_template('index.html', default_settings=default_settings)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data received.'}), 400

    address = data.get('address')
    calibers = data.get('calibers')
    wind_speed = data.get('wind_speed')
    wind_direction = data.get('wind_direction')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    pressure = data.get('pressure')

    if not address or not calibers or not wind_speed or not wind_direction or not temperature or not humidity or not pressure:
        return jsonify({'error': 'Incomplete data received.'}), 400

    # Convert 'calibers' to a list of dictionaries if it's a string
    if isinstance(calibers, str):
        try:
            calibers = json.loads(calibers)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid calibers data.'}), 400

    geolocator = Nominatim(user_agent="shooting_impact_map")
    location = geolocator.geocode(address)
    if not location:
        return jsonify({'error': 'Unable to geocode the provided address.'}), 400

    results = []
    for caliber_info in calibers:
        if not isinstance(caliber_info, dict):
            return jsonify({'error': 'Invalid caliber data.'}), 400
        color = caliber_info.get('color', 'blue')  # Set default color
        for angle in range(0, 360, 45):
            landing_location = calculate_landing_zone(location.latitude, location.longitude, caliber_info['muzzle_velocity'], angle, wind_speed, wind_direction, temperature, humidity, pressure)
            results.append({
                'latitude': landing_location[0],
                'longitude': landing_location[1],
                'label': f'{caliber_info["caliber"]}mm at {angle}°',
                'color': color
            })

    return jsonify(results)
def calculate_landing_zone(latitude, longitude, velocity, angle, wind_speed, wind_direction, temperature, humidity, pressure):
    # Constants
    GRAVITY = 9.81  # Acceleration due to gravity in m/s^2
    AIR_DENSITY = pressure / (287.05 * (temperature + 273.15))  # Air density in kg/m^3

    # Convert angle to radians
    angle_rad = math.radians(angle)

    # Convert wind direction to radians
    wind_direction_rad = math.radians(wind_direction)

    # Calculate wind components affecting the projectile
    wind_speed_x = wind_speed * math.cos(wind_direction_rad - angle_rad)
    wind_speed_y = wind_speed * math.sin(wind_direction_rad - angle_rad)

    # Calculate relative velocity of the projectile
    velocity_x = velocity * math.cos(angle_rad) - wind_speed_x
    velocity_y = velocity * math.sin(angle_rad) - wind_speed_y

    # Calculate time of flight using the horizontal component of velocity
    time_of_flight = (2 * velocity_y) / GRAVITY

    # Calculate horizontal displacement (range) using the horizontal component of velocity
    horizontal_displacement = velocity_x * time_of_flight

    # Calculate vertical displacement (height) using the vertical component of velocity
    vertical_displacement = (velocity_y ** 2) / (2 * GRAVITY)

    # Calculate landing latitude and longitude
    # Assuming Earth is a perfect sphere for simplicity
    EARTH_RADIUS = 6371000  # Earth's radius in meters
    lat_distance = vertical_displacement / EARTH_RADIUS
    lon_distance = horizontal_displacement / (EARTH_RADIUS * math.cos(math.radians(latitude)))

    new_latitude = latitude + math.degrees(lat_distance)
    new_longitude = longitude + math.degrees(lon_distance)

    return (new_latitude, new_longitude)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
