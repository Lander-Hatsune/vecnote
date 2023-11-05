# Generated by Django 4.2.7 on 2023-11-05 06:49

from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('content', models.TextField()),
                ('html_content', models.TextField()),
                ('embedding', pgvector.django.VectorField(dimensions=1024)),
                ('created_at', models.DateField()),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        pgvector.django.VectorExtension(),
    ]
