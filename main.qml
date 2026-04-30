import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 1.3

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 600
    height: 450
    title: "Rimuovi Password da PDF"

    Material.theme: Material.Light
    Material.accent: Material.DeepPurple

    // Funzione chiamata quando la finestra è pronta
    Component.onCompleted: {
        passwordField.text = backend.loadPassword()
    }

    // Finestre di dialogo
    MessageDialog {
        id: messageDialog
        title: "Messaggio"
        onAccepted: close()
    }

    FileDialog {
        id: openPdfDialog
        title: "Seleziona PDF"
        nameFilters: ["PDF files (*.pdf *.PDF)"]
        selectExisting: true
        onAccepted: {
            backend.requestPdfProcessing(openPdfDialog.fileUrl, passwordField.text)
        }
    }

    FileDialog {
        id: savePdfDialog
        title: "Salva PDF"
        nameFilters: ["PDF files (*.pdf)"]
        selectExisting: false
        onAccepted: {
            backend.savePdf(savePdfDialog.fileUrl, passwordField.text)
        }
    }

    // Segnali dal backend
    Connections {
        target: backend
        function onError(msg) {
            messageDialog.title = "Errore"
            messageDialog.icon = StandardIcon.Critical
            messageDialog.text = msg
            messageDialog.open()
        }
        function onInfo(msg) {
            messageDialog.title = "Informazione"
            messageDialog.icon = StandardIcon.Information
            messageDialog.text = msg
            messageDialog.open()
        }
        function onSuccess(msg) {
            messageDialog.title = "Successo"
            messageDialog.icon = StandardIcon.Information
            messageDialog.text = msg
            messageDialog.open()
        }
        function onSaveDialogRequested(suggestedUrl) {
            savePdfDialog.folder = suggestedUrl
            savePdfDialog.open()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        Label {
            text: "Inserisci la password del PDF:"
            font.pixelSize: 16
        }

        TextField {
            id: passwordField
            echoMode: TextInput.Password
            placeholderText: "Password"
            Layout.fillWidth: true
        }

        Button {
            text: "Seleziona PDF e Rimuovi Password"
            Layout.alignment: Qt.AlignHCenter
            onClicked: {
                if (passwordField.text === "") {
                    messageDialog.title = "Errore"
                    messageDialog.icon = StandardIcon.Critical
                    messageDialog.text = "Inserisci la password del PDF."
                    messageDialog.open()
                } else {
                    openPdfDialog.open()
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: dropArea.containsDrag ? Material.color(Material.Grey, Material.Shade200) : Material.color(Material.Grey, Material.Shade100)
            radius: 8
            border.color: dropArea.containsDrag ? Material.accent : Material.color(Material.Grey, Material.Shade400)
            border.width: 2
            
            DropArea {
                id: dropArea
                anchors.fill: parent
                onDropped: {
                    if (drop.hasUrls) {
                        for (var i = 0; i < drop.urls.length; i++) {
                            var fileUrl = drop.urls[i]
                            if (fileUrl.toLowerCase().endsWith(".pdf")) {
                                if (passwordField.text === "") {
                                    messageDialog.title = "Errore"
                                    messageDialog.icon = StandardIcon.Critical
                                    messageDialog.text = "Inserisci la password del PDF."
                                    messageDialog.open()
                                    return
                                }
                                backend.requestPdfProcessing(fileUrl, passwordField.text)
                                break // Gestiamo solo il primo per ora
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 10

                Label {
                    text: "Trascina qui il PDF"
                    font.pixelSize: 20
                    color: Material.color(Material.Grey, Material.Shade700)
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Label {
                    text: "protetto da password"
                    font.pixelSize: 16
                    color: Material.color(Material.Grey, Material.Shade600)
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}
