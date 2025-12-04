# build_db.py

# Импортируем необходимые библиотеки:
# numpy - для работы с числовыми массивами и математическими операциями
import numpy as np
# datasets - для загрузки стандартных датасетов (включая MNIST)
# transforms - для преобразований изображений
from torchvision import datasets, transforms
# Импортируем функции для работы с подключением к базе данных
from utils.db import get_conn, put_conn


def ds_to_arrays(ds):
    """
    Преобразует датасет PyTorch в массивы numpy.

    Args:
        ds: PyTorch Dataset объект (MNIST датасет)

    Returns:
        tuple: (X, Y) где:
            X - массив с векторными представлениями изображений формы (n_samples, 784)
            Y - массив с метками (цифрами от 0 до 9) формы (n_samples,)
    """
    xs, ys = [], []  # Создаем пустые списки для изображений и меток

    # Итерируемся по всем элементам датасета
    for img, y in ds:
        # img - тензор PyTorch формы (1, 28, 28)
        # squeeze(0) удаляет первую размерность (1, 28, 28) -> (28, 28)
        # numpy() преобразует тензор в массив numpy
        arr = img.squeeze(0).numpy()  # (28,28) в [0..1]

        # reshape(-1) преобразует 2D массив 28x28 в 1D массив из 784 элементов
        # -1 означает "автоматически определить размерность"
        xs.append(arr.reshape(-1))  # (784,)

        # Преобразуем метку в целое число и добавляем в список
        ys.append(int(y))

    # stack объединяет все массивы в один большой массив
    # np.array создает массив из списка меток
    return np.stack(xs), np.array(ys)


# Проверяем, запущен ли скрипт напрямую (а не импортирован как модуль)
if __name__ == "__main__":

    # Создаем преобразование: преобразует изображение в тензор PyTorch
    # и нормализует значения пикселей в диапазон [0, 1]
    to_tensor = transforms.ToTensor()

    # Загружаем тренировочный датасет MNIST:
    # "data" - папка для сохранения данных
    # train=True - загружаем тренировочную часть
    # download=True - скачиваем если нет локальной копии
    # transform=to_tensor - применяем преобразование в тензор
    train = datasets.MNIST("data", train=True, download=True, transform=to_tensor)

    # Загружаем тестовый датасет MNIST (train=False)
    test = datasets.MNIST("data", train=False, download=True, transform=to_tensor)

    # Преобразуем датасеты в массивы numpy
    # Xtr - тренировочные изображения (60000, 784), Ytr - тренировочные метки (60000,)
    # Xte - тестовые изображения (10000, 784), Yte - тестовые метки (10000,)
    Xtr, Ytr = ds_to_arrays(train)
    Xte, Yte = ds_to_arrays(test)

    # Получаем соединение с базой данных из пула
    conn = get_conn()
    try:

        # Создаем курсор для выполнения SQL-запросов
        with conn.cursor() as cur:

            # Проверяем, есть ли уже данные в таблице, чтобы избежать дублирования
            cur.execute("SELECT COUNT(*) FROM demo.mnist_samples")

            # fetchone() возвращает одну строку результата, [0] - первый столбец
            # Если запрос не вернул строк (rowcount == -1), устанавливаем cnt = 0
            cnt = cur.fetchone()[0] if cur.rowcount != -1 else 0

            # Если таблица пустая (cnt == 0), загружаем данные
            if cnt == 0:

                # Вложенная функция для вставки данных определенного раздела (train/test)
                def insert(split, X, Y):
                    """
                    Вставляет данные в таблицу mnist_samples.

                    Args:
                        split: строка 'train' или 'test'
                        X: массив изображений формы (n_samples, 784)
                        Y: массив меток формы (n_samples,)
                    """
                    rows = []  # Список для хранения кортежей с данными для вставки

                    # Итерируемся по всем изображениям и меткам
                    for x, y in zip(X, Y):
                        # Создаем кортеж с данными для одной строки:
                        rows.append((
                            split,  # раздел: 'train' или 'test'
                            int(y),  # метка: цифра от 0 до 9

                            # Преобразуем массив в бинарный формат:
                            # 1. astype(np.float32) - преобразуем в float32
                            # 2. tobytes() - преобразуем в байты
                            # 3. memoryview() - создаем представление памяти для эффективной передачи
                            memoryview(x.astype(np.float32).tobytes()),
                            28,  # количество строк в изображении
                            28  # количество столбцов в изображении
                        ))

                    # executemany выполняет один SQL запрос для всех строк
                    # Это эффективнее, чем выполнять отдельный INSERT для каждой строки
                    cur.executemany(
                        "INSERT INTO demo.mnist_samples (split,label,vec,rows,cols) VALUES (%s,%s,%s,%s,%s)",
                        rows  # список кортежей с данными
                    )


                # Вставляем тренировочные данные
                insert("train", Xtr, Ytr)

                # Вставляем тестовые данные
                insert("test", Xte, Yte)

                # Фиксируем изменения в базе данных
                conn.commit()
                print("✅ Данные MNIST загружены в PostgreSQL")
            else:
                # Если данные уже есть, выводим информационное сообщение
                print(f"ℹ️ Уже есть {cnt} строк — пропускаем загрузку")

    finally:
        # Всегда возвращаем соединение в пул, даже если произошла ошибка
        put_conn(conn)
