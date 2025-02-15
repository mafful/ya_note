# Generated by Django 3.2.15 on 2023-12-15 17:55

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='note',
            name='title',
            field=models.CharField(default='Название заметки', help_text='Дайте короткое название заметке', max_length=100, verbose_name='Заголовок'),
        ),
    ]
