function switchDevice(mode, deviceId) {
  var req = new XMLHttpRequest();
  req.open('POST', '/api/switch/' + deviceId + '/' + mode);
  req.send();
}

function setDeviceTimer(mode, deviceId, minutes) {
  var req = new XMLHttpRequest();
  req.open('POST', '/api/set-timer/' + deviceId);
  req.send(JSON.stringify({
    delay: minutes * 60,
    mode: mode,
  }));
}

var req = new XMLHttpRequest();
req.responseType = 'json';
req.open('GET', '/api/status', true);
req.onload = function() {
  var obj = req.response;
  var devices = document.getElementById('devices');
  devices.innerHTML = '';
  for(var i = 0; i < obj.devices.length; ++i) {
    var d = obj.devices[i];
    var inv;
    if(d.status === 'on') {
      inv = 'off';
    } else {
      inv = 'on';
    }
    var elem = document.createElement('tr');
    var h = (
      '<td>' + d.name + '</td>' +
      '<td><a href="javascript:switchDevice(\'' + inv + '\', ' + d.id + ')">' + d.status + '</a></td>'
    );
    if(d.temperature) {
      h += (
        '<td>current: ' + d.temperature.farenheit + '°F</td>'
      );
    } else {
      h += '<td></td>';
    }
    if(d.thermostat) {
      h += (
        '<td>target: ' + d.thermostat.farenheit + '°F</td>'
      );
    } else {
      h += '<td></td>';
    }
    if(d.timer) {
      h += (
        '<td>turn ' + d.timer.mode + ' at ' + d.timer.when + '</td>'
      );
    } else {
      h += '<td></td>';
    }
    h += (
      '<td>Turn ' + inv + ' in ' +
      '<a href="javascript:setDeviceTimer(\'' + inv + '\', ' + d.id + ', ' + (30) + ')">30min</a> ' +
      '<a href="javascript:setDeviceTimer(\'' + inv + '\', ' + d.id + ', ' + (60) + ')">1hr</a> ' +
      '</td>'
    );
    elem.innerHTML = h;
    devices.appendChild(elem);
  }
};
req.send();
