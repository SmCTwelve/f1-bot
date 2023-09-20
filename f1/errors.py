
class BotError(Exception):
    """Base error class for the bot."""

    def __init__(self, *args):
        super().__init__(*args)


class MissingDataError(BotError):
    """Raised if data required for the execution of a command is unavailable.

    Should be raised instead of returning `None` as it is more explicit and
    can be handled by `bot.on_command_error()`.
    """

    def __init__(
        self,
        message="Returned data missing or invalid, results could not be processed."
    ):
        self.message = message
        super().__init__(self.message)


class MessageTooLongError(BotError):
    """Raised if the message exceeds Discord's 2000 char limit on messages."""

    def __init__(self, message, orig_message):
        self.message = message
        self.length = len(orig_message)
        self.diff = self.length - 2000


class DriverNotFoundError(BotError):
    """Raised if the driver ID given to a command does not match a known driver."""

    def __init__(self):
        self.message = "The provided driver could not be found."
        super().__init__(self.message)
