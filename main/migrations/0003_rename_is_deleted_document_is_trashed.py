# Generated by Django 4.2.7 on 2023-11-08 11:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_document_is_deleted'),
    ]

    operations = [
        migrations.RenameField(
            model_name='document',
            old_name='is_deleted',
            new_name='is_trashed',
        ),
    ]