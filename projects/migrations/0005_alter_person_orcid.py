# Generated by Django 3.2 on 2021-05-03 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_rename_project_id_researchfolder_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='orcid',
            field=models.CharField(blank=True, max_length=19, null=True),
        ),
    ]
