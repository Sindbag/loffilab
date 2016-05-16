# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-05 18:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import loffi.models


class Migration(migrations.Migration):

    dependencies = [
        ('loffi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.ForeignKey(default=(loffi.models.Status(4, 'Не обработан', 'Заказ поступил в базу,но не был обработан администратором'), False), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='loffi.Status', verbose_name='Статус заказа'),
        ),
    ]
