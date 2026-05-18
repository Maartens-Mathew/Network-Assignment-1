import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Import your feature view folders
import "../features/channels/view"
import "../features/users/view"

Item {
    id: mainAppWorkspace
    Layout.fillWidth: true
    Layout.fillHeight: true

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ... (Sidebar layout remains the same) ...

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            StackLayout {
                id: workspaceStack
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: appViewModel.currentSection

                // Declared directly as clean, readable component elements
                ChannelScreen {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    channelsViewModel: channelsViewModel
                }
                UserScreen {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    usersViewModel: usersViewModel
                }
            }
        }
    }
}