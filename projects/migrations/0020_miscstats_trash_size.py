# Generated by Django 3.2.4 on 2021-06-15 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0019_auto_20210614_1733'),
    ]

    operations = [
        migrations.AddField(
            model_name='miscstats',
            name='trash_size',
            field=models.BigIntegerField(default=0),
        ),
    ]
