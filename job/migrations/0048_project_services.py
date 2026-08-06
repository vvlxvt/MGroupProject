from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("job", "0047_userquestion_telegram_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="services",
            field=models.ManyToManyField(
                blank=True,
                related_name="projects",
                to="job.post",
                verbose_name="Связанные услуги",
            ),
        ),
    ]
