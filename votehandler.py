import json
from teams_dict import teams_dict
from datetime import datetime, timedelta

VOTESFILE = 'votes.json'
POINTS_TOP_SCORER = 15
POINTS_WINNER = 15


class VoteHandler():
    def load_data(self):
        with open(VOTESFILE, 'r') as json_file:
            return json.load(json_file)

    def save(self, json_data):
        with open(VOTESFILE, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

    def add_top_scorer(self, id):
        data = self.load_data()
        id = int(id)
        if id < 1 or id > len(data["top_scorer"]["players"]):
            return f"A match with ID {id} does not exist"
        data["results"]["player_won"] = data["top_scorer"]["players"][id-1]["name"]
        self.save(data)
        return f"Top scorer was added"

    def add_winner(self, id):
        data = self.load_data()
        id = int(id)
        if id < 1 or id > len(data["winner"]["countries"]):
            return f"A country with ID {id} does not exist"
        data["results"]["country_won"] = data["winner"]["countries"][id-1]["name"]
        self.save(data)
        return f"Cup winner was added"

    def bet_winner(self, country_id, username):
        if datetime.now() + timedelta(hours=2) > datetime(2026, 6, 14):
            return "Voting closed"
        data = self.load_data()
        country_id = int(country_id)
        if country_id < 1 or country_id > len(data["winner"]["countries"]):
            return f"A country with ID {country_id} does not exist"
        for country in data["winner"]["countries"]:
            if username in country["voters"]:
                country["voters"].remove(username)
        data["winner"]["countries"][country_id-1]["voters"].append(username)
        self.save(data)
        return f"Cup winner bet submitted"

    def bet_top_scorer(self, player_id, username):
        if datetime.now() + timedelta(hours=2) > datetime(2026, 6, 14):
            return "Voting closed"
        data = self.load_data()
        player_id = int(player_id)
        if player_id < 1 or player_id > len(data["top_scorer"]["players"]):
            return f"A player with ID {player_id} does not exist"
        for player in data["top_scorer"]["players"]:
            if username in player["voters"]:
                player["voters"].remove(username)
        data["top_scorer"]["players"][player_id-1]["voters"].append(username)
        self.save(data)
        return f"Top scorer bet submitted"        

    def get_votes(self):
        data = self.load_data()
        countries = {}
        players = {}       
        for country in data["winner"]["countries"]:
            for voter in country["voters"]:
                countries[voter] = teams_dict[country["name"]]
        for player in data["top_scorer"]["players"]:
            for voter in player["voters"]:
                players[voter] = f"{player['name']} :{teams_dict[player['country']]}:"
        return countries, players

    def get_points(self):
        data = self.load_data()
        points = {}

        # Calculate points for predicting the winner
        winner = data["results"]["country_won"]
        for country in data["winner"]["countries"]:
            if country["name"] == winner:
                for username in country["voters"]:
                    if username not in points:
                        points[username] = 0
                    points[username] += POINTS_WINNER

        # Calculate points for predicting the top scorer
        top_scorer = data["results"]["player_won"]
        for player in data["top_scorer"]["players"]:
            if player["name"] == top_scorer:
                for username in player["voters"]:
                    if username not in points:
                        points[username] = 0
                    points[username] += POINTS_TOP_SCORER

        return points


    def get_vote_info(self):
        data = self.load_data()
        return {
            "countries": [teams_dict[c["name"]] for c in data["winner"]["countries"]],
            "players": [[p["name"], p["country"]] for p in data["top_scorer"]["players"]]
        }
