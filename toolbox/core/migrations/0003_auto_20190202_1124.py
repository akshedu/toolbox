# Generated by Django 2.0.10 on 2019-02-02 11:24

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_topchannels_topvideos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topchannels',
            name='date',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='topvideos',
            name='date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
