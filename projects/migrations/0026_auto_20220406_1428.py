# Generated by Django 3.2.12 on 2022-04-06 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0025_auto_20220404_1312'),
    ]

    operations = [
        migrations.AddField(
            model_name='researchstats',
            name='revision_size',
            field=models.BigIntegerField(default=0),
        )
    ]
