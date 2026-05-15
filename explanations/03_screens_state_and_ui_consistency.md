# Screens, Signals, and UI State Consistency

## Purpose

This guide explains how the View layer should work in the chat client.

In this project, screens are PySide6 widgets. A screen should build UI components, forward user actions to the view model, and render view model state.

The important rule is:

> The screen should not decide business logic. It should react to a finite set of states emitted by the view model.

The current `ChannelScreen` is the main example.

## Screen responsibilities

A screen should:

- build widgets,
- connect Qt signals to slots,
- call view model functions when the user does something,
- listen to `view_model.state_changed`,
- render the correct UI for each enum state,
- show user-friendly errors.

A screen should not:

- call `ChatProtocol` directly,
- create request or response objects,
- inspect raw server responses,
- decide how protocol errors work,
- contain repository logic.

## Basic screen structure

A clean screen usually has these sections:

```python
class SomeScreen(QWidget):
    def __init__(self, view_model: SomeViewModel):
        super().__init__()
        self.view_model = view_model

        self._build_ui()
        self._connect_signals()
        self._show_initial_state()

    def _build_ui(self) -> None:
        ...

    def _connect_signals(self) -> None:
        ...

    def _on_state_changed(self, state: SomeState) -> None:
        ...
```

This keeps UI construction, signal wiring, and state rendering separate.

## User actions should call the ViewModel

When the user clicks something, the screen should call the view model.

Example:

```python
@asyncSlot(Channel)
async def _on_join_clicked(self, channel: Channel) -> None:
    await self.view_model.join_channel(channel)
```

The screen does not know how joining works. It only forwards the intent.

The flow is:

```text
User clicks Join
    -> Screen calls view_model.join_channel(channel)
    -> ViewModel calls repository.join_channel(channel)
    -> Repository sends request through ChatProtocol
    -> ViewModel updates state
    -> Screen reacts to emitted state
```

## ViewModels emit enum states through `Signal(...)`

The view model should declare a typed signal:

```python
state_changed = Signal(ChannelState)
```

Then it emits states:

```python
self.state_changed.emit(ChannelState.LOADING)
self.state_changed.emit(ChannelState.CHANNEL_JOINED)
self.state_changed.emit(ChannelState.ERROR)
```

The screen connects to it:

```python
self.view_model.state_changed.connect(self._on_state_changed)
```

Then the screen renders the state:

```python
def _on_state_changed(self, state: ChannelState) -> None:
    match state:
        case ChannelState.LOADING:
            self._show_loading()

        case ChannelState.CHANNELS_LOADED:
            self._render_channels()
            self._show_empty_for_current_channels()

        case ChannelState.CHANNEL_SELECTED:
            self._render_selected_channel()
            self._show_chat()

        case ChannelState.ERROR:
            self._show_error(self.view_model.error or "Unknown error")
```

## Why enum states are useful

Enums force the UI into a finite number of known states.

This prevents messy UI bugs where:

- a loading indicator is still visible after success,
- buttons remain disabled after an error,
- stale data remains on screen,
- a dialog stays open after successful creation,
- a user can send a message before selecting a channel.

Instead, the screen asks:

> Which state did the view model emit, and how should the screen look in that state?

## Example: channel screen state rendering

The channel screen can be understood as a state machine.

| State | What the screen should do |
|---|---|
| `LOADING` | Disable controls and show loading UI. |
| `CHANNELS_LOADED` | Render the list of channels. |
| `CHANNEL_SELECTED` | Update selected channel and show chat panel. |
| `CHANNEL_CREATED` | Re-render channels, close create dialog, show empty/chat state. |
| `CHANNEL_JOINED` | Re-render channels. |
| `CHANNEL_LEFT` | Re-render channels and clear chat if needed. |
| `CHANNEL_INFO_LOADED` | Show channel info dialog. |
| `MESSAGES_LOADED` | Render messages and show chat. |
| `ERROR` | Restore controls and show the error. |

This is much safer than letting every button click manually edit the UI in a different way.

## Screens should render ViewModel fields

The screen should read data from the view model and render it.

Example:

```python
def _render_channels(self) -> None:
    self.channel_list.clear()

    for channel in self.view_model.channels:
        ...
```

The screen should not fetch the data itself.

The view model owns the screen data:

```python
self.channels: list[Channel] = []
self.selected_channel: Channel | None = None
self.channel_info: ChannelDetailed | None = None
self.error: str | None = None
```

The screen only displays it.

## Suggested screen pattern for users

A `UserScreen` could follow the same structure:

```python
class UserScreen(QWidget):
    def __init__(self, view_model: UsersViewModel):
        super().__init__()
        self.view_model = view_model
        self._build_ui()
        self._connect_signals()
        self._show_empty("Load users to begin.")

    def _connect_signals(self) -> None:
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.user_list.itemClicked.connect(self._on_user_clicked)
        self.view_model.state_changed.connect(self._on_state_changed)

    def _on_state_changed(self, state: UserState) -> None:
        match state:
            case UserState.LOADING:
                self._show_loading()
            case UserState.USERS_LOADED:
                self._render_users()
                self._show_users()
            case UserState.USER_SELECTED:
                self._render_selected_user()
            case UserState.USER_DETAILS_LOADED:
                self._show_user_details()
            case UserState.ERROR:
                self._show_error(self.view_model.error or "Unknown error")
```

Possible user states:

```python
class UserState(Enum):
    IDLE = auto()
    LOADING = auto()
    USERS_LOADED = auto()
    USER_SELECTED = auto()
    USER_DETAILS_LOADED = auto()
    ERROR = auto()
```

## Suggested screen pattern for messages

