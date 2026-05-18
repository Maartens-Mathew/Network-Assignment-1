// features/users/view/UserScreen.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property var usersViewModel
    Layout.fillWidth: true
    Layout.fillHeight: true

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            color: "#2c3e50"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 8

                Label {
                    text: "Users"
                    font.pixelSize: 15
                    font.bold: true
                    color: "#ffffff"
                }

                ListView {
                    id: usersListView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: root.usersViewModel ? root.usersViewModel.users : []
                    clip: true

                    delegate: ItemDelegate {
                        width: usersListView.width
                        height: 40

                        contentItem: RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4

                            Label { text: "@" + modelData.username; color: "#ffffff" }
                        }

                        onClicked: {
                            usersViewModel.select_user(modelData)
                        }
                    }
                }
            }
        }

        // Right-side chat area for DMs
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8
            anchors.margins: 12

            Label {
                text: root.usersViewModel && root.usersViewModel.selected_user ? "@" + root.usersViewModel.selected_user.username : "Select a user"
                font.pixelSize: 18
                font.bold: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#f4f6f7"
                border.color: "#bdc3c7"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8

                    ListView {
                        id: dmListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: root.usersViewModel ? root.usersViewModel.messages : []
                        delegate: Label { text: modelData.content; wrapMode: Text.WordWrap }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        TextField { id: dmInput; Layout.fillWidth: true }
                        Button {
                            text: "Send"
                            onClicked: {
                                root.usersViewModel.send_message(dmInput.text)
                                dmInput.text = ""
                            }
                        }
                    }
                }
            }
        }
    }
}
