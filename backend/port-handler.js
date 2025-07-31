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
    exec(`uvicorn main:app --reload --port ${port}`, (err, stdout, stderr) => {
        if (err) console.error(err);
        process.stdout.write(stdout);
        process.stderr.write(stderr);
    });
});
