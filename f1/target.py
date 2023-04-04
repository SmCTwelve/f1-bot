from discord import ApplicationContext
from discord.ext.commands import Context

from f1.config import Config


class MessageTarget:
    """Uses the appropriate response target based on the command context and config settings.

    Can send messages to user as DM, reply to the message using `commands.Context` or use an `Interaction.response`
    when used with an `ApplicationContext`.
    """

    def __init__(self, ctx: Context | ApplicationContext):
        if not (isinstance(ctx, (Context, ApplicationContext))):
            raise ValueError("No context available for message target.")
        self.ctx = ctx
        self.settings = Config().settings

    def send(self, *args, **kwargs):
        return self._get_send()(*args, **kwargs)

    def _get_send(self):
        """Return a reference to the send method to use for the context."""
        # Target DM channel
        if self.settings["MESSAGE"]["DM"]:
            return self.ctx.author.send
        # Use Application response for slash commands
        if isinstance(self.ctx, ApplicationContext):
            return self.ctx.respond
        # Use normal reply for message commands
        return self.ctx.reply
