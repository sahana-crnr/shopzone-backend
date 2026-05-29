# Generated migration for adding images field to Product

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_producttag_product_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="images",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
