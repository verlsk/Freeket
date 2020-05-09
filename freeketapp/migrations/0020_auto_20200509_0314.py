# Generated by Django 3.0.4 on 2020-05-09 03:14

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0019_auto_20200508_0217'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizador',
            name='direccion',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='entrada',
            name='fecha_adquisicion',
            field=models.DateField(default=datetime.date(2020, 5, 9)),
        ),
        migrations.AlterField(
            model_name='evento',
            name='fecha_creacion',
            field=models.DateField(default=datetime.date(2020, 5, 9)),
        ),
    ]