from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("job", "0048_project_services"),
    ]

    operations = [
        migrations.AddField(
            model_name="userquestion",
            name="contact_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AlterField(
            model_name="userquestion",
            name="user",
            field=models.ForeignKey(
                blank=True,
                help_text="Устаревшая связь с Telegram-профилем",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="job.userprofile",
            ),
        ),
    ]
