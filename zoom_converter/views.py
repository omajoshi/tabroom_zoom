from datetime import datetime
from itertools import chain
import csv, io

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.mail import send_mail as _send_mail
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from tabroom_zoom.settings import EMAIL_HOST_USER
from .models import *
from .tokens import email_token_generator, tabroom_token_generator, zoom_token_generator
from .decorators import activation_required
from .forms import TournamentAccessForm, CustomUserCreationForm, SchoolContactEmailForm
from .forms import EmailActivationForm, TabroomActivationForm, ZoomActivationForm


def send_mail(*args, **kwargs):
    print(args)
    print(kwargs)
    return _send_mail(*args, **kwargs)


def user_allowed_tournament(tournament, user, error=True):
    if user.is_superuser or tournament.authorized_users.filter(pk=user.pk).exists():
        return True
    if error:
        raise PermissionDenied
    return False



class UserAllowedTournament(UserPassesTestMixin):
    def test_func(self):
        tournament = get_object_or_404(Tournament, pk=self.kwargs.get('tournament', self.kwargs.get('pk')))
        return user_allowed_tournament(tournament, self.request.user)


@activation_required
def index(request):
    return HttpResponse('index')


@login_required
@activation_required
def tournament_list(request):
    if request.method == "POST":
        tournament = Tournament.objects.create(name=request.POST['name'], director=request.user)
        tournament.authorized_users.add(request.user)
        return redirect(tournament)
    context = {'tournaments': request.user.tournaments_authorized.all()}
    return render(request, "zoom_converter/tournament_list.html", context=context)


@login_required
@activation_required
def school_list(request):
    context = {}
    context['schools'] = request.user.schools_authorized.all()
    return render(request, "zoom_converter/school_list.html", context=context)


@login_required
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
    if headers[0] == 'Event' and headers[1] == 'Abbr': # import all events
        tournament.events.all().delete()
        for row in reader:
            if row[0] == "Total":
                break
            tournament.events.create(name=row[0], code=row[1])




    elif headers[0] == 'Name' and headers[1] == 'Shortened': # import all schools and head coaches
        tournament.schools.clear()
        good_coaches, new_coaches = [], []
        for row in reader:
            email = row[10] if row[10] and '@' in row[10] else None
            school, school_created = School.objects.get_or_create(name=row[0], contact_email=email)
            tournament.schools.add(school)
            if not email:
                continue
            candidates = User.objects.filter(email=email)
            if candidates.exists():
                school.coach = candidates.get()
                school.save()
                school.authorized_users.add(school.coach)
                # send email to coach saying registration complete
            else:
                pass # send email to new coach saying join the website
            [new_coaches, good_coaches][bool(candidates.exists())].append(email) # filter based on existing account
        message = "A team you coach has been added to the tournament.  Please activate your account now to gain full access"
        # mass email all of the new coaches

        message = "Your team has been entered ... please check email addresses"
        # mass email all of the good coaches
        return render(request, "zoom_converter/tournament_detail.html", context=context)

    # up to here is bug free
    elif headers[0] == 'Group' and headers[1] == 'Code': # import all judge entries
        new_judges, good_judges, bad_judges = [], [], []
        for row in reader:
            email = row[10] if row[10] else None
            name = f'{row[5]} {row[6]}'
            judge, created = tournament.judges.get_or_create(name=name)
            if not created:
                old_email = judge.tabroom_email
                pass # throw some sort of error that does something with old_email

            judge.tabroom_email = email
            judge.save()
        # send mass mail to new_judges saying fix your account or create it
        # see if a user exists which is linked to this tabroom account
        # basically just check if the is_claimed flag is True
    elif headers[0] == 'Code' and headers[1] == 'Event': # import all teams
        for row in reader:
            event = get_object_or_404(Event, tournament=tournament, code=row[1])
            school = tournament.schools.get(name=row[4])
            team = event.teams.create(school=school, code=row[0])
            try:
                col = 13
                while True:
                    testing = row[col+2]
                    person, create = Person.objects.get_or_create(school=school, name=row[col])
                    team.members.add(person)
                    col += 3
            except:
                pass

    elif headers[0] == 'School' and headers[1] == 'SchoolCode': # try to match users with persons
        for row in reader:
            event = tournament.events.get(code=row[2])
            team = event.teams.get(code=row[3])
            try:
                col = 5
                while True:
                    if '@' in row[col+2] and '@' not in row[col+1]:
                        member = team.members.get(name=f'{row[col]} {row[col+1]}')
                        member.tabroom_email = row[col+2]
                        member.save()
                    col += 1
            except:
                pass

    elif headers[0] in t_events:
        event = tournament.events.get(name=headers[0])
        round, created = event.rounds.get_or_create(number=headers[1])
        if not created:
            round.breakout_rooms.all().delete()
            round.delete()
            round = event.rounds.create(number=headers[1])
        for row in reader:
            if not row:
                break
            if row[2]: # debate
                if row[1] == 'BYE':
                    continue
                room = Room.objects.create(number=row[1])
                team1 = event.teams.get(code=row[2])
                team2 = event.teams.get(code=row[5])
                pairing = round.pairings.create(room=room)
                pairing.teams.add(team1, team2)
                try:
                    col = 9
                    while True:
                        testing = row[col+2]
                        judge, e_j = tournament.judges.get_or_create(name=f"{row[col]} {row[col+1]}")
                        pairing.judges.add(judge)
                        col += 3
                except:
                    pass
            else: # speech
                pass
        number = 1
        count = 0
        channel_max_size = 90
        total_members = []
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['Pre-assign Room Name', 'Email Address'])
        for pairing in round.pairings.all():
            room = pairing.room
            pairing_members = [*[member for team in pairing.teams.all() for member in team.members.all()], *list(pairing.judges.all())]
            if count + len(pairing_members) > channel_max_size - 1:
                csv_file = ContentFile(buffer.getvalue())
                csv_file.name = f'{event.code}/breakout {round.number}_{number}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                b = round.breakout_rooms.create(file=csv_file, number=number)
                b.persons.add(*total_members)
                buffer.close()
                total_members = []
                buffer = io.StringIO()
                writer = csv.writer(buffer)
                number += 1
                count = 0
                writer.writerow(['Pre-assign Room Name', 'Email Address'])
            for member in pairing_members:
                writer.writerow([room, member.get_zoom_email()])
                total_members.append(member)
                count += 1
        csv_file = ContentFile(buffer.getvalue())
        csv_file.name = f'{event.code}/breakout {round.number}_{number}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        b = round.breakout_rooms.create(file=csv_file, number=number)
        b.persons.add(*total_members)
        buffer.close()

    context['bad_judges'] = tournament.judges.filter(tabroom_email=None)
    context['bad_coaches'] = tournament.judges.filter(tabroom_email=None)
    context['bad_competitors'] = tournament.judges.filter(tabroom_email=None)
    return render(request, "zoom_converter/tournament_detail.html", context=context)


