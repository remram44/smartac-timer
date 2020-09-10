import QtQuick 2.5
import QtQuick.Layouts 1.0
import org.kde.plasma.components 2.0 as PlasmaComponents
import org.kde.plasma.plasmoid 2.0

Item {
    id: root

    Plasmoid.icon: "zone-out"

    // Always display the compact view.
    // Never show the full popup view even if there is space for it.
    Plasmoid.preferredRepresentation: Plasmoid.compactRepresentation

    Timer {
        interval: 30000
        running: true
        repeat: true
        onTriggered: updateStatus()
    }

    property var status: undefined
    signal statusUpdated(var status)

    function updateStatus() {
        var req = new XMLHttpRequest();
        req.responseType = "json";
        req.open("GET", "https://smartac.example.org/api/status", true);
        req.onload = function() {
            root.status = req.response.devices;
            root.statusUpdated(root.status);
        };
        req.send();
    }

    function switchDevice(status, deviceId) {
        var mode = status?"on":"off";
        console.log("Switching device ", deviceId, mode);
        var req = new XMLHttpRequest();
        req.open("POST", "https://smartac.example.org/api/switch/" + deviceId + "/" + mode);
        req.onload = function() {
            updateStatus();
        };
        req.send();
    }

    Component.onCompleted: updateStatus()

    Plasmoid.fullRepresentation: ColumnLayout {
        id: buttonLayout

        Component {
            id: deviceButton
            PlasmaComponents.Button {
                property int deviceId
                property bool status
                onClicked: root.switchDevice(!status, deviceId)
            }
        }

        PlasmaComponents.Button {
            id: toggleButton
            text: "Loading..."
            enabled: false
        }

        function updateStatus(status) {
            if(root.status === undefined) {
                return;
            }
            buttonLayout.children = [];
            for(var i = 0; i < status.length; ++i) {
                var d = status[i];
                deviceButton.createObject(
                    buttonLayout,
                    {deviceId: d.id, status: d.status === "on", text: d.status + " " + d.name},
                );
            }
        }

        Component.onCompleted: {
            updateStatus(root.status);
            root.statusUpdated.connect(updateStatus);
        }
    }
}
