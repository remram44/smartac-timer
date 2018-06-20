if('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js', {});
};

var buttons = document.getElementsByClassName('off-button');
for(var i = 0; i < buttons.length; ++i) {
    var button = buttons[i];
    button.addEventListener('click', function() {
        var classes = button.classList;
        var time = button.attributes['data-timeout'];
        var modlet = button.attributes['data-modlet'];
        setTimer(modlet, 'off', time);
    });
}

function setTimer(modlet, mode, time) {
    fetch('/set-timer', {
        method: 'POST',
        body: JSON.stringify({mode: mode, modlet: modlet, time: time}),
        cache: 'no-cache',
        headers: {'content-type': 'application/json'},
    }).then(function(response) {
        if(response.status == 200) {
            console.log("Response:", response.json());
        }
    });
}
