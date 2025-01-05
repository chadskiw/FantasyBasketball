from flask import Flask, render_template, request, jsonify
from espn_api.basketball import League
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# ESPN Credentials
credentials = {
    "league_id": "1561125630",
    "year": 2025,
    "espn_s2": "AEBtVQdRMtsKiytYgqILfvXaQV1B+Uj+Jdd1rgbfx13+qsgET3mDsvk/WtDdj3u9h2fKr8EFeHgOSZ8Ku4j/dmZlTjArDDLJIilOV7tD9eywK3SZF37JNZotIE2S73Ua1c9ELAmcsaqM9flQltdKvSKdN3ogtJKZa4iIecHidadCPZjI9vIVKoyMBde1KQMUy/gxbSlaUrkx18FxOoe7rkwa05w2aiTTz3541FjRgTU9QSEJftr4qxlrNxDM1wc60AZWTrTzl9lKQcxPs4MPUkCuou07iXqTuY5rHaX0t56FmA==",
    "swid": "{32307DF3-17F9-4871-A074-9EEE4BCE889F}"
}

# Load the league
def load_league():
    return League(
        league_id=credentials["league_id"],
        year=credentials["year"],
        espn_s2=credentials["espn_s2"],
        swid=credentials["swid"]
    )

# Load and preprocess schedule
schedule_df = pd.read_excel("static\\NBASchedule.xlsx")
schedule_df['Game Date'] = pd.to_datetime(schedule_df['Game Date'])
schedule_df['DOW'] = schedule_df['DOW'].str.strip()
schedule_df['Visit'] = schedule_df['Visit'].str.strip()
schedule_df['Home'] = schedule_df['Home'].str.strip()

# Day of Week Mapping
days_in_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def get_schedule_for_next_seven_days(league, selected_team):
    """
    Create the best schedule for the next seven days, starting from today in the current week
    and continuing into the next week if necessary.
    """
    today = datetime.now()
    current_week = today.isocalendar()[1] + 10  # Adjust to NBA season weeks
    current_dow = today.strftime('%a')  # Current day of the week (e.g., 'Thu')
    current_dow_index = days_in_week.index(current_dow)

    # Generate days for the current week from today onward
    remaining_days_current_week = days_in_week[current_dow_index:]

    # Calculate how many days are needed from the next week
    days_needed_from_next_week = 7 - len(remaining_days_current_week)

    # Generate days for the next week if needed
    days_from_next_week = days_in_week[:days_needed_from_next_week]

    # Combine the two to get the next 7 days
    next_seven_days = remaining_days_current_week + days_from_next_week

    # Filter schedule for the relevant days in current and next weeks
    schedule_in_range = schedule_df[
        ((schedule_df["Week"] == current_week) & (schedule_df["DOW"].isin(remaining_days_current_week))) |
        ((schedule_df["Week"] == current_week + 1) & (schedule_df["DOW"].isin(days_from_next_week)))
    ]

    daily_schedule = {day: [] for day in next_seven_days}
    day_summary = {day: {"player_count": 0, "total_points": 0} for day in next_seven_days}
    suggested_pickups = []
    drop_candidates = []

    def process_player(player, source="free_agent"):
        try:
            team_abbreviation = player.proTeam

            # Filter games for the player's team
            team_games = schedule_in_range[
                (schedule_in_range["Visit"] == team_abbreviation) |
                (schedule_in_range["Home"] == team_abbreviation)
            ]

            # Extract and sort game days to match next_seven_days order
            game_days = sorted(
                team_games["DOW"].tolist(),
                key=lambda day: next_seven_days.index(day)
            )
            games_in_week = len(game_days)

            # Fetch average points (if available)
            average_points = player.stats.get('2025_total', {}).get('applied_avg', 0)

            # Prepare player data
            player_data = {
                "name": player.name,
                "status": player.injuryStatus,
                "position": player.position,
                "team": player.proTeam,
                "source": source,
                "games_in_week": games_in_week,
                "game_days": ", ".join(game_days),
                "average_points": average_points,
            }

            # Add player to appropriate list
            if source == "free_agent":
                suggested_pickups.append(player_data)
            elif source == selected_team:
                drop_candidates.append(player_data)
                for day in game_days:
                    if len(daily_schedule[day]) < 10:  # Max 10 players per day
                        daily_schedule[day].append(player_data)
                        day_summary[day]["player_count"] += 1
                        day_summary[day]["total_points"] += average_points
        except Exception as e:
            print(f"Error processing player {player.name} from {source}: {e}")

    # Process free agents
    for player in league.free_agents():
        process_player(player, source="free_agent")

    # Process players for the selected team
    for team in league.teams:
        if team.team_name == selected_team:
            for player in team.roster:
                process_player(player, source=selected_team)

    return {
        "daily_schedule": daily_schedule,
        "suggested_pickups": suggested_pickups,
        "day_summary": day_summary,
        "drop_candidates": drop_candidates,
        "selected_team": selected_team
    }


@app.route('/recommendations', methods=['POST'])
def recommendations():
    try:
        selected_team = request.json.get("team")
        if not selected_team:
            raise ValueError("Team selection is required.")

        league = load_league()
        result = get_schedule_for_next_seven_days(league, selected_team)

        return jsonify(result)
    except Exception as e:
        print(f"Error in recommendations route: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/')
def home():
    try:
        league = load_league()
        team_names = [team.team_name for team in league.teams]
        return render_template('index.html', teams=team_names)
    except Exception as e:
        print(f"Error in home route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
