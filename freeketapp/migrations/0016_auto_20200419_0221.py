# Generated by Django 3.0.4 on 2020-04-19 02:21

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0015_auto_20200418_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entrada',
            name='fecha_adquisicion',
            field=models.DateField(default=datetime.date(2020, 4, 19)),
        ),
    ]