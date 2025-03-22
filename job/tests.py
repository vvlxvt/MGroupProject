from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User
import random

# Словарь для временного хранения кодов подтверждения
verification_codes = {}

def verify_user(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        tg_username = request.POST.get('tg_username')

        # Проверяем наличие пользователя в БД
        user = User.objects.filter(tg_username=tg_username).first()

        if user:
            # Если пользователь найден и верифицирован, возвращаем успешный ответ
            if user.verified:
                return JsonResponse({'status': 'verified'})
            else:
                return JsonResponse({'status': 'pending_verification'})
        else:
            # Если пользователь не найден, перенаправляем к телеграм-боту
            bot_url = f"https://t.me/mgrup24_bot?start=user={tg_username}"
            return JsonResponse({'status': 'redirect', 'url': bot_url})

    return render(request, 'verify_user.html')

@csrf_exempt
def verify_code(request):
    if request.method == 'POST':
        tg_username = request.POST.get('tg_username')
        code = request.POST.get('code')

        # Проверяем код из временного хранилища
        if tg_username in verification_codes and verification_codes[tg_username] == code:
            user, created = User.objects.get_or_create(tg_username=tg_username)
            user.verified = True
            user.save()

            # Удаляем код после успешной верификации
            del verification_codes[tg_username]

            return JsonResponse({'status': 'verified'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid code'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# В телеграм-боте нужно будет реализовать генерацию кода:
# 1. Получаем tg_username и telegram_id
# 2. Генерируем код
# 3. Сохраняем его во временное хранилище (verification_codes)
# Пример:
# def handle_start_command(tg_username):
#     code = str(random.randint(1000, 9999))
#     verification_codes[tg_username] = code
#     send_message_to_user(tg_username, f"Your verification code: {code}")
