// kill-ports.js
const { exec } = require('child_process');
const ports = [3000, 8000]; // Add more ports if needed

ports.forEach(port => {
    exec(`netstat -ano | findstr :${port}`, (err, stdout) => {
        if (stdout) {
            const lines = stdout.trim().split('\n');
            lines.forEach(line => {
                const pid = line.trim().split(/\s+/).pop();
                if (pid) {
                    exec(`taskkill /PID ${pid} /F`, (err) => {
                        if (err) console.error(`Failed to kill PID ${pid}: ${err}`);
                        else console.log(`Killed process on port ${port} (PID ${pid})`);
                    });
                }
            });
        }
    });
});
