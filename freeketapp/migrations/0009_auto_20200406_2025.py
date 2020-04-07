# Generated by Django 3.0.4 on 2020-04-06 20:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('freeketapp', '0008_remove_evento_organizador'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='evento',
            name='asistentes',
        ),
        migrations.AddField(
            model_name='evento',
            name='organizador',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='freeketapp.Organizador'),
        ),
    ]
