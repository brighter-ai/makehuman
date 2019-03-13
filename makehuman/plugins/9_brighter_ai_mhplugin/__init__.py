from .brighter_ai_taskview import BrighterAITaskView


def load(app):
    category = app.getCategory('Brighter AI')
    category.addTask(BrighterAITaskView(category))
    # event_handler = Randomizer()
    # app.addEventHandler(event_handler, 1)


def unload(app):
    pass
