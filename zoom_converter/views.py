from itertools import chain
import csv, io

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from tabroom_zoom.settings import EMAIL_HOST_USER
from .models import *
from .decorators import activation_required
from .forms import TournamentAccessForm, SchoolContactEmailForm
from .helpers import parse_pairings, generate_pairing_files, validate_csv, configure_tournament
from .helpers import import_events, import_schools, import_judges, import_entries, import_emails
from .profile_views import *

def user_allowed_tournament(tournament, user, error=True):
    if user.is_superuser or tournament.authorized_users.filter(pk=user.pk).exists():
        return True
    if error:
        raise PermissionDenied
    return False


class ActivationRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_authenticated and not self.request.user.verified():
            return False
        return True
    def handle_no_permission(self):
        return redirect('zoom_converter:profile')

class UserAllowedTournament(ActivationRequiredMixin):
    def test_func(self):
        tournament = get_object_or_404(Tournament, pk=self.kwargs.get('tournament', self.kwargs.get('pk')))
        return user_allowed_tournament(tournament, self.request.user)

class TournamentList(ActivationRequiredMixin, ListView):
    model = Tournament

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament_list'] = self.request.user.tournaments_authorized.all()
        return context

class TournamentCreate(ActivationRequiredMixin, CreateView):
    model = Tournament
    fields = ["name"]
    template_name_suffix = "_create"

    def form_valid(self, form):
        obj = form.instance
        obj.director=self.request.user
        obj.save()
        obj.authorized_users.add(self.request.user)
        return super().form_valid(form)


@activation_required
def school_list(request):
    context = {}
    context['schools'] = request.user.schools_authorized.all()
    return render(request, "zoom_converter/school_list.html", context=context)

@activation_required
def tournament_configure(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_allowed_tournament(tournament, request.user)
    context = {'tournament': tournament, 'errors': []}
    if request.method != "POST":
        return render(request, "zoom_converter/tournament_configure.html", context=context)
    if not (events:=request.FILES.get('events')):
        context['errors'].append('events')
    if not (schools:=request.FILES.get('schools')):
        context['errors'].append('schools')
    if not (judges:=request.FILES.get('judges')):
        context['errors'].append('judges')
    if not (entries:=request.FILES.get('entries')):
        context['errors'].append('entries')
    if not (emails:=request.FILES.get('emails')):
        context['errors'].append('emails')
    if not context['errors']:
        files = (events, schools, judges, entries, emails)
        try:
            for file in files:
                if not validate_csv(file):
                    raise Exception("File was of invalid type - OAJ")
            configure_tournament(tournament, files)
            return redirect(tournament)
        except Exception as e:
            raise e
    tournament.configured = True
    tournament.save()
    return render(request, "zoom_converter/tournament_configure.html", context=context)

@activation_required
def pairing_create(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_allowed_tournament(tournament, request.user)



@activation_required
def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_allowed_tournament(tournament, request.user)
    t_events = [e.name for e in tournament.events.all()]
    bad_coaches = tournament.schools.filter(contact_email=None)
    _bad_coaches = [SchoolContactEmailForm(request.POST, instance=b) for b in bad_coaches]
    context = {'tournament': tournament, 'bad_coaches': bad_coaches}
    if request.method != "POST":
        return render(request, "zoom_converter/tournament_detail.html", context=context)
    file = request.FILES.get('file')
    if not file or not file.name.endswith('.csv'):
        # deal with the forms
        context['error'] = 'Please upload a file in the correct CSV file as per the instructions'
        return render(request, "zoom_converter/tournament_detail.html", context=context)
    data_set = file.read().decode('UTF-8')
    io_string = io.StringIO(data_set)
    reader = csv.reader(io_string, delimiter=',', quotechar='"')
    headers = next(reader)
    if headers[0] in t_events:
        event = tournament.events.get(name=headers[0])
        round, created = event.rounds.get_or_create(number=headers[1])
        if not created:
            round.breakout_rooms.all().delete()
            round.delete()
            round = event.rounds.create(number=headers[1])
        parse_pairings(reader, round)
        generate_pairing_files(round)
    context['bad_judges'] = tournament.judges.filter(tabroom_email=None)
    context['bad_coaches'] = tournament.judges.filter(tabroom_email=None)
    context['bad_competitors'] = tournament.judges.filter(tabroom_email=None)
    return render(request, "zoom_converter/tournament_detail.html", context=context)


class TournamentUpdate(UserAllowedTournament, UpdateView):
    model = Tournament
    fields = ['name']


@activation_required
def tournament_access(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_allowed_tournament(tournament, request.user)
    if request.method == "POST":
        form = TournamentAccessForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                p = User.objects.get(email=email)
                tournament.authorized_users.add(p)
                form = TournamentAccessForm()
            except:
                form.add_error('email', "No user was found with this email")
    else:
        form = TournamentAccessForm()
    users = tournament.authorized_users.all()
    return render(request, "zoom_converter/tournament_access.html", context={'tournament': tournament, 'form': form, 'users': users})

@activation_required
def tournament_access_revoke(request, pk, revoke_user):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_allowed_tournament(tournament, request.user)
    u = User.objects.get(pk=revoke_user)
    if u != tournament.director and u != request.user:
        tournament.authorized_users.remove(u)
    return redirect('zoom_converter:tournament_access', pk=pk)

@activation_required
def tournament_access_director(request, pk, director_user):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_allowed_tournament(tournament, request.user)
    u = User.objects.get(pk=director_user)
    if request.user == tournament.director:
        tournament.director = u
        tournament.save()
    return redirect('zoom_converter:tournament_access', pk=pk)

class EventDetail(UserAllowedTournament, DetailView):
    model = Event

class RoundDetail(UserAllowedTournament, DetailView):
    model = Round


@activation_required
def breakout_room_detail(request, tournament, event, round, pk):
    breakout_room = get_object_or_404(BreakoutRoom, pk=pk)
    if request.method == "POST":
        tournament = get_object_or_404(Tournament, pk=tournament)
        user_allowed_tournament(tournament, request.user)
        subject = f"Zoom Link for {breakout_room.round}"
        try:
            link = request.POST.get('zoom_link')
            accept = request.POST.get('accept', '')
        except:
            return redirect(breakout_room.round)
        extra_info = request.POST.get('extra_info', 'None')
        if accept != "on" or link is None:
            return redirect(breakout_room.round)
        for person in breakout_room.persons.all():
            message = render_to_string('zoom_converter/zoom_link.html', {'link': link, 'person': person, 'extra_info': extra_info})
            send_mail(subject, message, EMAIL_HOST_USER, ["omajoshi9@gmail.com"], html_message=message)
            ####send_mail(subject, message, EMAIL_HOST_USER, [person.get_zoom_email()], html_message=message)
    return redirect(breakout_room.round)

# Create your views here.


