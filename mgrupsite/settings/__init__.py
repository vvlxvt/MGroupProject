from environs import Env

env = Env()
env.read_env()

DJANGO_ENV = env("DJANGO_ENV", default="dev")

if DJANGO_ENV == "prod":
    from .prod import *
else:
    from .dev import *
