from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="NoteLengthRule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("min_chars", models.PositiveIntegerField(default=1)),
                ("max_chars", models.PositiveIntegerField(default=200)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "备注字数规则",
                "verbose_name_plural": "备注字数规则",
            },
        ),
    ]
