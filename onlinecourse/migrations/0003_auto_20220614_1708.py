# Generated by Django 3.1.3 on 2022-06-14 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinecourse', '0002_auto_20220614_1640'),
    ]

    operations = [
        migrations.RenameField(
            model_name='choice',
            old_name='content',
            new_name='choice_text',
        ),
        migrations.RenameField(
            model_name='choice',
            old_name='correct',
            new_name='is_correct',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='text',
            new_name='question_text',
        ),
        migrations.AlterField(
            model_name='question',
            name='grade',
            field=models.IntegerField(default=10),
        ),
    ]