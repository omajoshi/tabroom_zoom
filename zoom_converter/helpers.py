import csv, io

from django.shortcuts import render, get_object_or_404

from .models import Room, School, Event, Team, Person, User

def parse_pairings(reader, round):
    num_rooms = 0
    while row:=next(reader):
        if not row:
            break
        num_rooms += 1
    next(reader)
    for x in range(num_rooms):
        row = next(reader) # gets the pairing and room number on top of the name block
        print(row)
        room = Room.objects.create(number=row[1])
        pairing = round.pairings.create(room=room)
        judge_mode_activated = False
        while row:=next(reader):
            if judge_mode_activated:
                try:
                    judge, e_j = round.event.tournament.judges.get_or_create(name=f"{row[1]} {row[2]}")
                    pairing.judges.add(judge)
                except Team.DoesNotExist:
                    print(f"Potential problem with {row[1]} {row[2]}")
            elif not row[0]:
                judge_mode_activated = True
                continue
            else:
                try:
                    team1 = round.event.teams.get(code=row[0])
                    pairing.teams.add(team1)
                except Team.DoesNotExist:
                    print(f"Potential problem with {row[0]}")



def generate_pairing_files():
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

def import_events(reader, tournament):
    tournament.events.all().delete()
    for row in reader:
        if row[0] == "Total":
            return
        tournament.events.create(name=row[0], code=row[1])

def import_schools(reader, tournament):
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


def import_judges(reader, tournament):
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

def import_entries(reader, tournament):
    for row in reader:
        event = get_object_or_404(Event, tournament=tournament, code=row[1])
        school = tournament.schools.get(name=row[4])
        team, created = event.teams.get_or_create(school=school, code=row[0])
        if not created:
            continue
        try:
            col = 13
            while True:
                testing = row[col+2]
                person, created = Person.objects.get_or_create(school=school, name=row[col])
                team.members.add(person)
                col += 3
        except:
            pass

def import_emails(reader, tournament):
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


def validate_csv(file):
    if not file.name.endswith('.csv'):
        return False
    return True

def configure_tournament(tournament, files):
    for file, function in zip(files, (import_events, import_schools, import_judges, import_entries, import_emails)):
        data_set = file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        reader = csv.reader(io_string, delimiter=',', quotechar='"')
        headers = next(reader)
        function(reader, tournament)
