# Generated by Django 3.2.4 on 2021-06-14 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0016_miscstats_revision_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='miscstats',
            name='external_users_total',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='miscstats',
            name='internal_users_total',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='miscstats',
            name='revision_size',
            field=models.BigIntegerField(),
        ),
    ]