from components import (
    BuyOrder,
    Wallet,
    Money,
)


def total_money_in_wallets(world) -> Money:
    wallets = world.get_component(Wallet)
    return Money(sum([w.money.creds for ent, w in wallets]))


def total_money_locked_in_orders(world) -> Money:
    buy_orders = world.get_component(BuyOrder)
    return Money(sum([o.price.creds for ent, o in buy_orders]))
