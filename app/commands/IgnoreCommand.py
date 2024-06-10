from app.commands import BlabberCommand
from typing import override
import logging

class IgnoreCommand(BlabberCommand):
    logger = logging.getLogger("VeraDemo:IgnoreCommand")

    connect = None
    username = None

    def __init__(self, connect, username):
        super()
        self.connect = connect
        self.username = username

    @override
    def execute(self, blabberUsername):
        sqlQuery = "DELETE FROM listeners WHERE blabber='%s' AND listener='%s';"
        self.logger.info(sqlQuery)