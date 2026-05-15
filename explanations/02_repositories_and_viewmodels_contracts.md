# Repository and ViewModel Contracts

## Why contracts matter

A contract is an agreement about what a class exposes and what other code can expect from it.

For this project, every feature should have two important contracts:

```text
Repository contract:
    protocol request -> response model or Error

ViewModel contract:
    user/app intent -> state update + emitted screen state
```

This keeps every feature predictable.

The channel feature is the current example. It already has repository methods such as:

- `get_channels()`
- `get_channel_details(channel)`
- `create_channel(channel)`
- `join_channel(channel)`
- `leave_channel(channel)`

The channel view model then exposes similar use-case functions for the screen:

- `load_channels()`
- `select_channel(channel)`
- `join_channel(channel)`
- `leave_channel(channel)`
- `get_channel_info(channel)`
- `create_channel(name, description)`

That pattern should be repeated for users, messages, login, and app-wide state.

## Repository rules

### Rule 1: one function per use case

Do not create one large repository function that handles many different operations.

Prefer this:

```python
async def get_users(self) -> list[User] | Error:
    ...

async def get_user_details(self, user: User) -> UserDetailed | Error:
    ...

async def send_message(self, channel: Channel, content: str) -> Message | Error:
    ...
```

Avoid this:

```python
async def do_user_thing(self, action: str, payload: dict):
    ...
```

The first approach gives the view model a clean and finite API.

### Rule 2: repositories convert protocol objects into app models

The repository should hide protocol details from the view model.

For example, the repository may receive this from the protocol:

```python
ListChannelsResponse
```

But it should return app-level models:

```python
list[Channel]
```

The view model should not need to know about `ListChannelsResponse`, `ChannelInfoResponse`, or `ErrorResponse`.

### Rule 3: return `Error`, not raw `ErrorResponse`

The protocol layer may return `ErrorResponse`, but the repository should convert it into the app-level error model.

Recommended pattern:

```python
async def get_channel_details(self, channel: Channel) -> ChannelDetailed | Error:
    response: ChannelInfoResponse | ErrorResponse = await self._client.send_request(
        ChannelInfoRequest(channel=channel.name)
    )

    if isinstance(response, ErrorResponse):
        return Error(response.message)

    return ChannelDetailed(
        name=response.channel,
        description=response.description,
    )
```

This means the view model only has to check for `Error`.

### Rule 4: be consistent with error handling

Do not mix these patterns:

```python
return Error(response.message)
return False
return None
raise Exception(...)
```

Pick one predictable pattern for expected server or protocol errors.

For this project, the cleanest pattern is:

```python
SuccessfulModel | Error
```

or:

```python
bool | Error
```

For example:

```python
async def leave_channel(self, channel: Channel) -> bool | Error:
    response: LeaveChannelResponse | ErrorResponse = await self._client.send_request(
        LeaveChannelRequest(channel=channel.name)
    )

    if isinstance(response, ErrorResponse):
        return Error(response.message)

    return response.channel == channel.name
```

Avoid returning `False` for an `ErrorResponse`, because the view model cannot tell whether the operation failed because of a server error or because the boolean result was genuinely false.

### Rule 5: repositories should not manage UI state

A repository should not emit Qt signals, show message boxes, or decide which screen is visible.

The repository should only answer:

> Did the operation succeed, and what data came back?

## ViewModel rules

### Rule 1: one function per screen/app use case

The view model should expose functions that represent what the screen can ask for.

Example:

```python
async def load_channels(self):
    ...

async def create_channel(self, name: str, description: str):
    ...

async def join_channel(self, channel: Channel):
    ...
```

The screen should not need to know how these operations work internally.

### Rule 2: emit `LOADING` before async operations

For any operation that waits for the server, emit a loading state first.

```python
async def load_users(self):
    self.state_changed.emit(UserState.LOADING)
    result = await self.repository.get_users()
    ...
```

This lets the screen disable controls, show a loading page, or update a dialog.

### Rule 3: handle `Error` immediately

Every repository result that can return `Error` should be checked before the view model updates success state.

```python
result = await self.repository.get_users()

if isinstance(result, Error):
    self.error = result.message
    self.state_changed.emit(UserState.ERROR)
    return

self.users = result
self.state_changed.emit(UserState.USERS_LOADED)
```

This keeps the screen simple. The screen only has to listen for `UserState.ERROR` and display `view_model.error`.

### Rule 4: store state in fields the screen can render

The view model should keep the current data needed by the screen.

For example, a `MessagesViewModel` might keep:

```python
self.messages: list[Message] = []
self.selected_message: Message | None = None
self.selected_channel: Channel | None = None
self.error: str | None = None
```

A `UsersViewModel` might keep:

```python
self.users: list[User] = []
self.selected_user: User | None = None
self.user_details: UserDetailed | None = None
self.error: str | None = None
```

A `LoginViewModel` might keep:

```python
self.username: str | None = None
self.session_id: int | None = None
self.is_logged_in: bool = False
self.transport_mode: TransportMode = TransportMode.PLAINTEXT
self.error: str | None = None
```

### Rule 5: only emit finite states

The view model should not emit random strings such as:

```python
self.state_changed.emit("done")
```

Use enums:

```python
self.state_changed.emit(ChannelState.CHANNEL_CREATED)
```

This makes the screen predictable because it can match every possible state.

## Suggested contracts for remaining repositories

### UserRepository

```python
class UserRepository:
    def __init__(self, client: ChatProtocol):
        self._client = client

    async def get_users(self) -> list[User] | Error:
        ...

    async def get_user_details(self, user: User) -> UserDetailed | Error:
        ...
```

