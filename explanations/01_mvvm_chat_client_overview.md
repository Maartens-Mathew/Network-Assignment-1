# MVVM Overview for the Chat Client

## Purpose of this guide

This project is roughly following an MVVM-style structure:

```text
Screen / View  ->  ViewModel  ->  Repository  ->  ChatProtocol  ->  Server
```

Each layer has a different responsibility. The goal is to keep the UI simple, keep business logic out of the widgets, and make each section of the chat client easier to extend.

The current `Channel` implementation is the best reference point. The channel feature already has:

- a repository for sending channel-related protocol requests,
- a view model for storing channel UI state,
- a screen for rendering the channel UI,
- a finite set of states that the screen responds to.

The remaining sections should follow the same pattern:

- users,
- messages,
- login/session management,
- app-wide state,
- transport mode selection, such as plaintext versus WireGuard-backed communication.

## The main rule

Each entity or section of the application should expose a finite number of use cases.

A use case is one thing the user or app needs to do. For example, for channels:

- load channels,
- select a channel,
- create a channel,
- join a channel,
- leave a channel,
- get channel details.

The repository and view model should both expose functions that correspond to those use cases.

The repository knows how to talk to the protocol. The view model knows how to turn repository results into UI state. The screen knows how to render that state.

## Suggested folder structure

```text
src/
  core/
    requests/
    responses/
  infrastructure/
    chat_protocol.py
    transport/
      plaintext_transport.py
      wireguard_transport.py
  models/
    channel.py
    user.py
    message.py
    error.py
  repositories/
    channel_repository.py
    user_repository.py
    message_repository.py
    auth_repository.py
  state/
    channel_state.py
    user_state.py
    message_state.py
    login_state.py
    app_state.py
  viewmodels/
    channel_viewmodel.py
    user_viewmodel.py
    message_viewmodel.py
    login_viewmodel.py
    app_viewmodel.py
  views/
    channel_screen/
    user_screen/
    message_screen/
    login_screen/
    root_window.py
```

This structure is not mandatory, but the important thing is that each feature follows the same direction of dependency:

```text
View depends on ViewModel
ViewModel depends on Repository
Repository depends on ChatProtocol
ChatProtocol depends on transport/socket details
```

Avoid reversing this direction. For example, repositories should not import screens, and protocol classes should not know about Qt widgets.

## What each layer should do

### Repository

The repository is responsible for protocol-level communication.

It should:

- create the correct request object,
- call `ChatProtocol.send_request(...)`,
- inspect the response,
- convert protocol responses into app models,
- convert `ErrorResponse` into the app-level `Error` model.

It should not:

- show message boxes,
- update Qt widgets,
- emit UI signals,
- decide what page the user should see.

Example idea:

```python
async def get_channels(self) -> list[Channel] | Error:
    response: ListChannelsResponse | ErrorResponse = await self._client.send_request(
        ListChannelsRequest()
    )

    if isinstance(response, ErrorResponse):
        return Error(response.message)

    return [Channel(channel) for channel in response.channels]
```

The repository should return either the successful result or an `Error`.

### ViewModel

The view model is responsible for UI-facing state and use-case orchestration.

It should:

- expose one async function per use case,
- call the repository,
- store successful results in fields used by the screen,
- store error messages in a field such as `self.error`,
- emit a finite state through `Signal(...)`.

It should not:

- create protocol request objects directly,
- directly manipulate Qt widgets,
- contain layout or styling code,
- show dialogs or message boxes.

Example idea:

```python
async def create_channel(self, name: str, description: str):
    self.state_changed.emit(ChannelState.LOADING)

    result = await self.repository.create_channel(
        ChannelDetailed(name=name, description=description)
    )

    if isinstance(result, Error):
        self.error = result.message
        self.state_changed.emit(ChannelState.ERROR)
        return

    self.channels.append(Channel(name=result.name))
    self.state_changed.emit(ChannelState.CHANNEL_CREATED)
```

### Screen / View

The screen is responsible for Qt widgets and rendering.

It should:

- build the UI,
- connect button clicks and item clicks to view model functions,
- listen to `state_changed`,
- render the correct page or widget state based on the enum state,
- show errors in a user-friendly way.

It should not:

- call `ChatProtocol` directly,
- create request objects,
- inspect raw protocol responses,
- contain business rules that belong in the view model.

Example idea:

```python
def _on_state_changed(self, state: ChannelState) -> None:
    match state:
        case ChannelState.LOADING:
            self._show_loading()
        case ChannelState.CHANNELS_LOADED:
            self._render_channels()
            self._show_empty_for_current_channels()
        case ChannelState.ERROR:
            self._show_error(self.view_model.error or "Unknown error")
```