class TournamentUpdate(LoginRequiredMixin, UserAllowedTournament, UpdateView):
    model = Tournament
    fields = ['name']


@login_required
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

@login_required
@activation_required
def tournament_access_revoke(request, pk, revoke_user):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_allowed_tournament(tournament, request.user)
    u = User.objects.get(pk=revoke_user)
    if u != tournament.director and u != request.user:
        tournament.authorized_users.remove(u)
    return redirect('zoom_converter:tournament_access', pk=pk)

@login_required
@activation_required
def tournament_access_director(request, pk, director_user):
    tournament = get_object_or_404(Tournament, pk=pk)
    user_allowed_tournament(tournament, request.user)
    u = User.objects.get(pk=director_user)
    if request.user == tournament.director:
        tournament.director = u
        tournament.save()
    return redirect('zoom_converter:tournament_access', pk=pk)

class EventDetail(LoginRequiredMixin, UserAllowedTournament, DetailView):
    model = Event

class RoundDetail(LoginRequiredMixin, UserAllowedTournament, DetailView):
    model = Round


@login_required
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
            ####send_mail(subject, message, EMAIL_HOST_USER, ["omajoshi9@gmail.com"], html_message=message)
            send_mail(subject, message, EMAIL_HOST_USER, [person.get_zoom_email()], html_message=message)
    return redirect(breakout_room.round)



def email_activation_helper(request): # not a view!!!
    user = request.user
    subject = "Tabroom/Zoom/Converter - Please verify your email"
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_token_generator.make_token(user)
    relative_link = reverse('zoom_converter:activate_email', kwargs={'uidb64': uidb64, 'token': token})
    link = request.build_absolute_uri(relative_link)
    message = render_to_string('registration/email_activation_email.html', {'link': link})
    send_mail(subject, message, EMAIL_HOST_USER, [user.email], html_message=message)

def tabroom_activation_helper(request): # not a view!!!
    user = request.user
    subject = "Tabroom/Zoom/Converter - Please verify your Tabroom email"
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = tabroom_token_generator.make_token(user)
    relative_link = reverse('zoom_converter:activate_tabroom', kwargs={'uidb64': uidb64, 'token': token})
    link = request.build_absolute_uri(relative_link)
    message = render_to_string('registration/tabroom_activation_email.html', {'link': link})
    send_mail(subject, message, EMAIL_HOST_USER, [user.tabroom_email], html_message=message)

