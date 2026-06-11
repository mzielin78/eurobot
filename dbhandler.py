import json
from datetime import datetime, timedelta
from teams_dict import teams_dict
from votehandler import VoteHandler

DBFILE = 'bets.json'
POINTS_RESULT_PREDICTED = 8
POINTS_WINNER_PREDICTED = 3


class DBHandler():
    def load_data(self):
        with open(DBFILE, 'r') as json_file:
            return json.load(json_file)

    def add_bet(self, id, username, result):
        data = self.load_data()
        if int(id) < 1 or int(id) > len(data["matches"]):
            return f"A match with ID {id} does not exist"
        for match in data['matches']:
            if str(match['match_id']) == str(id):
                if self.can_add_bet(match):
                    # Check if the user already has a bet
                    for bet in match['bets']:
                        if bet['user'] == username:
                            # Update the user's proposed result
                            bet['proposed_result'] = result
                            break
                    else:
                        # If the user doesn't have a bet, append a new one
                        match['bets'].append({"user": username, "proposed_result": result})
                else:
                    return f"Betting closed for match with ID {id}"
        self.save(data)
        return f"A match with ID {id} updated"

    def save(self, json_data):
        with open(DBFILE, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

    def is_winner_predicted(self, actual_score, actual_result):
        result1, result2 = map(int, actual_result.split('-'))
        score1, score2 = map(int, actual_score.split('-'))

        return (score1 > score2 and result1 > result2) or \
        (score1 < score2 and result1 < result2) or \
        (score1 == score2 and result1 == result2)

    def is_result_predicted(self, actual_score, actual_result):
        result1, result2 = map(int, actual_result.split('-'))
        score1, score2 = map(int, actual_score.split('-'))
        return score1 == result1 and score2 == result2

    def get_leaderboard(self):
        vote_handler = VoteHandler()
        leaderboard = vote_handler.get_points()
        data = self.load_data()

        for match in data["matches"]:
            actual_result = match["result"]

            if actual_result:

                for bet in match["bets"]:
                    user = bet["user"]
                    proposed_result = bet["proposed_result"]
                    
                    if user not in leaderboard:
                        leaderboard[user] = 0
                    
                    if self.is_result_predicted(proposed_result, actual_result):
                        leaderboard[user] += POINTS_RESULT_PREDICTED
                    elif self.is_winner_predicted(proposed_result, actual_result):
                        leaderboard[user] += POINTS_WINNER_PREDICTED

        leaderboard = sorted(leaderboard.items(), key=lambda item: item[1], reverse=True)
        return leaderboard

    def can_add_bet(self, match):
        datetime_str = match["date"] + ' ' + match["time"]
        match_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        return match_datetime > datetime.now() + timedelta(hours=2)

    def get_users_predictions(self, username):
        predictions = []
        data = self.load_data()
        for match in data["matches"]:
            match_info = {
                "match_id": match["match_id"],
                "teams": ":" + teams_dict[match["team1"]] + ": vs :" + teams_dict[match["team2"]] + ":",
                "result": match["result"],
                "bet": "..."
            }
            for bet in match["bets"]:
                if bet["user"] == username:
                    match_info["bet"] = bet["proposed_result"]
            predictions.append(match_info)

        return predictions
    
    def get_schedule(self):
        schedule = []
        data = self.load_data()
        for match in data["matches"]:
            match_info = {
                "match_id": match["match_id"],
                "teams": ":" + teams_dict[match["team1"]] + ": vs :" + teams_dict[match["team2"]] + ":",
                "datetime": datetime.strptime(f"{match['date']} {match['time']}", "%Y-%m-%d %H:%M")
            }
            schedule.append(match_info)
        return schedule

    def add_match(self, id, team1, team2):
        data = self.load_data()
        if team1 not in teams_dict.keys() or team2 not in teams_dict.keys():
            return f"Given teams do not participate in the tournament"
        if int(id) < 1 or int(id) > len(data["matches"]):
            return f"A match with ID {id} does not exist"
        for match in data['matches']:
            if str(match['match_id']) == str(id):
                match['team1'] = team1
                match['team2'] = team2
                break
        self.save(data)
        return f"Teams successfully added"

    def add_result(self, id, result):
        data = self.load_data()
        if int(id) < 1 or int(id) > len(data["matches"]):
            return f"A match with ID {id} does not exist"
        for match in data['matches']:
            if str(match['match_id']) == str(id):
                match['result'] = result
                print(match)
                break
        self.save(data)
        return f"Successfully added the match result"
    
    def get_bets_for_match(self, id):
        data = self.load_data()
        index = id - 1
        match = data['matches'][index] 
        return {
            "teams": ":" + teams_dict[match["team1"]] + ": vs :" + teams_dict[match["team2"]] + ":",
            "bets": match['bets']
        }
