# Generated by Django 4.2.7 on 2023-11-20 05:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_todoitem_cleaned_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='todoitem',
            name='linum',
        ),
        migrations.AddField(
            model_name='todoitem',
            name='node_idx',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
