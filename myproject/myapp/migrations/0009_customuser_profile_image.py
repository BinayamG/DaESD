# Generated by Django 5.2 on 2025-05-06 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_friendship_customuser_friends_friendrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='profile_images/'),
        ),
    ]
