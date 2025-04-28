# Импорт необходимых библиотек
import json
from datetime import datetime, timezone
from haversine import haversine, Unit
from collections import defaultdict

# Загрузка исходного файла
with open('bus_arrivals_filtered.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Группировка данных по автобусу и направлению
grouped_data = defaultdict(list)
for record in data:
    key = (record['bus_id'], record['direction_id'])
    grouped_data[key].append(record)

# Здесь будем собирать сырые результаты
raw_results = defaultdict(list)

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

            key = (stop_a['stop_name'], stop_b['stop_name'])
            raw_results[key].append((time_diff_seconds, speed_kmph))

# Теперь считаем средние значения
final_results = []
for (from_stop, to_stop), trips in raw_results.items():
    avg_time = sum(t[0] for t in trips) / len(trips)
    avg_speed = sum(t[1] for t in trips) / len(trips)

    final_results.append({
        "from_stop": from_stop,
        "to_stop": to_stop,
        "average_travel_time_seconds": avg_time,
        "average_speed_kmph": avg_speed
    })

# Сохраняем результаты в файл
with open('bus_routes_avg_statistics.json', 'w', encoding='utf-8') as f:
    json.dump(final_results, f, indent=4, ensure_ascii=False)

print("✅ Средние расчёты завершены. Результаты сохранены в файл bus_routes_avg_statistics.json")