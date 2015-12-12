function setupWebsocket(callback) {
    var l = document.location;
    var ws = new WebSocket("ws://" + l.hostname + ":" + l.port + "/ws?id=foobar");

    ws.onopen = function() {
    };

    ws.onmessage = function (evt) {
        var received_msg = evt.data;
        callback(received_msg);
    };

    ws.onclose = function() {
        console.log("WS closed");
    };
}
