// features/channels/view/ChannelInfoDialog.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: infoDialog
    title: "Channel Info"
    modal: true
    standardButtons: Dialog.Close

    property var channel

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10

        Label {
            text: channel ? "# " + channel.name : "No channel selected"
            font.pixelSize: 18
            font.bold: true
        }

        Label {
            text: channel && channel.description ? channel.description : "No description provided."
            wrapMode: Text.WordWrap
            color: "#4a6278"
        }
    }
}
