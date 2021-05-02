import esper
import icontract as icontract

from components import Money, Terminated, Wallet
from log import log

from .pure import total_money_in_wallets


class WealthRedistribution(esper.Processor):
    def __init__(self, tax_rate: float = 0):
        super().__init__()
        self.tax_rate = tax_rate

    @icontract.snapshot(lambda self: self)
    @icontract.ensure(lambda OLD, self: total_money_in_wallets(self.world) == total_money_in_wallets(OLD.self.world))
    def process(self):
        money_before_redistribution = total_money_in_wallets(self.world)
        money_for_redistribution = Money(0)
        total_wallets = len(self.world.get_component(Wallet))
        last_wallet = None
        for ent, wallet in self.world.get_component(Wallet):
            if not self.world.has_component(ent, Terminated):
                tax = wallet.money.multiply(self.tax_rate)
                money_for_redistribution += tax
                wallet.money -= tax
        ubi_value = money_for_redistribution.multiply(1 / total_wallets)
        for ent, wallet in self.world.get_component(Wallet):
            if not self.world.has_component(ent, Terminated):
                money_for_redistribution -= ubi_value
                wallet.money += ubi_value
                last_wallet = wallet
        # last one gets whats left
        if last_wallet is not None:
            last_wallet.money += money_for_redistribution
        log.info(f"Ubi this round is: {ubi_value}")
        assert money_before_redistribution == total_money_in_wallets(
            self.world
        ), f"Redistributing money should not change the amount of it: {money_before_redistribution} changed to {total_money_in_wallets(self.world)}"