Possible view model:

```python
class UsersViewModel(QObject):
    state_changed = Signal(UserState)

    def __init__(self, repository: UserRepository):
        super().__init__()
        self.repository = repository
        self.users: list[User] = []
        self.selected_user: User | None = None
        self.user_details: UserDetailed | None = None
        self.error: str | None = None

    async def load_users(self):
        self.state_changed.emit(UserState.LOADING)
        result = await self.repository.get_users()

        if isinstance(result, Error):
            self.error = result.message
            self.state_changed.emit(UserState.ERROR)
            return

        self.users = result
        self.state_changed.emit(UserState.USERS_LOADED)
```

Suggested states:

```python
class UserState(Enum):
    IDLE = auto()
    LOADING = auto()
    USERS_LOADED = auto()
    USER_SELECTED = auto()
    USER_DETAILS_LOADED = auto()
    USERS_FILTERED = auto()
    ERROR = auto()
```

### MessageRepository

```python
class MessageRepository:
    def __init__(self, client: ChatProtocol):
        self._client = client

    async def get_messages(self, channel: Channel) -> list[Message] | Error:
        ...

    async def send_message(self, channel: Channel, content: str) -> Message | Error:
        ...
```

Possible view model:

```python
class MessagesViewModel(QObject):
    state_changed = Signal(MessageState)

    def __init__(self, repository: MessageRepository):
        super().__init__()
        self.repository = repository
        self.current_channel: Channel | None = None
        self.messages: list[Message] = []
        self.error: str | None = None

    async def load_messages(self, channel: Channel):
        self.state_changed.emit(MessageState.LOADING)
        self.current_channel = channel

        result = await self.repository.get_messages(channel)

        if isinstance(result, Error):
            self.error = result.message
            self.state_changed.emit(MessageState.ERROR)
            return

        self.messages = result
        self.state_changed.emit(MessageState.MESSAGES_LOADED)

    async def send_message(self, content: str):
        if self.current_channel is None:
            self.error = "No channel selected."
            self.state_changed.emit(MessageState.ERROR)
            return

        self.state_changed.emit(MessageState.SENDING)
        result = await self.repository.send_message(self.current_channel, content)

        if isinstance(result, Error):
            self.error = result.message
            self.state_changed.emit(MessageState.ERROR)
            return

        self.messages.append(result)
        self.state_changed.emit(MessageState.MESSAGE_SENT)
```

Suggested states:

```python
class MessageState(Enum):
    IDLE = auto()
    LOADING = auto()
    SENDING = auto()
    MESSAGES_LOADED = auto()
    MESSAGE_SENT = auto()
    MESSAGE_SELECTED = auto()
    ERROR = auto()
```

### AuthRepository and LoginViewModel

Login and transport selection deserve their own area because they affect the whole app.

Possible transport enum:

```python
class TransportMode(Enum):
    PLAINTEXT = auto()
    WIREGUARD = auto()
```

Possible repository:

```python
class AuthRepository:
    def __init__(self, client_factory: ChatClientFactory):
        self._client_factory = client_factory
        self._client: ChatProtocol | None = None

    async def configure_transport(self, mode: TransportMode) -> ChatProtocol | Error:
        ...

    async def login(self, username: str, password: str) -> Session | Error:
        ...

    async def logout(self) -> bool | Error:
        ...
```

Possible view model:

```python
class LoginViewModel(QObject):
    state_changed = Signal(LoginState)

    def __init__(self, repository: AuthRepository):
        super().__init__()
        self.repository = repository
        self.transport_mode = TransportMode.PLAINTEXT
        self.session: Session | None = None
        self.error: str | None = None

    async def select_transport(self, mode: TransportMode):
        self.state_changed.emit(LoginState.CONFIGURING_TRANSPORT)
        result = await self.repository.configure_transport(mode)

        if isinstance(result, Error):
            self.error = result.message
            self.state_changed.emit(LoginState.ERROR)
            return

        self.transport_mode = mode
        self.state_changed.emit(LoginState.TRANSPORT_CONFIGURED)

    async def login(self, username: str, password: str):
        self.state_changed.emit(LoginState.LOGGING_IN)
        result = await self.repository.login(username, password)

        if isinstance(result, Error):
            self.error = result.message
            self.state_changed.emit(LoginState.ERROR)
            return

        self.session = result
        self.state_changed.emit(LoginState.LOGGED_IN)
```

Suggested states:

```python
class LoginState(Enum):
    IDLE = auto()
    CONFIGURING_TRANSPORT = auto()
    TRANSPORT_CONFIGURED = auto()
    LOGGING_IN = auto()
    LOGGED_IN = auto()
    LOGGING_OUT = auto()
    LOGGED_OUT = auto()
    ERROR = auto()
```

## App-wide ViewModel

The app-wide view model should coordinate high-level application state. It should not replace the feature view models.

It may track:

- whether the app is connected,
- whether the user is logged in,
- the current transport mode,
- the current screen/page,
- the active session,
- global errors,
- references to feature view models.

Possible states:

```python
class AppState(Enum):
    STARTING = auto()
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    AUTHENTICATED = auto()
    SHOW_LOGIN = auto()
    SHOW_MAIN_APP = auto()
    ERROR = auto()
```

Possible responsibility split:

```text
AppViewModel
    owns app-wide state and current page

LoginViewModel
    owns login form, login state, and transport selection

ChannelsViewModel
    owns channel list and selected channel

MessagesViewModel
    owns messages for the selected channel

UsersViewModel
    owns user list and user details
```
