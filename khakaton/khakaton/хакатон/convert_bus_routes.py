import json
import re
import folium
import csv
import os


def parse_point(point_str):
    match = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", point_str)
    if match:
        lon, lat = map(float, match.groups())
        return {"lat": lat, "lon": lon}
    return {}


def extract_stops(direction):
    stops = []
    platforms = direction.get("platforms", [])
    for platform in platforms:
        stop_name = platform.get("name")
        point_str = platform.get("geometry", {}).get("centroid")
        if stop_name and point_str:
            coordinates = parse_point(point_str)
            stops.append({
                "name": stop_name,
                "coordinates": coordinates
            })
    return stops


def convert_routes(input_data):
    converted = {"routes": []}
    items = input_data.get("result", {}).get("items", [])

    for item in items:
        route_name = f"автобус {item.get('name', '')}"
        route_id = item.get("id")
        to_name = item.get("to_name")
        directions = item.get("directions", [])

        for direction in directions:
            route_direction = f"До ост. {to_name}" if direction.get(
                "type") == "forward" else f"Обратно от ост. {to_name}"
            stops = extract_stops(direction)
            converted["routes"].append({
                "route_name": route_name,
                "route_direction": route_direction,
                "route_id": route_id,
                "stops": stops
            })

    return converted


# Загрузка исходного JSON
with open("all.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Конвертация
converted_data = convert_routes(data)

# Сохранение результата в output.json
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(converted_data, f, indent=4, ensure_ascii=False)

# Отображение на карте
first_route = converted_data["routes"][0]
map_center = first_route["stops"][0]["coordinates"]
m = folium.Map(location=[map_center["lat"], map_center["lon"]], zoom_start=13)

for route in converted_data["routes"]:
    for stop in route["stops"]:
        folium.Marker(
            [stop["coordinates"]["lat"], stop["coordinates"]["lon"]],
            popup=stop["name"],
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

m.save("map_with_stops.html")

# Генерация GTFS: stops.txt и trips.txt
os.makedirs("gtfs", exist_ok=True)

# stops.txt
with open("gtfs/stops.txt", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["stop_id", "stop_name", "stop_lat", "stop_lon"])
    stop_id = 1
    unique_stops = {}
    for route in converted_data["routes"]:
        for stop in route["stops"]:
            key = (stop["name"], stop["coordinates"]["lat"], stop["coordinates"]["lon"])
            if key not in unique_stops:
                unique_stops[key] = stop_id
                writer.writerow([stop_id, stop["name"], stop["coordinates"]["lat"], stop["coordinates"]["lon"]])
                stop_id += 1

# trips.txt
with open("gtfs/trips.txt", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["route_id", "trip_id", "trip_headsign"])
    trip_id = 1
    for route in converted_data["routes"]:
        writer.writerow([route["route_id"], trip_id, route["route_direction"]])
        trip_id += 1

print(" Готово! Карта сохранена в 'map_with_stops.html', GTFS-файлы — в папке 'gtfs/'.")