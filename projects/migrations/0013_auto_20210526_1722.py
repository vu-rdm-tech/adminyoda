# Generated by Django 3.2 on 2021-05-26 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0012_auto_20210519_1051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='abbreviation',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='department',
            name='faculty',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='department',
            name='institute',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='department',
            name='name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
