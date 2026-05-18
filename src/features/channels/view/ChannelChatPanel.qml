// features/channels/view/ChannelChatPanel.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property var channelsViewModel
    Layout.fillWidth: true
    Layout.fillHeight: true

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            text: root.channelsViewModel && root.channelsViewModel.selectedChannel ? "# " + root.channelsViewModel.selectedChannel.name : "No channel selected"
            font.pixelSize: 22
            font.bold: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#f4f6f7"
            border.color: "#bdc3c7"
            radius: 8

            Label {
                anchors.centerIn: parent
                text: root.channelsViewModel && root.channelsViewModel.selectedChannel ? "Chat messages will appear here." : "Select a channel to start chatting."
                color: "#7f8c8d"
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                width: parent.width * 0.8
            }
        }
    }
}
