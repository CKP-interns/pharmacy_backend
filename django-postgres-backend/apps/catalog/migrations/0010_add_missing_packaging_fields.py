from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0009_product_packaging_fields"),
    ]

    operations = [
        # Also add the fields to the model state for Django's ORM
        migrations.AddField(
            model_name="product",
            name="capsules_per_strip",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="doses_per_inhaler",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="grams_per_bar",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="grams_per_pack",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="grams_per_sachet",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="inhalers_per_box",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="bars_per_box",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="pieces_per_pack",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="packs_per_box",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="pairs_per_pack",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="sachets_per_box",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]

