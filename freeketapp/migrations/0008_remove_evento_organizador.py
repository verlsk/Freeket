# Generated by Django 3.0.4 on 2020-04-06 20:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0007_auto_20200406_1848'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='evento',
            name='organizador',
        ),
    ]