import asyncio
import sys

from dependency_injector import providers
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from di.container import Container


def main():
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    container = Container()
    container.config.server.host.from_value("csc4026z.link")
    container.config.server.port.from_value(51825)

    with loop:
        chat_protocol = loop.run_until_complete(container.create_chat_protocol())
        container.chat_protocol.override(providers.Object(chat_protocol))

        window = container.root_window()
        window.show()

        loop.run_forever()


if __name__ == "__main__":
    main()
