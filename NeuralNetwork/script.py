# Подключение библиотек
import cv2  # Библиотека для работы с видео и изображениями
import uuid  # Для генерации уникальных идентификаторов файлов
import os  # Для работы с файловой системой
import json  # Для работы с JSON-форматом данных
import pandas as pd  # Для обработки данных из CSV-файлов
from ultralytics import YOLO  # Библиотека для работы с моделью YOLOv8
from datetime import datetime, timedelta  # Для работы с датой и временем
import math  # Для математических вычислений (например, формула Haversine)
import logging  # Для логирования процесса обработки
import sys  # Для работы с системными параметрами и аргументами командной строки

# Функция настройки логирования
def setup_logging():
    """Настраивает систему логирования для записи сообщений в файл."""
    os.makedirs('LOGS', exist_ok=True)  # Создаём папку LOGS, если её нет
    log_filename = os.path.join('LOGS', datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.txt')  # Формируем имя файла лога с текущей датой и временем
    logging.basicConfig(
        level=logging.INFO,  # Устанавливаем уровень логирования INFO
        format='%(asctime)s - %(levelname)s - %(message)s',  # Формат сообщения: время - уровень - текст
        handlers=[logging.FileHandler(log_filename, encoding='utf-8')]  # Записываем лог в файл с кодировкой UTF-8
    )

# Функция вычисления расстояния между координатами (формула Haversine)
def haversine(lat1, lon1, lat2, lon2):
    """Вычисляет расстояние между двумя точками на сфере по широте и долготе."""
    R = 6371000  # Радиус Земли в метрах
    phi1 = math.radians(lat1)  # Преобразование широты первой точки в радианы
    phi2 = math.radians(lat2)  # Преобразование широты второй точки в радианы
    delta_phi = math.radians(lat2 - lat1)  # Разница широт в радианах
    delta_lambda = math.radians(lon2 - lon1)  # Разница долгот в радианах
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2  # Вычисление a по формуле Haversine
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # Вычисление центрального угла c
    return R * c  # Возвращаем расстояние в метрах

# Основная функция обработки видео
def process_video(video_file_path, road_name, section_of_road, text_file_path, critical_levels_json, road_class, road_category, contractor, model_path=None, save_video=False, display_video=False, frame_skip=1):
    """Обрабатывает видео, детектирует объекты, сохраняет результаты в JSON и изображения."""
    setup_logging()  # Инициализируем логирование
    logger = logging.getLogger()  # Получаем объект логгера
    logger.info("Старт обработки видео")  # Записываем сообщение о начале обработки

    try:
        # Установка пути к модели YOLO, если не указан
        if model_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем директорию текущего скрипта
            model_path = os.path.join(script_dir, 'bestFullM.pt')  # Формируем путь к модели по умолчанию

        # Проверка существования модели
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель {model_path} не найдена")

        # Извлечение имени видео и текстового файла
        video_file_name = os.path.basename(video_file_path)  # Получаем имя файла видео
        text_file_name = os.path.basename(text_file_path)  # Получаем имя текстового файла
        video_name_without_extension = os.path.splitext(video_file_name)[0]  # Убираем расширение из имени видео

        # Обработка уровней критичности из JSON
        try:
            critical_levels_dict = json.loads(critical_levels_json)  # Парсим JSON с уровнями критичности
            logger.info(f"Полученные уровни критичности: {critical_levels_dict}")  # Логируем полученные данные
            class_names = {
                'Плохой сад': 0, 'Загрязнение опоры': 1, 'Стертая разметка': 2,
                'Повреждение опоры': 3, 'Сломанный бордюр': 4, 'Грязная остановка': 5,
                'Трещина': 6, 'Граффити': 7, 'Выбоина': 8, 'Излишки мусора': 9,
                'Заплатка': 10, 'Малая яма': 11
            }  # Словарь имен классов и их индексов
            critical_levels = {class_names[name]: level for name, level in critical_levels_dict.items()}  # Преобразуем имена в индексы
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования critical_levels_json: {str(e)}")  # Логируем ошибку
            critical_levels = {0: 1, 1: 1, 2: 1, 3: 2, 4: 2, 5: 1, 6: 2, 7: 1, 8: 3, 9: 2, 10: 2, 11: 3}  # Значения по умолчанию

        # Логируем все входные параметры
        logger.info(f"Параметры: video_file_path={video_file_path}, road_name={road_name}, "
                    f"section_of_road={section_of_road}, text_file_path={text_file_path}, "
                    f"road_class={road_class}, road_category={road_category}, contractor={contractor}, "
                    f"model_path={model_path}")

        # Загрузка модели YOLOv8
        model = YOLO(model_path)
        model.model.names = {
            0: 'Плохой сад', 1: 'Загрязнение опоры', 2: 'Стертая разметка',
            3: 'Повреждение опоры', 4: 'Сломанный бордюр', 5: 'Грязная остановка',
            6: 'Трещина', 7: 'Граффити', 8: 'Выбоина', 9: 'Излишки мусора',
            10: 'Заплатка', 11: 'Малая яма'
        }  # Устанавливаем имена классов для модели

        # Словарь ярких цветов для прямоугольников (RGB)
        colors = {
            0: (0, 255, 255),   # Яркий жёлтый (Плохой сад)
            1: (255, 0, 255),   # Яркий magenta (Загрязнение опоры)
            2: (255, 255, 0),   # Яркий голубой (Стертая разметка)
            3: (255, 0, 0),     # Яркий красный (Повреждение опоры)
            4: (0, 255, 0),     # Яркий зелёный (Сломанный бордюр)
            5: (0, 0, 255),     # Яркий синий (Грязная остановка)
            6: (255, 255, 255), # Белый (Трещина)
            7: (255, 165, 0),   # Яркий оранжевый (Граффити)
            8: (255, 20, 147),  # Яркий розовый (Выбоина)
            9: (0, 191, 255),   # Яркий голубой (Излишки мусора)
            10: (255, 215, 0),  # Яркий золотой (Заплатка)
            11: (50, 205, 50)   # Яркий лаймовый (Малая яма)
        }

        # Инициализация счётчика объектов по классам
        class_counts = {name: 0 for name in model.model.names.values()}

        # Проверка существования видеофайла
        if not os.path.exists(video_file_path):
            raise FileNotFoundError(f"Видео файл {video_file_path} не найден")

        # Открытие видеофайла
        cap = cv2.VideoCapture(video_file_path)
        if not cap.isOpened():
            raise ValueError("Не удалось открыть видеофайл")

        # Получение параметров видео
        frame_width = int(cap.get(3))   # Ширина кадра
        frame_height = int(cap.get(4))  # Высота кадра
        fps = int(cap.get(5))           # Частота кадров
        final_wide = 800                # Желаемая ширина выходного видео
        r = float(final_wide) / frame_width  # Коэффициент масштабирования
        dim = (final_wide, int(frame_height * r))  # Новые размеры кадра

        # Настройка записи видео, если требуется
        if save_video:
            output_video_path = f'RESULT_VIDEO/{os.path.splitext(video_file_name)[0]}.mp4'  # Путь для сохранения видео
            os.makedirs('RESULT_VIDEO', exist_ok=True)  # Создаём папку RESULT_VIDEO
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Кодек для записи видео
            out = cv2.VideoWriter(output_video_path, fourcc, fps, dim)  # Инициализация объекта записи

        # Формирование пути для сохранения изображений
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Директория скрипта
        output_image_folder = os.path.join(script_dir, "RESULT_IMAGE", video_name_without_extension)  # Путь RESULT_IMAGE/{имя видео без расширения}
        os.makedirs(output_image_folder, exist_ok=True)  # Создаём папку для изображений

        # Создание папки для JSON-результатов
        output_json_folder = 'RESULT_JSON'
        os.makedirs(output_json_folder, exist_ok=True)  # Создаём папку RESULT_JSON

        # Проверка существования текстового файла с координатами
        if not os.path.exists(text_file_path):
            raise FileNotFoundError(f"Текстовый файл {text_file_path} не найден")

        # Чтение координат и времени из CSV
        df = pd.read_csv(text_file_path)  # Загружаем CSV в DataFrame
        df['TIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], format='%d.%m.%Y %H:%M:%S').dt.time  # Преобразуем столбец времени
        start_time = datetime.combine(datetime.today(), df['TIME'].iloc[0])  # Устанавливаем начальное время видео

        # Инициализация переменных для обработки
        total_distance = 0.0  # Общее расстояние
        prev_latitude = None  # Предыдущая широта
        prev_longitude = None  # Предыдущая долгота
        frame_count = 0  # Счётчик кадров
        start_time_utc = datetime.utcnow()  # Время начала обработки
        unique_track_ids = set()  # Множество уникальных ID объектов
        detected_objects = []  # Список обнаруженных объектов

        # Основной цикл обработки кадров
        while True:
            ret, frame = cap.read()  # Читаем очередной кадр
            if not ret:
                break  # Прерываем цикл, если кадры закончились

            frame_count += 1  # Увеличиваем счётчик кадров
            if frame_count % frame_skip != 0:
                continue  # Пропускаем кадры согласно frame_skip

            frame = cv2.resize(frame, dim)  # Масштабируем кадр до заданных размеров
            # Запускаем трекинг объектов с помощью YOLOv8
            results = model.track(frame, iou=0.4, conf=0.5, persist=True, imgsz=608, verbose=False, tracker="botsort.yaml")

            # Обработка результатов детекции
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Координаты bounding box
                    cls = int(box.cls[0])  # Индекс класса объекта
                    confidence = float(box.conf[0])  # Уверенность детекции
                    track_id = int(box.id[0]) if box.id is not None else 'N/A'  # ID объекта для трекинга
                    if track_id == 'N/A':
                        continue  # Пропускаем объекты без ID

                    label = model.model.names[cls]  # Название класса
                    color = colors[cls]  # Цвет прямоугольника для класса
                    critical_level = critical_levels[cls]  # Уровень критичности класса
                    class_counts[label] += 1  # Увеличиваем счётчик объектов данного класса

                    # Рисуем прямоугольник и метку на кадре
                    label_with_id = f'{label} ID:{track_id}'  # Метка с названием класса и ID
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)  # Рисуем яркий прямоугольник толщиной 2 пикселя
                    cv2.putText(frame, label_with_id, (x1, y1 - 10), cv2.FONT_HERSHEY_COMPLEX, 0.4, color, 1)  # Добавляем метку над прямоугольником

                    # Сохранение изображения для нового объекта
                    if track_id not in unique_track_ids:
                        unique_track_ids.add(track_id)  # Добавляем ID в множество уникальных
                        image_name = f'{track_id}_{uuid.uuid4()}.jpg'  # Формируем уникальное имя файла изображения
                        image_path = os.path.join(output_image_folder, image_name)  # Полный путь для сохранения изображения
                        object_frame = frame.copy()  # Копируем кадр для сохранения
                        cv2.imwrite(image_path, object_frame)  # Сохраняем изображение
                        logger.info(f"Изображение сохранено: {image_path}, track_id={track_id}, class={label}")  # Логируем сохранение

                        # Определяем временную метку для кадра
                        current_time = start_time + timedelta(seconds=frame_count // fps)  # Текущее время кадра
                        closest_time = min(df['TIME'], key=lambda x: abs((datetime.combine(datetime.today(), x) - current_time).total_seconds()))  # Находим ближайшее время в CSV
                        closest_row = df[df['TIME'] == closest_time].iloc[0]  # Получаем строку с ближайшим временем
                        latitude = closest_row['LATITUDE']  # Широта
                        longitude = closest_row['LONGITUDE']  # Долгота

                        # Добавляем объект в список результатов
                        detected_objects.append({
                            "Object_id": track_id,
                            "Title": road_name,
                            "SectionOfRoad": section_of_road,
                            "ImageName": image_name,
                            "VideoName": video_file_name,
                            "ClassName": label,
                            "Latitude": latitude,
                            "Longitude": longitude,
                            "Status": "new",
                            "CriticalLevel": critical_level,
                            "RoadClass": road_class,
                            "RoadCategory": road_category,
                            "Contractor": contractor,
                            "DateTimeDetection": datetime.utcnow().isoformat() + "Z"  # Время обнаружения в формате ISO 8601
                        })

            # Вычисление координат для текущего кадра
            current_time = start_time + timedelta(seconds=frame_count // fps)  # Текущее время кадра
            closest_time = min(df['TIME'], key=lambda x: abs((datetime.combine(datetime.today(), x) - current_time).total_seconds()))  # Находим ближайшее время
            closest_row = df[df['TIME'] == closest_time].iloc[0]  # Получаем строку с координатами
            latitude = closest_row['LATITUDE']  # Широта
            longitude = closest_row['LONGITUDE']  # Долгота

            # Подсчёт общего расстояния
            if prev_latitude is not None and prev_longitude is not None:
                total_distance += haversine(prev_latitude, prev_longitude, latitude, longitude)  # Добавляем расстояние между точками
            prev_latitude = latitude  # Обновляем предыдущую широту
            prev_longitude = longitude  # Обновляем предыдущую долготу

            # Запись кадра в видео, если включено сохранение
            if save_video:
                out.write(frame)
            # Отображение кадра, если включён просмотр
            if display_video:
                cv2.imshow('YOLOv8 Object Detection', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):  # Выход по нажатию 'q'
                    break

        # Освобождение ресурсов
        cap.release()  # Закрываем видеофайл
        if save_video:
            out.release()  # Закрываем запись видео
        cv2.destroyAllWindows()  # Закрываем окна OpenCV

        # Сохранение списка обнаруженных объектов в JSON
        json_file_path = os.path.join(output_json_folder, f'{os.path.splitext(video_file_name)[0]}.json')  # Путь к JSON-файлу объектов
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(detected_objects, json_file, ensure_ascii=False, indent=4)  # Записываем объекты в JSON

        # Формирование итоговых данных
        end_time_utc = datetime.utcnow()  # Время окончания обработки
        summary_data = {
            "VideoName": video_file_name,
            "RoadName": road_name,
            "SectionOfRoad": section_of_road,
            "RoadClass": road_class,
            "RoadCategory": road_category,
            "Contractor": contractor,
            "ClassCounts": class_counts,
            "TotalObjects": sum(class_counts.values()),
            "TotalDistance": total_distance,
            "ProcessingTime": str(end_time_utc - start_time_utc),
            "Status": "success"
        }  # Итоговые данные обработки

        # Сохранение итоговых данных в JSON
        summary_file_path = os.path.join(output_json_folder, f'{os.path.splitext(video_file_name)[0]}_summary.json')  # Путь к summary JSON
        with open(summary_file_path, 'w', encoding='utf-8') as summary_file:
            json.dump(summary_data, summary_file, ensure_ascii=False, indent=4)  # Записываем итоговые данные
        logger.info(f"Создан summary JSON файл: {summary_file_path}")  # Логируем создание файла

        # Возвращаем результат в формате JSON
        return json.dumps(summary_data, ensure_ascii=False).encode('utf8')

    except Exception as e:
        # Обработка ошибок
        logger.error(f"Ошибка: {str(e)}", exc_info=True)  # Логируем ошибку с трассировкой
        error_data = {
            "VideoName": os.path.basename(video_file_path) if 'video_file_path' in locals() else "",
            "RoadName": road_name,
            "SectionOfRoad": section_of_road,
            "RoadClass": road_class,
            "RoadCategory": road_category,
            "Contractor": contractor,
            "ClassCounts": {},
            "TotalObjects": 0,
            "TotalDistance": 0.0,
            "ProcessingTime": "0:00:00",
            "Status": "error",
            "Error": str(e)
        }  # Формируем данные об ошибке
        if 'video_file_name' in locals():
            summary_file_path = os.path.join('RESULT_JSON', f'{os.path.splitext(video_file_name)[0]}_summary.json')
            with open(summary_file_path, 'w', encoding='utf-8') as summary_file:
                json.dump(error_data, summary_file, ensure_ascii=False, indent=4)  # Записываем данные об ошибке
            logger.info(f"Создан summary JSON файл с ошибкой: {summary_file_path}")
        return json.dumps(error_data, ensure_ascii=False).encode('utf8')  # Возвращаем данные об ошибке

# Точка входа скрипта
if __name__ == "__main__":
    # Проверка наличия аргумента с путём к JSON-файлу параметров
    if len(sys.argv) < 2:
        print("Ошибка: Не указан путь к JSON-файлу с параметрами")
        sys.exit(1)

    json_file_path = sys.argv[1]  # Получаем путь к JSON-файлу из аргументов
    with open(json_file_path, 'r', encoding='utf-8') as f:
        params = json.load(f)  # Читаем параметры из JSON

    # Извлечение параметров из JSON
    road_name = params.get("RoadName", "")  # Название дороги
    section_of_road = params.get("SectionOfRoad", "")  # Участок дороги
    video_file_path = params.get("VideoFilePath", "")  # Путь к видеофайлу
    text_file_path = params.get("TextFilePath", "")  # Путь к CSV-файлу
    critical_levels_json = params.get("CriticalLevels", "{}")  # Уровни критичности в JSON
    road_class = params.get("RoadClass", "")  # Класс дороги
    road_category = params.get("RoadCategory", "")  # Категория дороги
    contractor = params.get("Contractor", "")  # Подрядчик

    # Запуск обработки видео с полученными параметрами
    result = process_video(video_file_path, road_name, section_of_road, text_file_path, critical_levels_json, road_class, road_category, contractor)
    sys.stdout.buffer.write(result)  # Вывод результата в stdout