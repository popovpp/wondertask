# Generated by Django 3.2.2 on 2021-08-30 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_task_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='priority',
            field=models.PositiveIntegerField(default=4),
        ),
    ]
