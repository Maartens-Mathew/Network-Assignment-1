import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Import the directory where LoginView lives to use it as a direct tag
import "../features/auth/view"

ApplicationWindow {
    id: windowRoot
    visible: true
    width: 1100
    height: 700
    title: "PySide6 Chat Client"

    StackLayout {
        id: rootStack
        anchors.fill: parent
        currentIndex: 0

        // Look how clean this is now! No Loaders required.
        LoginView {
            id: loginView
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        MainAppWindow {
            id: mainAppWindow
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    Connections {
        target: loginViewModel
        function onLogin_succeeded() {
            rootStack.currentIndex = 1
            appInitializer.initialize_authenticated_session()
        }
    }
}