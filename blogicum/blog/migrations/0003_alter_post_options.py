# Generated by Django 3.2.16 on 2025-01-07 22:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_auto_20250107_2317'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('pub_date', 'title'), 'verbose_name': 'публикация', 'verbose_name_plural': 'Публикации'},
        ),
    ]
