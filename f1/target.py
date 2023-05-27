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
        self.msg_settings = Config().settings["MESSAGE"]
        self.kwargs = None

    def send(self, *args, **kwargs):
        self.kwargs = kwargs
        # Passes the args into the function returned by _get_send(), not the call itself
        return self._get_send()(*args, **self.kwargs)

    def _get_send(self):
        """Return a reference to the send method to use for the context."""
        # Target DM channel
        if self.msg_settings.getboolean("DM") is True:
            return self.ctx.author.send
        # Use ApplicationContext webhook followup for deferred slash commands
        if isinstance(self.ctx, ApplicationContext):
            self.kwargs["ephemeral"] = self.msg_settings.getboolean("EPHEMERAL")
            return self.ctx.followup.send
        # Use normal reply for message commands
        return self.ctx.reply
