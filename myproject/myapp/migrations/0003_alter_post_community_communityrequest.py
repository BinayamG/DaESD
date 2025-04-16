# Generated by Django 5.1.6 on 2025-04-16 20:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_community_event_notification_post'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='community',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='myapp.community'),
        ),
        migrations.CreateModel(
            name='CommunityRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('tags', models.CharField(blank=True, max_length=255)),
                ('is_approved', models.BooleanField(default=False)),
                ('is_rejected', models.BooleanField(default=False)),
                ('rejection_reason', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_requests', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
