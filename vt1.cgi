#!/usr/bin/python
# -*- coding: utf-8 -*-
import cgitb
import cgi
import simplejson as json
import urllib2
cgitb.enable(format="text")

print u"""Content-type: text/plain; charset=UTF-8

"""
# Ladataan json-tietorakenne.
site = urllib2.urlopen("http://appro.mit.jyu.fi/tiea2120/vt/vt1/2019/data.json")
data = json.load(site)

#Kerätään mahdolliset tiedot querystringistä.
fields = cgi.FieldStorage()
team_name = fields.getfirst(u"nimi", default=None)
team_id = fields.getfirst(u"id")
team_members = fields.getlist(u"jasenet")
leimaus = fields.getlist(u"leimaustapa")

new_team = {
      "nimi": u"Pällit",
      "jasenet": [
        u"Tommi Lahtonen",
        u"Matti Meikäläinen"
      ],
      "id": 99999,
      "leimaustapa": [
        u"GPS"
      ],
      "rastit": []
}


# Käy läpi querystring tiedot. Muokkaa lisättävää joukkuetta jos tiedot OK.
def check_fields():

    if team_name is None:
        return

    if (team_name is not None) & (team_id is not None):
        new_team["nimi"] = team_name.decode("UTF-8")
        new_team["id"] = team_id
        if len(team_members) > 0:
            new_team["jasenet"] = team_members
            if len(leimaus) > 0:
                new_team["leimaustapa"] = leimaus
    else:
        print u"Name or id is missing/invalid"
        print u"Team modifying cancelled.\n"
        

# Luodaan uutta joukkuetta. Validoi joukkueen ennen lisäystä.
def create_team(data, team, race_name, series):
    if validate_team(team):
        add_team(data, team, race_name, series)


# Validoi joukkueen. Esittää virheilmoituksen jos validointi epäonnistuu.
def validate_team(team):
    if team.get("nimi") is None:
        print "ahahaaa"
        return

    if id_available(unicode(team.get("id"))):
        return True
    else:
        print u"Invalid id parameter {id} on team {team}".format(id=team.get("id"), team=team.get("nimi")).encode("UTF-8")
        print u"Team creation cancelled.\n"
        return False
        

# Tarkastaa id:n validiuden
def id_available(id):
    if not id.isnumeric():  # Tarkastetaan onko id kokonaisluku.
        return False

    for race in data:       # Tarkastetaan onko id jo jollain käytössä.
        for series in race.get("sarjat"):
            for team in series.get("joukkueet"):
                if unicode(team.get("id")) == id:
                    return False
    return True # Id on validi.


# Printtaa kilpailut ja niihin ilmoitetut joukkueet.
def print_race_and_teams():
    teams_with_points = [] # Tuple-lista johon joukkue-piste tuplet kerätään printtausta varten

    for race in data:
        print race.get("nimi").encode("UTF-8")      # Printtaa kilpailun nimen
        for series in race.get("sarjat"):
            for team in series.get("joukkueet"):    
                points = count_points(data, race.get("nimi"), series.get("nimi"), team.get("nimi")) # Laskee kilpailuun osallistuneiden pisteet
                team = team.get("nimi")
                twp = (team, points)
                teams_with_points.append(twp)       # Lisää joukkue-piste tuplet listaan.

    teams_with_points.sort(key=lambda team: team[1], reverse=True)
    for team in teams_with_points:
        print u"    {team} ({points} p)".format(team = team[0], points = team[1]).encode("UTF-8")
    

# Lisää joukkueen annettuun kilpailuun ja sarjaan.
def add_team(data, team, race_name, series_name):
    race = find_race(data, race_name)
    if race is None:
        return
    series = find_series(race, series_name)
    if series is None:
        return
    teams = series.get("joukkueet")
    if teams is None:
        return
    teams.append(team)


# Poistaa joukkueen annetusta kilpailusta ja sarjasta.
def delete_team(data, race_name, series_name, team_name):

    race = find_race(data, race_name)
    if race is None:
        return
    series = find_series(race, series_name)
    if series is None:
        return
    team = find_team(series, team_name)
    if team is None:
        return
    teams = series.get("joukkueet")
    if teams is None:
        return
    teams.remove(team)


# laskee annetun joukkueen pisteet.
def count_points(data, race_name, series_name, team_name):

    checkpoints = find_checkpoints(find_race(data, race_name))  # Kilpailun kaikki rastit.
    team = find_team(find_series(find_race(data, race_name), series_name), team_name)
    team_checkpoints = team.get("rastit")                       # Joukkueen käymät rastit.
    
    result = 0
    for point in team_checkpoints:                              # Laskee joukkueen pisteet yhteeen.
        result += parse_points(find_checkpoint_code(unicode(point.get("rasti")), checkpoints)) 
    return result


# Palauttaa rastin koodin mukaisen pistemäärän.
def parse_points(check_point_code):
    if check_point_code is None:
        return 0
    else:
        if check_point_code[0].isalpha(): # Ensimmäinen merkki on kirjain -> 0p
            return 0
        else:
            return int(check_point_code[0])


# Etsii tietorakenteesta kilpailun. 
def find_race(data, race_name):
    for race in data:
        if race.get("nimi") == race_name:
            return race


# Etsii tietorakenteesta kilpailun sarjan.
def find_series(race, series_name):
    for series in race.get("sarjat"):
        if series.get("nimi") == series_name:
            return series


# Etsii kilpailun kaikki rastit.
def find_checkpoints(race):
    return race.get("rastit")


# Etsii sarjasta joukkueen.
def find_team(series, team_name):
    for team in series.get("joukkueet"):
        if team.get("nimi") == team_name:
            return team


# Etsii käytyä rastia vastaavan koodin kaikista rasteista.
def find_checkpoint_code(point_id, checkpoints):
    for point in checkpoints:
        if unicode(point.get("id")) == point_id:
            return point.get("koodi")

# Tarkastaa querystringin sisällön ja muuttaa lisättävää joukkuetta tarpeen mukaan.
check_fields()

# Luo uutta joukkuetta
create_team(data, new_team, u"Jäärogaining", u"4h")

# Poistaa kolme joukuetta 
delete_team(data, u"Jäärogaining", u"8h", u"Vara 1")
delete_team(data, u"Jäärogaining", u"8h", u"Vara 2")
delete_team(data, u"Jäärogaining", u"4h", u"Vapaat")

# Printtaa joukkueet
print_race_and_teams()                                  
