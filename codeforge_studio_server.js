const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 5050;
const LLAMA_URL = 'http://localhost:8000';

// CRITICAL FIX: Use workspace subfolder to prevent root pollution
const PROJECT_ROOT = process.cwd();
const WORKSPACE_ROOT = path.join(PROJECT_ROOT, 'workspace');

// Create workspace directory if it doesn't exist
if (!fs.existsSync(WORKSPACE_ROOT)) {
    fs.mkdirSync(WORKSPACE_ROOT, { recursive: true });
    console.log(`✅ Created workspace directory: ${WORKSPACE_ROOT}`);
}

// Admin token for security
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'localdev';

// Middleware
app.use(cors());
app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ extended: true, limit: '100mb' }));

// Serve static files from project root (for HTML/CSS/JS)
app.use(express.static(PROJECT_ROOT));

// File upload support
const multer = require('multer');
const upload = multer({ storage: multer.memoryStorage() });

// ============= SECURITY HELPERS =============
function checkAdminToken(req, res) {
    const token = req.headers['x-admin-token'];
    if (!token || token !== ADMIN_TOKEN) {
        res.status(401).json({ ok: false, error: 'Unauthorized - invalid admin token' });
        return false;
    }
    return true;
}

function sanitizePath(userPath) {
    // Remove leading slashes and normalize
    const cleaned = path.normalize(userPath).replace(/^[\\\/]+/, '');
    // Resolve within workspace
    const fullPath = path.join(WORKSPACE_ROOT, cleaned);
    
    // CRITICAL: Prevent directory traversal
    if (!fullPath.startsWith(WORKSPACE_ROOT)) {
        throw new Error('Access denied: path outside workspace');
    }
    
    return fullPath;
}

// ============= FILE OPERATIONS =============

