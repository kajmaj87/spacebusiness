from components import Consumer, ResourcePile, Resource, Details, Storage, Producer


def createPerson(world, name, food_consumption, food_amount):
    person = world.create_entity()
    storage = Storage()
    storage.add(ResourcePile(Resource.FOOD, food_amount))
    # not possible to store man days
    storage.set_limit(ResourcePile(Resource.MAN_DAY, 1))

    world.add_component(person, Details(name))
    world.add_component(person, Consumer(ResourcePile(Resource.FOOD, food_consumption)))
    # man days are produced from nothing
    world.add_component(person, Producer(ResourcePile(Resource.NOTHING), ResourcePile(Resource.MAN_DAY, 1)))
    world.add_component(person, storage)
    return person
