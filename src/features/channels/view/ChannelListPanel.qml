// features/channels/view/ChannelListPanel.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property var channelsViewModel
    signal channelSelected(var channel)
    signal channelInfoRequested(var channel)
    signal newChannelRequested()

    Layout.fillHeight: true

    Rectangle {
        anchors.fill: parent
        color: "#1e1e24"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 8

            Label {
                text: "Channels"
                font.pixelSize: 18
                font.bold: true
                color: "#ffffff"
                Layout.fillWidth: true
            }

            ListView {
                id: channelListView
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                model: root.channelsViewModel ? root.channelsViewModel.channelModel : null
                spacing: 2

                delegate: ItemDelegate {
                    width: channelListView.width
                    height: 44
                    hoverEnabled: true
                    // Changed modelData.name to model.name (or simply: name)
                    highlighted: root.channelsViewModel && root.channelsViewModel.selectedChannel && root.channelsViewModel.selectedChannel.name === model.name

                    contentItem: RowLayout {
                        anchors.fill: parent
                        anchors.margins: 4
                        spacing: 8

                        Label {
                            text: "# " + model.name // Changed here
                            color: "#ffffff"
                            Layout.fillWidth: true
                        }

                        Button {
                            text: "i"
                            Layout.preferredWidth: 26
                            // Pass a constructed anonymous object back to python if needed, or pass the index
                            onClicked: root.channelInfoRequested({"name": model.name}) 
                        }
                    }

                    onClicked: root.channelSelected({"name": model.name})
                }
            }

            Button {
                text: "＋  New Channel"
                Layout.fillWidth: true
                onClicked: root.newChannelRequested()
            }
        }
    }
}
