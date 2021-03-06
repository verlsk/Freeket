# Generated by Django 3.0.4 on 2020-06-13 18:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0025_auto_20200609_0130'),
    ]

    operations = [
        migrations.AddField(
            model_name='entrada',
            name='validada',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='entrada',
            name='fecha_adquisicion',
            field=models.DateField(default=datetime.date(2020, 6, 13)),
        ),
        migrations.AlterField(
            model_name='evento',
            name='fecha_creacion',
            field=models.DateField(default=datetime.date(2020, 6, 13)),
        ),
    ]
