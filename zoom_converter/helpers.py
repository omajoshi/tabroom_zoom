from .models import Room, Team

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
