from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    objects = CustomUserManager()
    email = models.EmailField(_('email address'), unique=True)
    email_confirmed = models.BooleanField(default=False)
    tabroom_email = models.EmailField()
    tabroom_confirmed = models.BooleanField(default=False)
    zoom_email = models.EmailField()
    zoom_confirmed = models.BooleanField(default=False)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['tabroom_email', 'zoom_email']
    def __str__(self):
        return self.email

    def verified(self):
        return self.email_confirmed and self.zoom_confirmed and self.tabroom_confirmed

class School(models.Model):
    contact_email = models.EmailField(null=True, blank=True)
    coach = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='schools_coach')
    authorized_users = models.ManyToManyField(User, blank=True, related_name='schools_authorized')
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.name}"

class Person(models.Model):
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    tabroom_email = models.EmailField(null=True, blank=True)
    claimed = models.BooleanField(default=False)
    def __str__(self):
        return f'{self.name} {self.tabroom_email}'
    def get_zoom_email(self):
        try:
            user = User.objects.get(tabroom_confirmed=True, tabroom_email=self.tabroom_email)
            return user.zoom_email
        except:
            pass
        if self.tabroom_email:
            return self.tabroom_email
        if self.school and self.school.contact_email:
            return self.school.contact_email
        return 'test@localhost.local'

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    director = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tournaments_director')
    authorized_users = models.ManyToManyField(User, blank=True, related_name='tournaments_authorized')
    schools = models.ManyToManyField(School, blank=True, related_name='tournaments')
    judges = models.ManyToManyField(Person, blank=True, related_name='tournaments')
    real_tournament = models.BooleanField(default=False)
    configured = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.name}"
    def get_absolute_url(self):
        return reverse('zoom_converter:tournament_detail', kwargs={'pk': self.pk})

class Event(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    def __str__(self):
        return f"{self.tournament} {self.code} {self.name}"
    def get_absolute_url(self):
        return reverse('zoom_converter:event', kwargs={'tournament': self.tournament.pk, 'pk': self.pk})

class Team(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teams')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='teams')
    members = models.ManyToManyField(Person, related_name='teams')
    code = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.event.code}-{self.code}"

class Round(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rounds')
    number = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.event.code}-{self.number}"
    def get_absolute_url(self):
        return reverse('zoom_converter:round', kwargs={'tournament': self.event.tournament.pk, 'event': self.event.pk, 'pk': self.pk})

class BreakoutRoom(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='breakout_rooms')
    file = models.FileField()
    number = models.PositiveSmallIntegerField()
    persons = models.ManyToManyField(Person)
    def __str__(self):
        return self.file.name
    def get_absolute_url(self):
        return reverse('zoom_converter:breakout_room', kwargs={'tournament': self.round.event.tournament.pk, 'event': self.round.event.pk, 'round': self.round.pk, 'pk': self.pk})

class Room(models.Model):
    number = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.number}"

class Pairing(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="pairings")
    teams = models.ManyToManyField(Team, related_name="pairings")
    judges = models.ManyToManyField(Person)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, related_name="pairings", null=True, blank=True)
    def __str__(self):
        return f"{self.room} --- {self.round.number} {' vs. '.join([team.code for team in self.teams.all()])} {', '.join([judge.name for judge in self.judges.all()])}"
