from .models import Room, Team, School, User

def create_pairings(reader, round):
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

def import_events(reader, tournament):
    tournament.events.all().delete()
    for row in reader:
        if row[0] == "Total":
            return
        tournament.events.create(name=row[0], code=row[1])

def import_schools():
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


def import_judges():
    return


def import_entries_full():
    return

def import_entries_emails():
    return
