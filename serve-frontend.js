#!/usr/bin/env node
const fs = require('fs');
const http = require('http');
const path = require('path');

const outPath = path.join(__dirname, 'out');
const PORT = 3001;

const server = http.createServer((req, res) => {
  let filePath = path.join(outPath, req.url === '/' ? 'index.html' : req.url);
  
  fs.readFile(filePath, (err, content) => {
    if (err) {
      // Send index.html for SPA routing
      fs.readFile(path.join(outPath, 'index.html'), (err2, content2) => {
        if (err2) {
          res.writeHead(404, { 'Content-Type': 'text/plain' });
          res.end('404 - File Not Found');
          return;
        }
        res.writeHead(200, { 'Content-Type': 'text/html;charset=UTF-8' });
        res.end(content2);
      });
    } else {
      const ext = path.extname(filePath);
      const mimeTypes = {
        '.html': 'text/html;charset=UTF-8',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject'
      };
      const contentType = mimeTypes[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`Frontend server running on http://localhost:${PORT}`);
  console.log(`Serving from: ${outPath}`);
});
