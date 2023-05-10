import math
import requests
import argparse
import time
import redis
import json

def get_movement(src, dst):
    speed = 0.00001
    dst_x, dst_y = dst
    x, y = src
    direction = math.sqrt((dst_x - x)**2 + (dst_y - y)**2)
    longitude_move = speed * ((dst_x - x) / direction )
    latitude_move = speed * ((dst_y - y) / direction )
    return longitude_move, latitude_move

def move_drone(src, d_long, d_la):
    x, y = src
    x = x + d_long
    y = y + d_la        
    return (x, y)

def plan_path(current_coords, to_coords):
    home_coords = current_coords
    drone_coords = home_coords
    path = []
    
    d_long, d_la = get_movement(drone_coords, to_coords)
    while ((to_coords[0] - drone_coords[0])**2 + (to_coords[1] - drone_coords[1])**2)*10**6 > 0.0002:
        drone_coords = move_drone(drone_coords, d_long, d_la)
        path.append(drone_coords)
        d_long, d_la = get_movement(drone_coords, to_coords)

    time.sleep(1)

    d_long, d_la = get_movement(drone_coords, home_coords)
    while ((home_coords[0] - drone_coords[0])**2 + (home_coords[1] - drone_coords[1])**2)*10**6 > 0.0002:
        drone_coords = move_drone(drone_coords, d_long, d_la)
        path.append(drone_coords)
        d_long, d_la = get_movement(drone_coords, home_coords)

    return path

def your_function(current_coords, to_coords):
    path = plan_path(current_coords, to_coords)
    for drone_coords in path:
        yield drone_coords

def run(current_coords, to_coords, SERVER_URL, drone_id):
    for drone_coords in your_function(current_coords, to_coords):
        with requests.Session() as session:
            drone_location = {'longitude': drone_coords[0],
                              'latitude': drone_coords[1]
                            }
            resp = session.post(f"{SERVER_URL}/{drone_id}", json=drone_location)
    redis_server.set(f'drone{drone_id}_status', 'idle')  # Set drone status to idle after completing task

if __name__ == "__main__":
    SERVER_URL = "http://127.0.0.1:5001/drone"
    redis_server = redis.Redis(host="localhost")
    

    parser = argparse.ArgumentParser()
    parser.add_argument("--drone_id", help='drone id', type=int)
    args = parser.parse_args()
    drone_id = args.drone_id

    # Get initial coordinates from Redis
    home_coords = (float(redis_server.get(f'drone{drone_id}_longitude')), float(redis_server.get(f'drone{drone_id}_latitude')))
    print(home_coords)

    while True:
        task = redis_server.blpop('drone_tasks', 0)  # Fetch a task from the queue, waits if queue is empty
        if task:
            to_coords = json.loads(task[1])
            print(to_coords)
            redis_server.set(f'drone{drone_id}_status', 'busy')  # Set drone status to busy before starting task
            run(home_coords, to_coords, SERVER_URL, drone_id)
        time.sleep(1)
