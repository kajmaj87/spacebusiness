from components import Consumer, ResourcePile, Resource, Details, Storage


def createPerson(world, name, food_consumption, food_amount):
       person = world.create_entity()
       storage = Storage()
       storage.add(Resource.FOOD, food_amount)

       world.add_component(person, Details(name))
       world.add_component(person, Consumer(ResourcePile(Resource.FOOD, food_consumption)))
       world.add_component(person, storage)
       return person



