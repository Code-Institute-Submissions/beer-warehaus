# Generated by Django 3.1.2 on 2020-10-13 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_auto_20201013_1710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slide',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='slides'),
        ),
    ]
