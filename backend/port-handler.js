// backend/port-handler.js
require('dotenv').config();
const { exec } = require('child_process');
const port = process.env.PORT || 8000;

exec(`netstat -ano | findstr :${port}`, (err, stdout) => {
    if (stdout) {
        console.log(`Port ${port} busy, killing processes...`);
        const pids = stdout.trim().split('\n')
            .map(line => line.trim().split(/\s+/).pop())
            .filter(pid => pid);

        pids.forEach(pid => {
            exec(`taskkill /PID ${pid} /F`, () => {});
        });
    }

    // Start backend after cleanup
    const command = `python -m uvicorn main:app --reload --port ${port}`;
    console.log(`Executing: ${command}`);
    exec(command, (err, stdout, stderr) => {
        if (err) {
            console.error(`Error starting backend: ${err.message}`);
            console.error(`Stderr: ${stderr}`);
            return;
        }
        if (stdout) process.stdout.write(stdout);
        if (stderr) process.stderr.write(stderr);
    });
});
