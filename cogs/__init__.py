from importlib import import_module
from discord.ext import commands

def cog_get(cog_class, *args, **kwargs):
    try:
        if '.' in cog_class:
            module_name, class_name = cog_class.rsplit('.', 1)
        else:
            module_name = cog_class
            class_name = cog_class.capitalize()

        module = import_module('.' + module_name, package='cogs')

        _class = getattr(module, class_name)

        instance = _class(*args, **kwargs)
    except (AttributeError, ModuleNotFoundError):
        raise ImportError('{} is not part of our cogs'.format(cog_class))
    except Exception as e:
        raise e

    if not issubclass(_class, commands.Cog):
        raise ImportError("We currently don't have {}, but you are welcome to send in the request for it!".format(animal_class))

    return instance