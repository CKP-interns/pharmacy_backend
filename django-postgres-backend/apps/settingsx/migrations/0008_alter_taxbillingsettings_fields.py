from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settingsx", "0007_alertthresholds"),
    ]

    operations = [
        migrations.AlterField(
            model_name="taxbillingsettings",
            name="gst_rate",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name="taxbillingsettings",
            name="cgst_rate",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name="taxbillingsettings",
            name="sgst_rate",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name="taxbillingsettings",
            name="calc_method",
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AlterField(
            model_name="taxbillingsettings",
            name="invoice_prefix",
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AlterField(
            model_name="taxbillingsettings",
            name="invoice_start",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="taxbillingsettings",
            name="invoice_template",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name="taxbillingsettings",
            name="invoice_footer",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
