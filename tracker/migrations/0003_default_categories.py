from django.db import migrations

DEFAULT_CATEGORIES = [
    "Groceries",
    "Rent",
    "Transport",
    "Utilities",
    "Airtime & Data",
    "Entertainment",
    "Health",
    "Education",
    "Savings",
    "Salary",
    "Other",
]


def add_default_categories(apps, schema_editor):
    Category = apps.get_model("tracker", "Category")
    for name in DEFAULT_CATEGORIES:
        # get_or_create: safe to run on a database that already has some of these.
        Category.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0002_add_user_ownership"),
    ]

    operations = [
        # Reverse does nothing, so un-migrating never deletes categories people are using.
        migrations.RunPython(add_default_categories, migrations.RunPython.noop),
    ]