## Why finite states matter

The screens should not be coded as a collection of random UI updates. Instead, each screen should respond to a finite set of states.

For example, a channel screen might have:

```python
class ChannelState(Enum):
    IDLE = auto()
    LOADING = auto()
    CHANNELS_LOADED = auto()
    CHANNEL_SELECTED = auto()
    CHANNEL_CREATED = auto()
    CHANNEL_JOINED = auto()
    CHANNEL_LEFT = auto()
    CHANNEL_INFO_LOADED = auto()
    MESSAGES_LOADED = auto()
    ERROR = auto()
```

The view model emits one of these states:

```python
state_changed = Signal(ChannelState)
```

The screen then uses `match state:` to decide how to update itself.

This gives the UI consistency. The screen is always in one known state, rather than half-loading, half-error, or half-rendered.

## Finite operations per section

Each section should begin with a small table of use cases before anyone writes code.

### Channels

| Use case | Repository function | ViewModel function | Success state | Error state |
|---|---|---|---|---|
| List channels | `get_channels()` | `load_channels()` | `CHANNELS_LOADED` | `ERROR` |
| Select channel | none or local only | `select_channel(channel)` | `CHANNEL_SELECTED` | optional |
| Create channel | `create_channel(channel)` | `create_channel(name, description)` | `CHANNEL_CREATED` | `ERROR` |
| Join channel | `join_channel(channel)` | `join_channel(channel)` | `CHANNEL_JOINED` | `ERROR` |
| Leave channel | `leave_channel(channel)` | `leave_channel(channel)` | `CHANNEL_LEFT` | `ERROR` |
| Get details | `get_channel_details(channel)` | `get_channel_info(channel)` | `CHANNEL_INFO_LOADED` | `ERROR` |

### Users

Possible operations:

| Use case | Repository function | ViewModel function | Success state | Error state |
|---|---|---|---|---|
| List users | `get_users()` | `load_users()` | `USERS_LOADED` | `ERROR` |
| Get user details | `get_user_details(user)` | `load_user_details(user)` | `USER_DETAILS_LOADED` | `ERROR` |
| Search/filter users locally | none or local only | `filter_users(query)` | `USERS_FILTERED` | optional |
| Select user | none or local only | `select_user(user)` | `USER_SELECTED` | optional |

### Messages

Possible operations:

| Use case | Repository function | ViewModel function | Success state | Error state |
|---|---|---|---|---|
| Load channel messages | `get_messages(channel)` | `load_messages(channel)` | `MESSAGES_LOADED` | `ERROR` |
| Send message | `send_message(channel, content)` | `send_message(content)` | `MESSAGE_SENT` | `ERROR` |
| Receive or refresh messages | `get_messages(channel)` | `refresh_messages()` | `MESSAGES_LOADED` | `ERROR` |
| Select message | none or local only | `select_message(message)` | `MESSAGE_SELECTED` | optional |

### Login and transport mode

Possible operations:

| Use case | Repository function | ViewModel function | Success state | Error state |
|---|---|---|---|---|
| Login | `login(username, password)` | `login(username, password)` | `LOGGED_IN` | `ERROR` |
| Logout | `logout()` | `logout()` | `LOGGED_OUT` | `ERROR` |
| Select plaintext transport | configuration-level operation | `select_plaintext_mode()` | `TRANSPORT_SELECTED` | `ERROR` |
| Select WireGuard transport | configuration-level operation | `select_wireguard_mode()` | `TRANSPORT_SELECTED` | `ERROR` |
| Connect session | `connect()` | `connect()` | `CONNECTED` | `ERROR` |

The transport selection should probably live above the normal entity repositories, because users, channels, and messages should not care whether communication is plaintext or WireGuard-backed. They should only depend on a working `ChatProtocol` or client abstraction.

## Recommended development process

For each new feature, follow this order:

1. Define the model.
2. Define the request and response classes.
3. Define the repository functions.
4. Define the state enum.
5. Define the view model fields and functions.
6. Define the screen rendering for each state.
7. Connect the screen slots to the view model.
8. Test both success and error responses.

Do not start with the screen. The screen should be the final layer that reflects already-defined use cases and states.

## Key team convention

Every use case should answer these questions:

1. What function does the repository expose?
2. What successful model does it return?
3. What error type does it return?
4. What function does the view model expose?
5. What fields does the view model update?
6. What state does the view model emit on success?
7. What state does the view model emit on failure?
8. How does the screen render each state?

If a teammate cannot answer those questions, the feature is not designed clearly enough yet.
