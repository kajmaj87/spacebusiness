import statistics


def log_transactions(resource_type, buy_orders, sell_orders):
    with open("ticker.log", mode="a") as ticker:
        buy_sum = sum([o.price for ent, o in buy_orders])
        sell_sum = sum([o.price for ent, o in sell_orders])
        if len(buy_orders) > 0:
            mean = statistics.mean([b[1].price + s[1].price for b, s in zip(buy_orders, sell_orders)])
            ticker.write(f"{resource_type},{mean:.2f},{(buy_sum + sell_sum) / 2:.2f},{len(buy_orders)}\n")
