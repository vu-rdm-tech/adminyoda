# Generated by Django 3.2.4 on 2021-06-16 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0021_auto_20210616_0938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='miscstats',
            name='size_research',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='miscstats',
            name='size_vault',
            field=models.BigIntegerField(default=0),
        ),
    ]