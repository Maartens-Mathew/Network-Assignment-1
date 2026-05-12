import sys

from PySide6.QtWidgets import QApplication


def main() -> None:
    app = QApplication(sys.argv)

   # Set style of application
   # app.setStyleSheet(APP_STYLE)

    # define view models that live for lifetime of program
    # view_model = TaskViewModel()

    app = App()
    # entry point for first window
    # window = MainWindow(view_model)

    # window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()