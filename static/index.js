function sortByKey(array, key) {
  array.sort(function(a, b) {
    if(key(a) < key(b)) {
      return -1;
    } else if(key(a) > key(b)) {
      return 1;
    } else {
      return 0;
    }
  });
}

function objEqual(obj1, obj2) {
  var props1 = Object.getOwnPropertyNames(obj1);
  var props2 = Object.getOwnPropertyNames(obj2);

  if(props1.length != props2.length) {
    return false;
  } else {
    for(var i = 0; i < props1.length; i++) {
      var prop = props1[i];

      if(typeof(obj1[prop]) === 'object' && typeof(obj2[prop]) === 'object') {
        if(!objEqual(obj1[prop], obj2[prop])) {
          return false;
        }
      } else if(obj1[prop] !== obj2[prop]) {
        return false;
      }
    }
  }

  return true;
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
        if(objEqual(currentList[currentIdx], newList[newIdx])) {
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
  req.onload = function() {
    updateStatusSoon(2);
  };
  req.send();
}

function setDeviceTimer(mode, deviceId, minutes) {
  var req = new XMLHttpRequest();
  req.open('POST', '/api/set-timer/' + deviceId);
  req.onload = function() {
    updateStatusSoon(2);
  };
  req.send(JSON.stringify({
    delay: minutes * 60,
    mode: mode,
  }));
}

function renderDeviceRow(d) {
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
  return elem;
}

var currentStatus = undefined;
var updateTimer = undefined;

function updateStatusSoon(delay) {
  if(updateTimer !== undefined) {
    clearTimeout(updateTimer);
  }
  updateTimer = setTimeout(updateStatus, delay * 1000);
}

function updateStatus() {
  var req = new XMLHttpRequest();
  req.responseType = 'json';
  req.open('GET', '/api/status', true);
  req.onload = function() {
    var newStatus = req.response;
    sortByKey(newStatus.devices, function(d) { return d.id; });
    var devices = document.getElementById('devices');
    if(currentStatus === undefined) {
      devices.innerHTML = '';
      currentStatus = {devices: []};
    }
    reconcileList(devices, currentStatus.devices, newStatus.devices, renderDeviceRow);
    currentStatus = newStatus;
  };
  req.send();

  updateStatusSoon(30);
}

updateStatus();
