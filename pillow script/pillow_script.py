import os
from PIL import Image

# Папка, где находятся изображения
folder_path = "C:/Users/vital/Downloads/mgrup24/job/1536x1024/webp"  #"C:\Users\vital\PycharmProjects\Frontend_for_MGroup\photo\Ilford 2018_01.jpg"
# Укажите путь к папке с фото

# Поддерживаемые расширения
extensions = (".png", ".jpg", ".jpeg", "JPG")

# Лимит размера файла в байтах (1MB = 1 * 1024 * 1024)
size_limit = 1 * 1024 * 1024


def convert_and_compress(image_path):
    try:
        # Открываем изображение
        with Image.open(image_path) as img:
            # file_size = os.path.getsize(image_path)
            # if file_size > size_limit:
                # Уменьшаем размер на 50%
            # width, height = img.size
            # img = img.resize((width // 10, height // 10))
            #
            #
            # new_width = 1600
            # width_percent = new_width / float(img.size[0])
            # new_height = int((float(img.size[1]) * float(width_percent)))
            # img = img.resize((new_width, 1061), Image.LANCZOS)
            # img=img.transpose(Image.ROTATE_270)


            # Создаём новый путь с расширением .webp
            new_path = os.path.splitext(image_path)[0] + ".webp"
            img.save(new_path, "WEBP", quality=100)  # Сохраняем в WebP с качеством 80%

            print(f"✅ {image_path} → {new_path}")

            # Удаляем оригинальный файл
            os.remove(image_path)
            print(f"🗑️ Удален {image_path}")

    except Exception as e:
        print(f"❌ Ошибка с {image_path}: {e}")


for root, _, files in os.walk(folder_path):
    for file in files:
        if file.lower().endswith(extensions):
            file_path = os.path.join(root, file)
            convert_and_compress(file_path)

# image = Image.open(
#     "C:/Users/vital/Downloads/mgrup24/1/caution-barricade_tape.jpg"
# )
# # Конвертируем в чёрно-белое
# bw_image = image.convert("L")
# # Сохраняем результат
# bw_image.save("plug_image_bw.jpg")
