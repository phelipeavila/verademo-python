from app.commands import BlabberCommand
import logging

class IgnoreCommand(BlabberCommand):
    logger = logging.getLogger("__name__")