// List all files in workspace
app.get('/api/list-files', (req, res) => {
    try {
        const files = [];
        
        function walkDirectory(dir, prefix = '') {
            try {
                const items = fs.readdirSync(dir);
                
                items.forEach(item => {
                    // Skip hidden files and node_modules
                    if (item.startsWith('.') || item === 'node_modules') return;
                    
                    const fullPath = path.join(dir, item);
                    const relativePath = prefix ? `${prefix}/${item}` : item;
                    
                    try {
                        const stat = fs.statSync(fullPath);
                        
                        if (stat.isDirectory()) {
                            walkDirectory(fullPath, relativePath);
                        } else {
                            files.push({
                                name: relativePath,
                                size: stat.size,
                                modified: stat.mtime,
                                isDirectory: false
                            });
                        }
                    } catch (err) {
                        console.error(`Error reading ${fullPath}:`, err.message);
                    }
                });
            } catch (err) {
                console.error(`Error reading directory ${dir}:`, err.message);
            }
        }
        
        walkDirectory(WORKSPACE_ROOT);
        res.json({ ok: true, files });
    } catch (err) {
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Get file content
app.post('/api/get-file', (req, res) => {
    try {
        const { path: filePath } = req.body;
        if (!filePath) {
            return res.status(400).json({ ok: false, error: 'Missing path' });
        }
        
        const fullPath = sanitizePath(filePath);
        const content = fs.readFileSync(fullPath, 'utf-8');
        
        res.json({ ok: true, content, path: filePath });
    } catch (err) {
        res.status(404).json({ ok: false, error: `File not found: ${err.message}` });
    }
});

// Save file (with backup)
app.post('/api/save-file', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    
    try {
        const { path: filePath, content } = req.body;
        
        if (!filePath || content === undefined) {
            return res.status(400).json({ ok: false, error: 'Missing path or content' });
        }
        
        const fullPath = sanitizePath(filePath);
        const dir = path.dirname(fullPath);
        
        // Create directory if needed
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        
        // Backup existing file
        if (fs.existsSync(fullPath)) {
            const backupPath = fullPath + '.bak';
            fs.copyFileSync(fullPath, backupPath);
        }
        
        // Write file
        fs.writeFileSync(fullPath, content, 'utf-8');
        
        console.log(`✅ Saved: ${filePath} (${content.length} bytes)`);
        res.json({ ok: true, path: filePath, size: content.length });
    } catch (err) {
        console.error('Save error:', err);
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Create new file
app.post('/api/create-file', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    
    try {
        const { path: filePath, content = '' } = req.body;
        
        if (!filePath) {
            return res.status(400).json({ ok: false, error: 'Missing path' });
        }
        
        const fullPath = sanitizePath(filePath);
        const dir = path.dirname(fullPath);
        
        // Create directory if needed
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        
        fs.writeFileSync(fullPath, content, 'utf-8');
        
        console.log(`✅ Created: ${filePath}`);
        res.json({ ok: true, path: filePath });
    } catch (err) {
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Create folder
app.post('/api/create-folder', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    
    try {
        const { path: folderPath } = req.body;
        
        if (!folderPath) {
            return res.status(400).json({ ok: false, error: 'Missing path' });
        }
        
        const fullPath = sanitizePath(folderPath);
        
        if (!fs.existsSync(fullPath)) {
            fs.mkdirSync(fullPath, { recursive: true });
        }
        
        console.log(`✅ Created folder: ${folderPath}`);
        res.json({ ok: true, path: folderPath });
    } catch (err) {
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Delete file
app.post('/api/delete-file', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    
    try {
        const { path: filePath } = req.body;
        
        if (!filePath) {
            return res.status(400).json({ ok: false, error: 'Missing path' });
        }
        
        const fullPath = sanitizePath(filePath);
        
        if (fs.existsSync(fullPath)) {
            fs.unlinkSync(fullPath);
            console.log(`✅ Deleted: ${filePath}`);
        }
        
        res.json({ ok: true, deleted: filePath });
    } catch (err) {
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Rename/Move file
app.post('/api/rename-file', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    
    try {
        const { oldPath, newPath } = req.body;
        
        if (!oldPath || !newPath) {
            return res.status(400).json({ ok: false, error: 'Missing paths' });
        }
        
        const oldFullPath = sanitizePath(oldPath);
        const newFullPath = sanitizePath(newPath);
        
        // Create target directory if needed
        const newDir = path.dirname(newFullPath);
        if (!fs.existsSync(newDir)) {
            fs.mkdirSync(newDir, { recursive: true });
        }
        
        fs.renameSync(oldFullPath, newFullPath);
        
        console.log(`✅ Renamed: ${oldPath} → ${newPath}`);
        res.json({ ok: true, oldPath, newPath });
    } catch (err) {
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Upload folder (browser folder picker)
app.post('/api/upload-folder', upload.any(), (req, res) => {
    if (!checkAdminToken(req, res)) return;
    
    try {
        const files = req.files || [];
        
        if (files.length === 0) {
            return res.status(400).json({ ok: false, error: 'No files uploaded' });
        }
        
        let count = 0;
        const results = [];
        
        for (const file of files) {
            try {
                // Get relative path from original filename
                let relativePath = file.originalname || file.fieldname || '';
                
                // Handle webkitRelativePath if available
                if (file.webkitRelativePath) {
                    relativePath = file.webkitRelativePath;
                }
                
                // Clean path
                relativePath = relativePath.replace(/\\/g, '/').replace(/^\//, '');
                
                if (!relativePath) continue;
                
                const fullPath = sanitizePath(relativePath);
                const dir = path.dirname(fullPath);
                
                // Create directory if needed
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
                
                // Write file
                fs.writeFileSync(fullPath, file.buffer);
                
                count++;
                results.push(`✅ ${relativePath}`);
            } catch (err) {
                results.push(`❌ ${file.originalname}: ${err.message}`);
            }
        }
        
        console.log(`✅ Uploaded ${count}/${files.length} files`);
        res.json({ ok: true, count, total: files.length, results: results.slice(0, 20) });
    } catch (err) {
        res.status(500).json({ ok: false, error: err.message });
    }
});

// ============= AI STREAMING =============

app.post('/api/stream', async (req, res) => {
    const { prompt, n_predict = 2000, temperature = 0.7 } = req.body;
    
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${LLAMA_URL}/completion`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt,
                n_predict,
                temperature,
                stream: true
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeout);
        
        if (response.ok) {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const text = decoder.decode(value);
                const lines = text.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data:')) {
                        res.write(line + '\n\n');
                    }
                }
            }
        }
        
        res.write('data: [DONE]\n\n');
        res.end();
    } catch (err) {
        const fallback = "CodeForge AI is ready! (Llama server optional)";
        res.write(`data: ${JSON.stringify({ content: fallback })}\n\n`);
        res.write('data: [DONE]\n\n');
        res.end();
    }
});

// ============= COMMAND EXECUTION =============

app.post('/api/exec', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    
    const { cmd } = req.body;
    
    if (!cmd) {
        return res.status(400).json({ ok: false, error: 'Missing command' });
    }
    
    console.log(`⚡ Executing: ${cmd}`);
    
    exec(cmd, {
        cwd: WORKSPACE_ROOT,
        timeout: 300000, // 5 minutes
        maxBuffer: 10 * 1024 * 1024 // 10MB
    }, (error, stdout, stderr) => {
        res.json({
            ok: !error,
            stdout: stdout || '',
            stderr: stderr || '',
            error: error ? error.message : null
        });
    });
});

// ============= GIT OPERATIONS =============

app.get('/api/git-status', (req, res) => {
    exec('git status --porcelain', { cwd: WORKSPACE_ROOT }, (error, stdout) => {
        const changes = [];
        
        if (!error && stdout) {
            stdout.split('\n').forEach(line => {
                if (line.trim()) {
                    const status = line.substring(0, 2).trim();
                    const file = line.substring(3);
                    changes.push({ status, file });
                }
            });
        }
        
        res.json({ ok: true, changes });
    });
});

app.post('/api/git-commit', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    
    const { message } = req.body;
    
    if (!message) {
        return res.status(400).json({ ok: false, error: 'Missing commit message' });
    }
    
    const cmd = `git add -A && git commit -m "${message.replace(/"/g, '\\"')}"`;
    
    exec(cmd, { cwd: WORKSPACE_ROOT }, (error, stdout, stderr) => {
        if (error && !stdout.includes('nothing to commit')) {
            return res.status(500).json({ ok: false, error: stderr });
        }
        
        res.json({ ok: true, message: stdout || 'Committed successfully' });
    });
});

// ============= SEARCH =============

app.post('/api/search', (req, res) => {
    const { query } = req.body;
    
    if (!query) {
        return res.status(400).json({ ok: false, error: 'Missing query' });
    }
    
    const results = [];
    
    function searchInDirectory(dir, prefix = '') {
        try {
            const items = fs.readdirSync(dir);
            
            items.forEach(item => {
                if (item.startsWith('.') || item === 'node_modules') return;
                
                const fullPath = path.join(dir, item);
                const relativePath = prefix ? `${prefix}/${item}` : item;
                
                try {
                    const stat = fs.statSync(fullPath);
                    
                    if (stat.isDirectory()) {
                        searchInDirectory(fullPath, relativePath);
                    } else {
                        // Search in filename
                        if (item.toLowerCase().includes(query.toLowerCase())) {
                            results.push({ path: relativePath, type: 'filename' });
                        }
                        
                        // Search in content (for text files)
                        if (stat.size < 1024 * 1024) { // Max 1MB
                            try {
                                const content = fs.readFileSync(fullPath, 'utf-8');
                                if (content.toLowerCase().includes(query.toLowerCase())) {
                                    results.push({ path: relativePath, type: 'content' });
                                }
                            } catch (err) {
                                // Skip binary files
                            }
                        }
                    }
                } catch (err) {
                    // Skip inaccessible files
                }
            });
        } catch (err) {
            // Skip inaccessible directories
        }
    }
    
    searchInDirectory(WORKSPACE_ROOT);
    
    res.json({ ok: true, results: results.slice(0, 100) });
});

// ============= HEALTH CHECK =============

app.get('/health', (req, res) => {
    res.json({
        ok: true,
        service: 'CodeForge Studio Backend',
        version: '3.0',
        workspace: WORKSPACE_ROOT,
        timestamp: new Date().toISOString()
    });
});

app.get('/', (req, res) => {
    res.sendFile(path.join(PROJECT_ROOT, 'vscode_clone.html'));
});

// ============= ERROR HANDLING =============

process.on('uncaughtException', (err) => {
    console.error('❌ Uncaught Exception:', err);
});

process.on('unhandledRejection', (reason) => {
    console.error('❌ Unhandled Rejection:', reason);
});

// Graceful shutdown
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

function shutdown() {
    console.log('\n\n🛑 Shutting down gracefully...');
    process.exit(0);
}

// ============= START SERVER =============

const server = app.listen(PORT, () => {
    console.log('\n' + '='.repeat(70));
    console.log('  🚀 CodeForge Studio Backend v3.0');
    console.log('='.repeat(70));
    console.log(`\n  📡 Server:    http://localhost:${PORT}`);
    console.log(`  📂 Workspace: ${WORKSPACE_ROOT}`);
    console.log(`  🔑 Token:     ${ADMIN_TOKEN}`);
    console.log(`  🧠 Llama:     ${LLAMA_URL}`);
    console.log('\n  🌐 Open: http://localhost:' + PORT + '/vscode_clone.html');
    console.log('\n' + '='.repeat(70) + '\n');
});

// Extended timeouts
server.timeout = 600000;
server.keepAliveTimeout = 610000;
server.headersTimeout = 620000;