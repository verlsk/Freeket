# Generated by Django 3.0.4 on 2020-04-11 16:14

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0012_delete_usuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='entrada',
            name='date_adquisicion',
            field=models.DateField(default=datetime.date(2020, 4, 11)),
        ),
    ]
