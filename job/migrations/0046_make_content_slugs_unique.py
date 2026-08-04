from django.db import migrations, models
from django.db.models import Count


CONTENT_MODELS = ("Post", "Article", "Project")


def ensure_slugs_are_unique(apps, schema_editor):
    duplicate_messages = []

    for model_name in CONTENT_MODELS:
        model = apps.get_model("job", model_name)
        duplicate_slugs = list(
            model.objects.values("slug")
            .annotate(row_count=Count("pk"))
            .filter(row_count__gt=1)
            .order_by("slug")
        )
        if duplicate_slugs:
            formatted_slugs = ", ".join(
                f"{item['slug']} ({item['row_count']})"
                for item in duplicate_slugs
            )
            duplicate_messages.append(f"{model_name}: {formatted_slugs}")

    if duplicate_messages:
        details = "; ".join(duplicate_messages)
        raise RuntimeError(
            "Cannot make content slugs globally unique. "
            f"Resolve duplicate slugs first: {details}"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("job", "0045_applicantprofile_position"),
    ]

    operations = [
        migrations.RunPython(
            ensure_slugs_are_unique,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="post",
            name="slug",
            field=models.SlugField(max_length=250, unique=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="slug",
            field=models.SlugField(max_length=250, unique=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="slug",
            field=models.SlugField(max_length=250, unique=True),
        ),
    ]
