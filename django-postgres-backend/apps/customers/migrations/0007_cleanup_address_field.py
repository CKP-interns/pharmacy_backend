from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('customers', '0006_alter_customer_phone'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE customers_customer
                DROP COLUMN IF EXISTS address;
            """,
            reverse_sql="",
        ),
    ]
