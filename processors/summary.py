import esper

import globals
from components import Resource, Money, Details, Storage, Wallet
from log import log
from .pure import total_money_in_wallets
from transaction_logger import Ticker


class TurnSummaryProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.ticker = Ticker()

    def process(self):
        log.info(f"Total money: {total_money_in_wallets(self.world)}")
        log.info(f"Prices in {globals.star_date}:")
        for resource in Resource:
            if globals.stats_history.has_stats_for_day(globals.star_date, resource):
                log.info(globals.stats_history.stats_for_day(globals.star_date, resource))
            self.ticker.log_transactions(resource)

        log.info("Richest entities:")
        money_in_rich_pockets = Money(0)
        for ent, (details, storage, wallets) in sorted(self.world.get_components(Details, Storage, Wallet), key=lambda x: -x[1][2].money.creds)[0:5]:
            log.info(f"{details.name} has {wallets.money} left. Storage: {storage}")
            money_in_rich_pockets += wallets.money
        log.info(
            f"Richest have {money_in_rich_pockets} accounting for {money_in_rich_pockets.creds/total_money_in_wallets(self.world).creds*100:.2f}% of total cr"
        )
