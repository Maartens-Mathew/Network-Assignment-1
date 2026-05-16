APP_STYLESHEET = """
QMainWindow {
    background-color: #f4f4f4;
}

QWidget {
    font-family: Segoe UI;
    font-size: 14px;
}

#LoginCard {
    background-color: white;
    border: 1px solid #d5d5d5;
    border-radius: 8px;
    min-width: 340px;
    max-width: 340px;
    padding: 20px;
}

#LoginTitle {
    font-size: 24px;
    font-weight: bold;
    color: #222222;
}

QLineEdit {
    padding: 9px;
    border: 1px solid #bdbdbd;
    border-radius: 5px;
    background-color: white;
}

QLineEdit:focus {
    border: 1px solid #4a90e2;
}

QPushButton {
    padding: 9px 14px;
    border-radius: 5px;
    border: 1px solid #999999;
    background-color: #ffffff;
}

QPushButton:hover {
    background-color: #eeeeee;
}

#NavBar {
    background-color: #2f343a;
    min-width: 120px;
    max-width: 120px;
}

#NavButton {
    color: white;
    background-color: #3b4148;
    border: none;
    padding: 12px;
    text-align: left;
}

#NavButton:hover {
    background-color: #505861;
}

#TopBar {
    background-color: white;
    border-bottom: 1px solid #dddddd;
    min-height: 52px;
    max-height: 52px;
}

#SettingsButton {
    background-color: #ffffff;
    border: 1px solid #cccccc;
}

#SideList {
    background-color: white;
    border: 1px solid #dddddd;
    padding: 4px;
}

QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #eeeeee;
}

QListWidget::item:selected {
    background-color: #dcecff;
    color: #222222;
}

#ChatTitle {
    font-size: 22px;
    font-weight: bold;
    color: #222222;
    padding: 8px;
}

QTextEdit {
    background-color: white;
    border: 1px solid #dddddd;
    border-radius: 5px;
    padding: 10px;
}
"""