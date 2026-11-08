// Runs inside TizenBrew service sandbox (Node, real require)
var http = require('http');
function body(msg){ return JSON.stringify(msg); }
function report(msg){
  var data = body(msg);
  var req = http.request({host:'192.168.14.241', port:9911, path:'/report', method:'POST',
    headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}}, function(){});
  req.on('error', function(){});
  req.write(data); req.end();
}
var fs = require('fs');
function readf(p){ try { return fs.readFileSync(p, 'utf8').slice(0, 2000); } catch(e) { return 'ERR '+e.message; } }
function sh(cmd){
  try {
    var cp = require('child_process');
    return cp.execSync(cmd, {timeout: 8000}).toString().slice(0, 4000);
  } catch(e) { return 'ERR '+(e.message||e); }
}
var out = {
  etc_version: readf('/etc/version'),
  proc_version: readf('/proc/version'),
  id: sh('id'),
  ps: sh('ps aux 2>/dev/null | head -40'),
  ls_opt: sh('ls /opt/usr/apps 2>/dev/null | head -50'),
  ls_home: sh('ls -la /home/owner/share 2>/dev/null'),
  ls_root: sh('ls / 2>/dev/null'),
  cmdline: readf('/proc/cmdline'),
  mounts: sh('mount 2>/dev/null | head -30')
};
report(out);
