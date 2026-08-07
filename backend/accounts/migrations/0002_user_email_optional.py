from django.db import migrations, models


def blank_emails_to_null(
    apps,
    schema_editor,
):
    User = apps.get_model(
        "accounts",
        "User",
    )

    User.objects.filter(
        email="",
    ).update(
        email=None,
    )


class Migration(
    migrations.Migration,
):
    dependencies = [
        (
            "accounts",
            "0001_initial",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                blank=True,
                max_length=254,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(
            blank_emails_to_null,
            migrations.RunPython.noop,
        ),
    ]