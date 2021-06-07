# Generated by Django 3.2 on 2021-05-31 11:25

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0013_auto_20210526_1722'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datamanager',
            name='vunetid',
        ),
        migrations.AddField(
            model_name='datamanager',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='datamanager',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='datamanager',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='projects.person'),
        ),
        migrations.AddField(
            model_name='datamanager',
            name='yoda_name',
            field=models.CharField(default='-', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='person',
            name='firstname',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='person',
            name='lastname',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
