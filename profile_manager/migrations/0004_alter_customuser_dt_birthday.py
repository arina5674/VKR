# Generated by Django 5.1.4 on 2025-02-13 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profile_manager', '0003_alter_customuser_town'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='dt_birthday',
            field=models.DateField(null=True, verbose_name='Дата рождения'),
        ),
    ]
