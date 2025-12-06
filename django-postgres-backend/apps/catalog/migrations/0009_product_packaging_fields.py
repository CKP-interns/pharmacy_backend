from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0008_batchlot_initial_quantity_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="bottles_per_box",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="grams_per_tube",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="ml_per_bottle",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="ml_per_vial",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="tubes_per_box",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="vials_per_box",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
