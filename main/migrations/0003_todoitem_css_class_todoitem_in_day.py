# Generated by Django 4.2.7 on 2023-11-18 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_remove_todoitem_css_class_remove_todoitem_in_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='todoitem',
            name='css_class',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='todoitem',
            name='in_day',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
