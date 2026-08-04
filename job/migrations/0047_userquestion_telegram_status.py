from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("job", "0046_make_content_slugs_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="userquestion",
            name="telegram_status",
            field=models.CharField(
                choices=[
                    ("pending", "Ожидает отправки"),
                    ("sent", "Отправлено"),
                    ("failed", "Ошибка отправки"),
                ],
                db_index=True,
                default="pending",
                max_length=10,
            ),
        ),
    ]
