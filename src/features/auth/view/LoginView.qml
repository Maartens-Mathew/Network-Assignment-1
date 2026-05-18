// ui/LoginView.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: loginScreenRoot
    Layout.fillWidth: true
    Layout.fillHeight: true

    // ─── Palette ──────────────────────────────────────────────────────
    readonly property color bg:         "#0D0F14"
    readonly property color bgAlt:      "#111520"
    readonly property color cardBg:     "#131720"
    readonly property color fieldBg:    "#161C2C"
    readonly property color fieldFocus: "#1A2133"
    readonly property color borderSub:  "#1E2738"
    readonly property color borderFoc:  "#5B8DEF"
    readonly property color accent:     "#5B8DEF"
    readonly property color accentHov:  "#6B9EFF"
    readonly property color accentPrs:  "#4A7ADE"
    readonly property color textPri:    "#E8ECF4"
    readonly property color textSec:    "#6B7A99"
    readonly property color danger:     "#E05B5B"

    // ─── Background ───────────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: loginScreenRoot.bg }
            GradientStop { position: 1.0; color: loginScreenRoot.bgAlt }
        }
    }

    // ─── Login Card ───────────────────────────────────────────────────
    Rectangle {
        id: loginCard
        width: 420
        anchors.centerIn: parent
        height: cardLayout.implicitHeight + 72
        radius: 4
        color: loginScreenRoot.cardBg
        border.color: loginScreenRoot.borderSub
        border.width: 1

        opacity: 0
        NumberAnimation on opacity {
            from: 0; to: 1
            duration: 500
            easing.type: Easing.OutCubic
            running: true
        }

        property real slideOffset: 16
        anchors.verticalCenterOffset: slideOffset
        NumberAnimation on slideOffset {
            from: 16; to: 0
            duration: 500
            easing.type: Easing.OutCubic
            running: true
        }

        ColumnLayout {
            id: cardLayout
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
                topMargin: 36
                leftMargin: 36
                rightMargin: 36
            }
            spacing: 0

            // ── Header ──────────────────────────────────────────────
            Column {
                Layout.fillWidth: true
                Layout.bottomMargin: 34
                spacing: 8

                Label {
                    text: "CHAT CLIENT"
                    font.pixelSize: 9
                    font.letterSpacing: 3.5
                    font.family: "Courier New"
                    font.weight: Font.Medium
                    color: loginScreenRoot.accent
                }
                Label {
                    text: "Sign In"
                    font.pixelSize: 26
                    font.weight: Font.Light
                    color: loginScreenRoot.textPri
                }
            }

            // ── Username ─────────────────────────────────────────────
            Column {
                Layout.fillWidth: true
                Layout.bottomMargin: 20
                spacing: 8

                Label {
                    text: "USERNAME"
                    font.pixelSize: 9
                    font.letterSpacing: 2
                    font.family: "Courier New"
                    color: loginScreenRoot.textSec
                }
                Rectangle {
                    width: parent.width; height: 40
                    radius: 3
                    color: usernameField.activeFocus
                        ? loginScreenRoot.fieldFocus
                        : loginScreenRoot.fieldBg
                    border.color: usernameField.activeFocus
                        ? loginScreenRoot.borderFoc
                        : loginScreenRoot.borderSub
                    border.width: 1
                    Behavior on color      { ColorAnimation { duration: 150 } }
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    TextField {
                        id: usernameField
                        anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
                        text: "Mathew"
                        placeholderText: "Enter your username"
                        color: loginScreenRoot.textPri
                        placeholderTextColor: loginScreenRoot.textSec
                        font.pixelSize: 13
                        selectionColor: loginScreenRoot.accent
                        background: Item {}
                        onTextChanged: loginViewModel.username = text
                    }
                }
            }

            // ── Public Key ───────────────────────────────────────────
            Column {
                Layout.fillWidth: true
                Layout.bottomMargin: 20
                spacing: 8

                Label {
                    text: "PUBLIC KEY"
                    font.pixelSize: 9
                    font.letterSpacing: 2
                    font.family: "Courier New"
                    color: loginScreenRoot.textSec
                }
                Rectangle {
                    width: parent.width; height: 40
                    radius: 3
                    color: publicKeyField.activeFocus
                        ? loginScreenRoot.fieldFocus
                        : loginScreenRoot.fieldBg
                    border.color: publicKeyField.activeFocus
                        ? loginScreenRoot.borderFoc
                        : loginScreenRoot.borderSub
                    border.width: 1
                    Behavior on color        { ColorAnimation { duration: 150 } }
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    TextField {
                        id: publicKeyField
                        anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
                        text: "ZixewENi85M3vxEUIu0TC5/nrzuUsHAT4ZTdhc8BC0M="
                        placeholderText: "Base64 encoded public key"
                        color: loginScreenRoot.textPri
                        placeholderTextColor: loginScreenRoot.textSec
                        font.pixelSize: 12
                        font.family: "Courier New"
                        selectionColor: loginScreenRoot.accent
                        background: Item {}
                        onTextChanged: loginViewModel.public_key = text
                    }
                }
            }

            // ── Private Key ──────────────────────────────────────────
            Column {
                Layout.fillWidth: true
                Layout.bottomMargin: 32
                spacing: 8

                Label {
                    text: "PRIVATE KEY"
                    font.pixelSize: 9
                    font.letterSpacing: 2
                    font.family: "Courier New"
                    color: loginScreenRoot.textSec
                }
                Rectangle {
                    width: parent.width; height: 40
                    radius: 3
                    color: privateKeyField.activeFocus
                        ? loginScreenRoot.fieldFocus
                        : loginScreenRoot.fieldBg
                    border.color: privateKeyField.activeFocus
                        ? loginScreenRoot.borderFoc
                        : loginScreenRoot.borderSub
                    border.width: 1
                    Behavior on color        { ColorAnimation { duration: 150 } }
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    TextField {
                        id: privateKeyField
                        anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
                        echoMode: TextField.Password
                        placeholderText: "Enter your private key"
                        color: loginScreenRoot.textPri
                        placeholderTextColor: loginScreenRoot.textSec
                        font.pixelSize: 13
                        selectionColor: loginScreenRoot.accent
                        background: Item {}
                        onTextChanged: loginViewModel.private_key = text
                    }
                }
            }

            // ── Sign In Button ───────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                Layout.bottomMargin: 36
                height: 44
                radius: 3
                color: loginMouse.pressed
                    ? loginScreenRoot.accentPrs
                    : loginMouse.containsMouse
                        ? loginScreenRoot.accentHov
                        : loginScreenRoot.accent
                Behavior on color { ColorAnimation { duration: 120 } }

                Label {
                    anchors.centerIn: parent
                    text: loginViewModel.isLoading ? "AUTHENTICATING..." : "SIGN IN"
                    font.pixelSize: 10
                    font.letterSpacing: 2.5
                    font.family: "Courier New"
                    font.weight: Font.Medium
                    color: "#FFFFFF"
                }

                MouseArea {
                    id: loginMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        loginViewModel.username    = usernameField.text
                        loginViewModel.public_key  = publicKeyField.text
                        loginViewModel.private_key = privateKeyField.text
                        loginViewModel.login()
                    }
                }
            }
        }
    }

    // ─── Failure Dialog ───────────────────────────────────────────────
    Dialog {
        id: failureDialog
        anchors.centerIn: parent
        modal: true
        standardButtons: Dialog.Ok
        property alias text: failureLabel.text

        background: Rectangle {
            color: loginScreenRoot.cardBg
            border.color: loginScreenRoot.danger
            border.width: 1
            radius: 4
        }

        header: Item {
            height: 52
            Row {
                anchors { left: parent.left; leftMargin: 20; verticalCenter: parent.verticalCenter }
                spacing: 10

                Rectangle {
                    width: 6; height: 6; radius: 3
                    color: loginScreenRoot.danger
                    anchors.verticalCenter: parent.verticalCenter
                }
                Label {
                    text: "Authentication failed"
                    font.pixelSize: 13
                    font.weight: Font.Medium
                    color: loginScreenRoot.danger
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        contentItem: Item {
            implicitWidth: 320
            implicitHeight: failureLabel.implicitHeight + 28

            Label {
                id: failureLabel
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                color: loginScreenRoot.textSec
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
        }
    }

    // ─── Connections ──────────────────────────────────────────────────
    Connections {
        target: loginViewModel
        function onLogin_failed(reason) {
            failureDialog.text = reason
            failureDialog.open()
        }
    }
}
