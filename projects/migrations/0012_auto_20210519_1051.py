# Generated by Django 3.2 on 2021-05-19 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_auto_20210518_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='researchstats',
            name='collected',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vaultstats',
            name='collected',
            field=models.DateField(blank=True, null=True),
        ),
    ]