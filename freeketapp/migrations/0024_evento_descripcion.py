# Generated by Django 3.0.4 on 2020-06-08 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0023_auto_20200608_1414'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='descripcion',
            field=models.CharField(default='', max_length=2000),
        ),
    ]