Messages will probably be closely connected to channels. A `MessagesViewModel` can own message loading and sending, while the channel screen or chat panel renders the messages.

The current channel screen already has a placeholder for messages:

```python
def _render_messages(self) -> None:
    # Once available:
    #     self.chat_panel.set_messages(self.view_model.messages)
    pass
```

A future version could either:

1. keep messages inside `ChannelsViewModel`, or
2. create a dedicated `MessagesViewModel` and inject it into the chat panel or channel screen.

The second approach is cleaner if messages become complex.

Possible message state rendering:

```python
def _on_message_state_changed(self, state: MessageState) -> None:
    match state:
        case MessageState.LOADING:
            self.chat_panel.set_loading(True)
        case MessageState.MESSAGES_LOADED:
            self.chat_panel.set_loading(False)
            self.chat_panel.set_messages(self.messages_view_model.messages)
        case MessageState.SENDING:
            self.chat_panel.set_send_enabled(False)
        case MessageState.MESSAGE_SENT:
            self.chat_panel.set_send_enabled(True)
            self.chat_panel.set_messages(self.messages_view_model.messages)
            self.chat_panel.clear_input()
        case MessageState.ERROR:
            self.chat_panel.set_send_enabled(True)
            self._show_error(self.messages_view_model.error or "Unknown message error")
```

## Suggested screen pattern for login and transport selection

The login screen may need to support both plaintext communication and WireGuard communication.

This should still be state-driven.

Possible login states:

```python
class LoginState(Enum):
    IDLE = auto()
    CONFIGURING_TRANSPORT = auto()
    TRANSPORT_CONFIGURED = auto()
    LOGGING_IN = auto()
    LOGGED_IN = auto()
    ERROR = auto()
```

Possible screen rendering:

```python
def _on_state_changed(self, state: LoginState) -> None:
    match state:
        case LoginState.CONFIGURING_TRANSPORT:
            self._disable_form()
            self._show_status("Configuring transport...")

        case LoginState.TRANSPORT_CONFIGURED:
            self._enable_form()
            self._show_status("Transport configured.")

        case LoginState.LOGGING_IN:
            self._disable_form()
            self._show_status("Logging in...")

        case LoginState.LOGGED_IN:
            self._enable_form()
            self.login_successful.emit()

        case LoginState.ERROR:
            self._enable_form()
            self._show_error(self.view_model.error or "Login failed")
```

The login screen should not know the technical details of WireGuard setup. It should only allow the user to select the transport mode and then ask the view model to configure it.

## App-wide screen and root window

The root window or app shell should also be state-driven.

It may need to switch between:

- login screen,
- main chat screen,
- loading/connecting screen,
- disconnected/error screen.

Possible app state:

```python
class AppState(Enum):
    STARTING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    AUTHENTICATED = auto()
    SHOW_LOGIN = auto()
    SHOW_MAIN_APP = auto()
    DISCONNECTED = auto()
    ERROR = auto()
```

Possible root rendering:

```python
def _on_app_state_changed(self, state: AppState) -> None:
    match state:
        case AppState.SHOW_LOGIN:
            self.stack.setCurrentWidget(self.login_screen)

        case AppState.SHOW_MAIN_APP:
            self.stack.setCurrentWidget(self.main_screen)

        case AppState.CONNECTING:
            self.stack.setCurrentWidget(self.loading_screen)

        case AppState.ERROR:
            self._show_error(self.app_view_model.error or "Application error")
```

The root window should coordinate screens, but it should not take over the logic belonging to each feature.

## UI consistency checklist

For every screen, check the following:

- Does the screen receive a view model in its constructor?
- Does the screen connect to `view_model.state_changed`?
- Does the screen use `match state:` or equivalent finite state handling?
- Does every async user action call a view model function?
- Does the screen avoid calling repositories directly?
- Does the screen avoid creating request/response objects?
- Does the screen restore controls after success and error?
- Does the screen show useful errors from `view_model.error`?
- Does the screen render from view model fields rather than owning duplicate data?
- Does the screen have a known empty/loading/error state?

## Common mistakes to avoid

### Mistake 1: putting protocol logic in the screen

Bad:

```python
async def _on_send_clicked(self):
    response = await self.client.send_request(SendMessageRequest(...))
```

Good:

```python
async def _on_send_clicked(self, content: str):
    await self.view_model.send_message(content)
```

### Mistake 2: updating the UI before the view model confirms success

Bad:

```python
self.channel_list.addItem(channel.name)
await self.view_model.create_channel(channel.name, description)
```

Good:

```python
await self.view_model.create_channel(channel.name, description)
# Then wait for CHANNEL_CREATED and re-render from view_model.channels.
```

### Mistake 3: not having an error state

Bad:

```python
if isinstance(result, Error):
    print(result.message)
```

Good:

```python
if isinstance(result, Error):
    self.error = result.message
    self.state_changed.emit(ChannelState.ERROR)
    return
```

### Mistake 4: too many hidden UI states

Bad:

```python
self.loading = True
self.has_error = False
self.dialog_open = True
self.button_disabled = True
```

This can easily create inconsistent combinations.

Good:

```python
self.state_changed.emit(ChannelState.LOADING)
self.state_changed.emit(ChannelState.CHANNEL_CREATED)
self.state_changed.emit(ChannelState.ERROR)
```

Then the screen decides the correct UI for each state.

## Final rule for screens

A screen should be boring, code-wise (not UI/UX-wise).

That is a good thing.

It should mostly contain:

- widget construction,
- signal connections,
- small slot functions,
- render functions,
- state handling.

The interesting decisions should live in the view model and repository contracts, not scattered throughout the UI.
