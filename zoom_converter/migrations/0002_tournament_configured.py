# Generated by Django 3.1 on 2020-08-16 06:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoom_converter', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='configured',
            field=models.BooleanField(default=False),
        ),
    ]