if('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js', {});
};

var buttons = document.getElementsByClassName('button');
for(var i = 0; i < buttons.length; ++i) {
    var button = buttons[i];
    button.addEventListener('click', function() {
        var classes = this.classList;
        var time = this.attributes['data-timeout'].value;
        var modlet = this.attributes['data-modlet'].value;
        var mode = this.attributes['data-mode'].value;
        setTimer(modlet, mode, time);
    });
}

function setTimer(modlet, mode, time) {
    console.log("setTimer", {modlet: modlet, mode: mode, time: time});
    fetch('/set-timer', {
        method: 'POST',
        body: JSON.stringify({mode: mode, modlet: modlet, time: time}),
        cache: 'no-cache',
        headers: {'content-type': 'application/json'},
    }).then(function(response) {
        if(response.status == 200) {
            response.json().then(function(obj) {
                console.log("Response:", obj);
            });
        }
    });
}
