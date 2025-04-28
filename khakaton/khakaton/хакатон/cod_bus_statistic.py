# Импорт необходимых библиотек
import json
from datetime import datetime
from datetime import datetime, timezone
from haversine import haversine, Unit

# Загрузка исходного файла
with open('bus_arrivals_filtered.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Группировка данных по автобусу и направлению
from collections import defaultdict

grouped_data = defaultdict(list)

for record in data:
    key = (record['bus_id'], record['direction_id'])
    grouped_data[key].append(record)

# Здесь будем собирать результаты
results = []

# Проход по каждой группе (автобус + направление)
for (bus_id, direction_id), records in grouped_data.items():
    # Сортируем записи по времени
    records_sorted = sorted(records, key=lambda x: x['timestamp'])

    # Отбираем только те записи, где автобус был близко к остановке
    stops = [rec for rec in records_sorted if rec['distance'] <= 30]

    # Проходим по парам остановок
    for i in range(len(stops) - 1):
        stop_a = stops[i]
        stop_b = stops[i + 1]

        # Переводим timestamp в datetime для удобства
        time_a = datetime.fromtimestamp(stop_a['timestamp'], tz=timezone.utc)
        time_b = datetime.fromtimestamp(stop_b['timestamp'], tz=timezone.utc)
        # Считаем разницу во времени в секундах
        time_diff_seconds = (time_b - time_a).total_seconds()

        # Координаты остановок
        coord_a = (stop_a['stop_coordinates']['lat'], stop_a['stop_coordinates']['lon'])
        coord_b = (stop_b['stop_coordinates']['lat'], stop_b['stop_coordinates']['lon'])

        # Расстояние между остановками в метрах
        distance_meters = haversine(coord_a, coord_b, unit=Unit.METERS)

        # Вычисляем среднюю скорость (м/с и км/ч)
        if time_diff_seconds > 0:
            speed_mps = distance_meters / time_diff_seconds   # м/с
            speed_kmph = speed_mps * 3.6                      # км/ч
        else:
            speed_mps = 0
            speed_kmph = 0

        # Сохраняем результат
        results.append({
            "bus_id": bus_id,
            "direction_id": direction_id,
            "from_stop": stop_a['stop_name'],
            "to_stop": stop_b['stop_name'],
            "departure_time": stop_a['datetime'],
            "arrival_time": stop_b['datetime'],
            "travel_time_seconds": time_diff_seconds,
            "distance_meters": distance_meters,
            "average_speed_kmph": speed_kmph
        })

# Сохраняем результаты в файл
with open('bus_routes_statistics.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("✅ Расчёты завершены. Результаты сохранены в файл bus_routes_statistics.json")