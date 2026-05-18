// features/channels/view/ChannelNewDialog.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: dialog
    title: "Create New Channel"
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    width: 380
    height: 180
    anchors.centerIn: parent

    property alias channelName: channelNameInput.text
    property alias channelDescription: channelDescriptionInput.text

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10

        TextField {
            id: channelNameInput
            placeholderText: "Channel Name"
            Layout.fillWidth: true
        }

        TextField {
            id: channelDescriptionInput
            placeholderText: "Description"
            Layout.fillWidth: true
        }
    }

    onAccepted: {
        dialog.channelName = channelNameInput.text
        dialog.channelDescription = channelDescriptionInput.text
    }

    onVisibleChanged: {
        if (visible && parent) {
            x = parent.width / 2 - width / 2
            y = parent.height / 2 - height / 2
        }
    }
}
