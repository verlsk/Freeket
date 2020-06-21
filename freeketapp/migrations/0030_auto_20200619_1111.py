# Generated by Django 3.0.4 on 2020-06-19 11:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0029_auto_20200615_2257'),
    ]

    operations = [
        migrations.AddField(
            model_name='entrada',
            name='aux_email',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='entrada',
            name='fecha_adquisicion',
            field=models.DateField(default=datetime.date(2020, 6, 19)),
        ),
        migrations.AlterField(
            model_name='evento',
            name='fecha_creacion',
            field=models.DateField(default=datetime.date(2020, 6, 19)),
        ),
    ]
