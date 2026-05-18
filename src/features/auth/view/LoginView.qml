// ui/LoginView.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: loginScreenRoot
    Layout.fillWidth: true
    Layout.fillHeight: true

    Rectangle {
        anchors.fill: parent
        color: "#f5f6fa"
    }

    Rectangle {
        id: loginCard
        width: 380
        height: 340
        radius: 8
        color: "#ffffff"
        anchors.centerIn: parent

        border.color: "#dcdde1"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 14

            Label {
                text: "Chat Client Login"
                font.pixelSize: 20
                font.bold: true
                color: "#2f3640"
                Layout.alignment: Qt.AlignHCenter
                Layout.bottomMargin: 10
            }

            TextField {
                id: usernameField
                placeholderText: "Username"
                text: "Mathew"
                Layout.fillWidth: true
                onTextChanged: loginViewModel.username = text
            }

            TextField {
                id: publicKeyField
                placeholderText: "Public Key"
                text: "ZixewENi85M3vxEUIu0TC5/nrzuUsHAT4ZTdhc8BC0M="
                Layout.fillWidth: true
                onTextChanged: loginViewModel.public_key = text
            }

            TextField {
                id: privateKeyField
                placeholderText: "Private Key"
                echoMode: TextField.Password
                Layout.fillWidth: true
                onTextChanged: loginViewModel.private_key = text
            }

            Button {
                text: loginViewModel.isLoading ? "Logging in..." : "Login"
                Layout.fillWidth: true
                Layout.topMargin: 10

                onClicked: {
                    loginViewModel.username = usernameField.text
                    loginViewModel.public_key = publicKeyField.text
                    loginViewModel.private_key = privateKeyField.text
                    loginViewModel.login() // Triggers the authentication slot in Python
                }
            }
        }
    }

    Dialog {
        id: failureDialog
        title: "Login Failed"
        anchors.centerIn: parent
        modal: true
        standardButtons: Dialog.Ok
        property alias text: failureLabel.text

        Label { id: failureLabel }
    }

    Connections {
        target: loginViewModel
        function onLogin_failed(reason) {
            failureDialog.text = reason
            failureDialog.open()
        }
    }
}