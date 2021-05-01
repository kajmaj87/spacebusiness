import globals


class Ticker:
    def __init__(self):
        self.ticker = open("ticker.csv", mode="w")

    def log_transactions(self, resource_type):
        if globals.stats_history.has_stats_for_day(globals.star_date, resource_type):
            today_stats = globals.stats_history.stats_for_day(globals.star_date, resource_type)
            self.ticker.write(today_stats.as_csv() + "\n")
