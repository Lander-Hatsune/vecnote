# Generated by Django 4.2.7 on 2023-11-16 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_document_is_pinned_document_never_embed_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='never_embed',
        ),
        migrations.AddField(
            model_name='document',
            name='do_embed',
            field=models.BooleanField(default=True),
        ),
    ]