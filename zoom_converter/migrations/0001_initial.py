# Generated by Django 3.0.5 on 2020-05-08 02:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import zoom_converter.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('email_confirmed', models.BooleanField(default=False)),
                ('tabroom_email', models.EmailField(max_length=254)),
                ('tabroom_confirmed', models.BooleanField(default=False)),
                ('zoom_email', models.EmailField(max_length=254)),
                ('zoom_confirmed', models.BooleanField(default=False)),
                ('first_name', models.CharField(max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(max_length=150, verbose_name='last name')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', zoom_converter.models.CustomUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('tabroom_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('claimed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('code', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('authorized_users', models.ManyToManyField(blank=True, related_name='schools_authorized', to=settings.AUTH_USER_MODEL)),
                ('coach', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='schools_coach', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('real_tournament', models.BooleanField(default=False)),
                ('authorized_users', models.ManyToManyField(blank=True, related_name='tournaments_authorized', to=settings.AUTH_USER_MODEL)),
                ('director', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tournaments_director', to=settings.AUTH_USER_MODEL)),
                ('judges', models.ManyToManyField(blank=True, related_name='tournaments', to='zoom_converter.Person')),
                ('schools', models.ManyToManyField(blank=True, related_name='tournaments', to='zoom_converter.School')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams', to='zoom_converter.Event')),
                ('members', models.ManyToManyField(related_name='teams', to='zoom_converter.Person')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams', to='zoom_converter.School')),
            ],
        ),
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=100)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rounds', to='zoom_converter.Event')),
            ],
        ),
        migrations.AddField(
            model_name='person',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='zoom_converter.School'),
        ),
        migrations.CreateModel(
            name='Pairing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('judges', models.ManyToManyField(to='zoom_converter.Person')),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pairings', to='zoom_converter.Room')),
                ('round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pairings', to='zoom_converter.Round')),
                ('teams', models.ManyToManyField(related_name='pairings', to='zoom_converter.Team')),
            ],
        ),
        migrations.AddField(
            model_name='event',
            name='tournament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='zoom_converter.Tournament'),
        ),
        migrations.CreateModel(
            name='BreakoutRoom',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('number', models.PositiveSmallIntegerField()),
                ('persons', models.ManyToManyField(to='zoom_converter.Person')),
                ('round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='breakout_rooms', to='zoom_converter.Round')),
            ],
        ),
    ]
