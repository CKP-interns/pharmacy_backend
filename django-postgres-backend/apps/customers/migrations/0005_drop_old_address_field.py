from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0004_merge_20251107_1241'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE customers_customer DROP COLUMN IF EXISTS address;",
            reverse_sql="ALTER TABLE customers_customer ADD COLUMN address TEXT;"
        ),
    ]
