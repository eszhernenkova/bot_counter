from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os

app = Flask(__name__)

global_total = 0
last_match_kills = 0

# При старте — пытаемся загрузить сохранённое значение
try:
    with open("kills_count.txt", "r", encoding="utf-8") as f:
        global_total = int(f.read().strip())
except Exception:
    global_total = 0

@app.route('/static/fonts/led_board-7')
def serve_fonts(filename):
    # Раздаём шрифты напрямую, если лежат в /static/fonts/
    return send_from_directory(os.path.join(app.root_path, 'static', 'fonts'), filename)

@app.route('/')
def index():
    # HTML со стилями под LED-табло
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>LED Kill Counter</title>
        <style>
          /* Подключаем кастомный шрифт */
          @font-face {
            font-family: 'LedCounter';
            src: url('/static/fonts/led_board-7.ttf') format('truetype');
            font-weight: normal;
            font-style: normal;
          }

          body {
            margin: 0;
            padding: 0;
            background: transparent; /* Для OBS — прозрачный фон */
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh; /* Чтобы текст был по центру */
            background: black;
          }
          #led-display {
            font-family: 'LedCounter', monospace;
            font-size: 120px;       /* Размер цифр */
            color: #ff9900;         /* Оранжевый цвет */
            letter-spacing: 5px;    /* Расстояние между цифрами */
            text-shadow: 0 0 10px #ff9900; /* Свечение */
            background: url('/static/img/bgsf.png');
            background-repeat: no-repeat;
            background-size: 96.5%;
            background-position: left center;
          }
        </style>
      </head>
      <body>
        <div id="led-display">{{ total }}</div>
        <script>
          // Функция для запроса актуального счётчика
          function fetchKills() {
            fetch('/api/kills')
              .then(response => response.json())
              .then(data => {
                document.getElementById('led-display').textContent = data.kill_count;
              })
              .catch(err => console.error(err));
          }
          setInterval(fetchKills, 500); // Обновляем каждые 500мс
          fetchKills();
        </script>
      </body>
    </html>
    """
    return render_template_string(html, total=global_total)

@app.route('/api/kills', methods=['GET'])
def get_kills():
    # Здесь форматируем число на 6 знаков
    padded_value = f"{global_total:07d}"
    return jsonify({"kill_count": padded_value})

@app.route('/csgo', methods=['POST'])
def csgo_data():
    global global_total, last_match_kills
    data = request.get_json(force=True)
    print("Получены данные:", data)

    if "player" in data and "match_stats" in data["player"]:
        new_match_kills = data["player"]["match_stats"].get("kills", 0)

        if new_match_kills < last_match_kills:
            # Сброс статистики (перезапуск карты)
            print("Обнаружен сброс статистики. last_match_kills:", last_match_kills, "->", new_match_kills)
            last_match_kills = new_match_kills
        else:
            diff = new_match_kills - last_match_kills
            if diff > 0:
                global_total += diff
                last_match_kills = new_match_kills
                with open("kills_count.txt", "w", encoding="utf-8") as f:
                    f.write(str(global_total))
                print("Добавлено", diff, "убийств. Новый общий счет:", global_total)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
