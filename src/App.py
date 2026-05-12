from channels.ChannelViewModel import ChannelViewModel
from sessions import SessionViewModel


class App:
    """
    This class will hold the references to the view models and services that need to exist
    for the lifetime of the application.

    Why do we need to do this?

    PySide6 automatically cleans up any view models that don't have references. This means
    that when you navigate to a different page in the app, then the old view model is cleared.
    This means that message history will also be cleared (not very UX friendly). Also, the session
    would be cleared, rendering the whole thing useful because we 'lost' the session ID.
    """
    async def initialise(self):
        pass

    def __init__(self):
        pass
