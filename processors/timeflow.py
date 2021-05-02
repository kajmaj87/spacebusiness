import esper

import globals
from log import log

from .pure import total_money_in_wallets


class Timeflow(esper.Processor):
    def __init__(self):
        super().__init__()
        self.total_money_at_start = None

    def process(self):
        globals.star_date.increase()
        log.info(f"It is now {globals.star_date}. Total money: {total_money_in_wallets(self.world)}")
        if self.total_money_at_start is None:
            self.total_money_at_start = total_money_in_wallets(self.world)
        if self.total_money_at_start.creds != total_money_in_wallets(self.world).creds:
            raise Exception(
                f"Total money changed from {self.total_money_at_start} to {total_money_in_wallets(self.world)}. "
                f"(diff {self.total_money_at_start.creds - total_money_in_wallets(self.world).creds}cr)"
            )