def zoom_activation_helper(request): # not a view!!!
    user = request.user
    subject = "Tabroom/Zoom/Converter - Please verify your Zoom email"
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = zoom_token_generator.make_token(user)
    relative_link = reverse('zoom_converter:activate_zoom', kwargs={'uidb64': uidb64, 'token': token})
    link = request.build_absolute_uri(relative_link)
    message = render_to_string('registration/zoom_activation_email.html', {'link': link})
    send_mail(subject, message, EMAIL_HOST_USER, [user.zoom_email], html_message=message)













def register(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', 'zoom_converter:tournament_list'))
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            email_activation_helper(request)
            tabroom_activation_helper(request)
            zoom_activation_helper(request)
            # 'we sent you an three different emails'
            return redirect('zoom_converter:profile')
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {'form': form})







@login_required
def awaiting_email_activation(request):
    if request.user.email_confirmed:
        return redirect('zoom_converter:tournament_list')
    return HttpResponse(f'Please click the link in your email to activate.  Or click <a href="{reverse("logout")}">here</a> to log out.  Or click <a href="{reverse("zoom_converter:activation_email")}">here</a> to resend the email.')

@login_required
def send_email_activation(request):
    email_activation_helper(request)
    return redirect('zoom_converter:profile')

def activate_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except:
        user = None
    if email_token_generator.check_token(user, token):
        user.email_confirmed = True
        user.save()
        login(request, user)
        return redirect('zoom_converter:profile')
    else:
        return HttpResponse('invalid activation key')



@login_required
def awaiting_tabroom_activation(request):
    if request.user.tabroom_confirmed:
        return redirect('zoom_converter:tournament_list')
    return HttpResponse(f'Please click the link in your email to activate.  Or click <a href="{reverse("logout")}">here</a> to log out.  Or click <a href="{reverse("zoom_converter:activation_email")}">here</a> to resend the email.')

@login_required
def send_tabroom_activation(request):
    tabroom_activation_helper(request)
    return redirect('zoom_converter:profile')

def activate_tabroom(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except:
        user = None
    if tabroom_token_generator.check_token(user, token):
        user.tabroom_confirmed = True
        user.save()
        login(request, user)
        return redirect('zoom_converter:profile')
    else:
        return HttpResponse('invalid activation key')



@login_required
def awaiting_zoom_activation(request):
    if request.user.zoom_confirmed:
        return redirect('zoom_converter:tournament_list')
    return HttpResponse(f'Please click the link in your email to activate.  Or click <a href="{reverse("logout")}">here</a> to log out.  Or click <a href="{reverse("zoom_converter:activation_email")}">here</a> to resend the email.')

@login_required
def send_zoom_activation(request):
    zoom_activation_helper(request)
    return redirect('zoom_converter:profile')

def activate_zoom(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except:
        user = None
    if zoom_token_generator.check_token(user, token):
        user.zoom_confirmed = True
        user.save()
        login(request, user)
        return redirect('zoom_converter:profile')
    else:
        return HttpResponse('invalid activation key')

@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        data = [user.email, user.email_confirmed, user.tabroom_email, user.tabroom_confirmed, user.zoom_email, user.zoom_confirmed]
        form1 = EmailActivationForm(request.POST, instance=user)
        form2 = TabroomActivationForm(request.POST, instance=user)
        form3 = ZoomActivationForm(request.POST, instance=user)
        # check for duplicate people
        if form1.is_valid():
            if 'email' not in form1.changed_data:
                user.email = data[0]
                user.email_confirmed = data[1]
            else:
                email_activation_helper(request)
        if form2.is_valid():
            if 'tabroom_email' not in form2.changed_data:
                user.tabroom_email = data[2]
                user.tabroom_confirmed = data[3]
            else:
                tabroom_activation_helper(request)
        if form3.is_valid():
            if 'zoom_email' not in form3.changed_data:
                user.zoom_email = data[4]
                user.zoom_confirmed = data[5]
            else:
                zoom_activation_helper(request)
        user.save()
        return redirect('zoom_converter:profile')
    else:
        form1 = EmailActivationForm(instance=user)
        form2 = TabroomActivationForm(instance=user)
        form3 = ZoomActivationForm(instance=user)
    return render(request, 'registration/profile.html', context={'form1': form1, 'form2': form2, 'form3': form3})


# Create your views here.
