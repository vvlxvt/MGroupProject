import os
from PIL import Image

# Папка, где находятся изображения
folder_path = "C:/Users/vital/PycharmProjects/MGroupProject/mgrupsite/job/static/job/images/partners/transparent"  #
# Укажите путь к папке с фото

# Поддерживаемые расширения
extensions = (".png", ".jpg", ".jpeg", "JPG")

# Лимит размера файла в байтах (1MB = 1 * 1024 * 1024)
size_limit = 1 * 1024 * 1024


def convert_and_compress(image_path):
    try:
        # Открываем изображение
        with Image.open(image_path) as img:
            # Проверяем размер файла
            file_size = os.path.getsize(image_path)
            if file_size > size_limit:
                # Уменьшаем размер на 50%
                width, height = img.size
                img = img.resize((width // 2, height // 2))

            # Создаём новый путь с расширением .webp
            new_path = os.path.splitext(image_path)[0] + ".webp"
            img.save(new_path, "WEBP", quality=80)  # Сохраняем в WebP с качеством 80%

            print(f"✅ {image_path} → {new_path}")

            # Удаляем оригинальный файл
            os.remove(image_path)
            print(f"🗑️ Удален {image_path}")

    except Exception as e:
        print(f"❌ Ошибка с {image_path}: {e}")


# Рекурсивный обход папок
# for root, _, files in os.walk(folder_path):
#     for file in files:
#         if file.lower().endswith(extensions):
#             file_path = os.path.join(root, file)
#             convert_and_compress(file_path)

image = Image.open('C:/Users/vital/PycharmProjects/MGroupProject/mgrupsite/job/static/job/images/IMG_9436.JPG')
# Конвертируем в чёрно-белое
bw_image = image.convert('L')
# Сохраняем результат
bw_image.save('plug_image_bw.jpg')