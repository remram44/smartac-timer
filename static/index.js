function entriesMatch(a, b) {
  return a.id == b.id;
}

function reconcileList(container, currentList, newList, buildFn) {
  var currentElement = container.firstElementChild;
  var currentIdx = 0;
  var newIdx = 0;
  while(true) {
    if(currentIdx < currentList.length) {
      if(newIdx >= newList.length || currentList[currentIdx].id < newList[newIdx].id) {
        // Delete current element
        var next = currentElement.nextElementSibling;
        container.removeChild(currentElement);
        currentElement = next;
        currentIdx++;
      } else if(currentList[currentIdx].id > newList[newIdx].id) {
        // Insert before current
        var newChild = buildFn(newList[newIdx]);
        container.insertBefore(newChild, currentElement);
        newIdx++;
      } else {
        if(entriesMatch(currentList[currentIdx], newList[newIdx])) {
          // Entries match, move on
          currentIdx++;
          newIdx++;
          currentElement = currentElement.nextElementSibling;
        } else {
          // Entries don't match, delete current element
          var next = currentElement.nextElementSibling;
          container.removeChild(currentElement);
          currentElement = next;
          currentIdx++;
        }
      }
    } else {
      if(newIdx < newList.length) {
        // Insert new element
        var newChild = buildFn(newList[newIdx]);
        if(currentElement) {
          container.insertBefore(newChild, currentElement);
        } else {
          container.appendChild(newChild);
        }
        newIdx++;
      } else {
        // Done with both lists
        break;
      }
    }
  }
  return newList;
}

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
