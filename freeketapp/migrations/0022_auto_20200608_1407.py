# Generated by Django 3.0.4 on 2020-06-08 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0021_auto_20200608_1406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evento',
            name='img',
            field=models.ImageField(upload_to='m'),
        ),
    ]