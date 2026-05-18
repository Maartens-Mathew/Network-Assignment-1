// features/channels/view/ChannelScreen.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property var channelsViewModel
    Layout.fillWidth: true
    Layout.fillHeight: true

    RowLayout {
        anchors.fill: parent
        spacing: 0

        ChannelListPanel {
            id: channelListPanel
            Layout.preferredWidth: 280
            Layout.maximumWidth: 320
            Layout.fillHeight: true
            channelsViewModel: root.channelsViewModel
            onChannelSelected: root.channelsViewModel && root.channelsViewModel.select_channel(channel)
            onChannelInfoRequested: {
                channelInfoDialog.channel = channel
                channelInfoDialog.open()
            }
            onNewChannelRequested: {
                newChannelDialog.open()
            }
        }

        StackLayout {
            id: contentStack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.channelsViewModel ? root.channelsViewModel.statePage : 0

            Item {
                Label {
                    text: "Loading…"
                    anchors.centerIn: parent
                    color: "#95a6a6"
                    font.pixelSize: 15
                }
            }

            Item {
                Label {
                    text: root.channelsViewModel && root.channelsViewModel.channels.length === 0
                        ? "No channels yet. Create one to get started."
                        : "Select a channel to start chatting"
                    anchors.centerIn: parent
                    color: "#4a6278"
                    font.pixelSize: 14
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }

            ChannelChatPanel {
                channelsViewModel: root.channelsViewModel
            }
        }
    }

    ChannelNewDialog {
        id: newChannelDialog
        onAccepted: {
            if (root.channelsViewModel) {
                root.channelsViewModel.create_channel(channelName, channelDescription)
            }
            channelName = ""
            channelDescription = ""
        }
    }

    ChannelInfoDialog {
        id: channelInfoDialog
    }
}
