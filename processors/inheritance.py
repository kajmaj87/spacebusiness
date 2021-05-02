from random import choice

import esper

from components import Details, InheritancePool, Storage, Terminated, Wallet
from log import log


class InheritanceLottery(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for _, (pool_storage, pool_wallet, _) in self.world.get_components(Storage, Wallet, InheritancePool):
            if pool_wallet.money.creds > 0:
                winner, (details, storage, wallet) = choice(self.world.get_components(Details, Storage, Wallet))
                half, _ = pool_wallet.money.split()
                if not self.world.has_component(winner, Terminated):
                    log.debug(f"{details.name} won {half} at the inheritance lottery!")
                    wallet.money += half
                    pool_wallet.money -= half
                else:
                    log.debug(f"{details.name} won {half} at the inheritance lottery but was already dead!")
                log.debug(f"Inheritance pool contents: {pool_wallet.money} and {pool_storage}")
