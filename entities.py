from components import (
    Consumer,
    Details,
    Money,
    Need,
    Needs,
    Producer,
    Resource,
    ResourcePile,
    Storage,
    Wallet,
)


def create_person(world, name, food_consumption, food_amount, water_consumption, water_amount, money):
    person = world.create_entity()
    storage = Storage()
    storage.add(ResourcePile(Resource.FOOD, food_amount))
    storage.add(ResourcePile(Resource.WATER, water_amount))
    # not possible to store man days
    storage.set_limit(ResourcePile(Resource.MAN_DAY, 1))

    needs = Needs()
    needs.add(
        Need(
            "have water for tomorrow",
            priority=0,
            pile=ResourcePile(Resource.WATER, water_consumption),
            price_change_on_buy=0.8,
            price_change_on_failed_buy=1.1,
        )
    )
    needs.add(
        Need(
            "have food for tomorrow",
            priority=1,
            pile=ResourcePile(Resource.FOOD, food_consumption),
            price_change_on_buy=0.8,
            price_change_on_failed_buy=1.1,
        )
    )
    needs.add(
        Need(
            "have water for next few days",
            priority=2,
            pile=ResourcePile(Resource.WATER, 5 * water_consumption),
            price_change_on_buy=0.8,
            price_change_on_failed_buy=1.1,
        )
    )
    needs.add(
        Need(
            "have food for next few days",
            priority=2,
            pile=ResourcePile(Resource.FOOD, 4 * food_consumption),
            price_change_on_buy=0.8,
            price_change_on_failed_buy=1.1,
        )
    )
    needs.add(
        Need(
            "have a big stash of water",
            priority=3,
            pile=ResourcePile(Resource.WATER, 15 * water_consumption),
            price_change_on_buy=0.8,
            price_change_on_failed_buy=1.1,
        )
    )
    needs.add(
        Need(
            "have a big stash of food",
            priority=3,
            pile=ResourcePile(Resource.FOOD, 10 * food_consumption),
            price_change_on_buy=0.8,
            price_change_on_failed_buy=1.1,
        )
    )

    world.add_component(person, Details(name))
    world.add_component(person, Wallet(Money(money)))
    consumption = Consumer()
    consumption.add_need(ResourcePile(Resource.FOOD, food_consumption))
    consumption.add_need(ResourcePile(Resource.WATER, water_consumption))
    world.add_component(person, consumption)
    # man days are produced from nothing
    world.add_component(person, Producer(ResourcePile(Resource.NOTHING, 0), ResourcePile(Resource.MAN_DAY)))
    # simplified growth process so that human cannot grow before is bought at cloning center
    # world.add_component(person, Producer(ResourcePile(Resource.EMBRYO), ResourcePile(Resource.GROWN_HUMAN)))
    world.add_component(person, storage)
    world.add_component(person, needs)
    return person


def create_well(world, name, labour_consumption, water_production, water_storage, money):
    entity = world.create_entity()
    storage = Storage()
    storage.set_limit(ResourcePile(Resource.WATER, water_storage))

    needs = Needs()
    needs.add(
        Need(
            "have someone in work",
            priority=1,
            pile=ResourcePile(Resource.MAN_DAY),
            price_change_on_buy=0.9,
            price_change_on_failed_buy=1.1,
        )
    )

    world.add_component(entity, Details(name))
    world.add_component(entity, Wallet(Money(money)))
    world.add_component(
        entity,
        Producer(ResourcePile(Resource.MAN_DAY, labour_consumption), ResourcePile(Resource.WATER, water_production)),
    )
    world.add_component(entity, storage)
    world.add_component(entity, needs)
    return entity


def create_farm(world, name, labour_consumption, food_production, food_storage, money):
    farm = world.create_entity()
    storage = Storage()
    storage.set_limit(ResourcePile(Resource.FOOD, food_storage))

    needs = Needs()
    needs.add(
        Need(
            "have someone in work",
            priority=1,
            pile=ResourcePile(Resource.MAN_DAY),
            price_change_on_buy=0.9,
            price_change_on_failed_buy=1.1,
        )
    )
    # needs.add(Need("have someone in work", priority=2, pile=ResourcePile(Resource.MAN_DAY), price_change_on_buy=0.8, price_change_on_failed_buy=1.05))
    # needs.add(Need("have someone in work", priority=3, pile=ResourcePile(Resource.MAN_DAY), price_change_on_buy=0.7, price_change_on_failed_buy=1.02))

    world.add_component(farm, Details(name))
    world.add_component(farm, Wallet(Money(money)))
    world.add_component(farm, Producer(ResourcePile(Resource.MAN_DAY, labour_consumption), ResourcePile(Resource.FOOD, food_production)))
    world.add_component(farm, storage)
    world.add_component(farm, needs)
    return farm


def create_cloning_center(world, name, embryo_storage, embryo_food_cost, money):
    cloning_center = world.create_entity()

    storage = Storage()
    storage.set_limit(ResourcePile(Resource.EMBRYO, embryo_storage))

    needs = Needs()
    needs.add(
        Need(
            "food for one embryo",
            priority=1,
            pile=ResourcePile(Resource.FOOD, embryo_food_cost),
            price_change_on_buy=0.95,
            price_change_on_failed_buy=1.1,
        )
    )
    needs.add(
        Need(
            "food for some more embrios",
            priority=2,
            pile=ResourcePile(Resource.FOOD, embryo_food_cost * 2),
            price_change_on_buy=0.9,
            price_change_on_failed_buy=1.05,
        )
    )
    needs.add(
        Need(
            "food for even more embrios",
            priority=3,
            pile=ResourcePile(Resource.FOOD, embryo_food_cost * 3),
            price_change_on_buy=0.9,
            price_change_on_failed_buy=1.05,
        )
    )
    # needs.add(Need("have someone in work", priority=3, pile=ResourcePile(Resource.MAN_DAY), price_change_on_buy=0.7, price_change_on_failed_buy=1.02))

    world.add_component(cloning_center, Details(name))
    world.add_component(cloning_center, Wallet(Money(money)))
    # FIXME this should create embryo first but producing system allows only for one person to produce one thing
    # (no more labor if man needs to change embrio to grown_human)
    # world.add_component(cloning_center, Producer(ResourcePile(Resource.FOOD, embryo_food_cost), ResourcePile(Resource.EMBRYO)))
    world.add_component(cloning_center, Producer(ResourcePile(Resource.FOOD, embryo_food_cost), ResourcePile(Resource.GROWN_HUMAN)))
    world.add_component(cloning_center, storage)
    world.add_component(cloning_center, needs)
    return cloning_center
