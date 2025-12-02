const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 5050;
const LLAMA_URL = 'http://localhost:8000';
const PROJECT_ROOT = process.cwd();

// File upload support (for importing folders via browser)
const multer = require('multer');
const upload = multer({ storage: multer.memoryStorage() });

// Middleware
app.use(express.json({ limit: '50mb' }));
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, x-admin-token');
    next();
});

// Serve static files
app.use(express.static(PROJECT_ROOT));

// Admin token validation
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'localdev';
function checkAdminToken(req, res) {
    const token = req.headers['x-admin-token'];
    if (!token || token !== ADMIN_TOKEN) {
        res.status(401).json({ ok: false, error: 'Unauthorized' });
        return false;
    }
    return true;
}

// ============= FILE OPERATIONS =============

/**
 * List all files in project
 */
app.get('/api/list-files', (req, res) => {
    try {
        const files = [];
        function walk(dir, prefix = '') {
            try {
                const items = fs.readdirSync(dir);
                items.forEach(item => {
                    if (item.startsWith('.') || item === 'node_modules') return;
                    const fullPath = path.join(dir, item);
                    try {
                        const stat = fs.statSync(fullPath);
                        if (stat.isDirectory()) {
                            walk(fullPath, prefix ? `${prefix}/${item}` : item);
                        } else {
                            files.push({
                                name: prefix ? `${prefix}/${item}` : item,
                                size: stat.size,
                                modified: stat.mtime
                            });
                        }
                    } catch (e) { }
                });
            } catch (e) { }
        }
        walk(PROJECT_ROOT);
        res.json({ files });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

/**
 * Get file content
 */
app.post('/api/get-file', (req, res) => {
    try {
        const { path: filePath } = req.body;
        if (!filePath) return res.status(400).json({ error: 'Missing path' });

        const fullPath = path.join(PROJECT_ROOT, filePath);
        if (!fullPath.startsWith(PROJECT_ROOT)) {
            return res.status(403).json({ error: 'Access denied' });
        }

        const content = fs.readFileSync(fullPath, 'utf-8');
        res.json({ ok: true, content });
    } catch (e) {
        res.status(404).json({ error: 'File not found' });
    }
});

/**
 * Save file (requires admin token)
 */
app.post('/api/save-file', (req, res) => {
    if (!checkAdminToken(req, res)) return;

    const { path: filePath, content } = req.body;
    if (!filePath || content === undefined) {
        return res.status(400).json({ error: 'Missing path or content' });
    }

    try {
        const fullPath = path.join(PROJECT_ROOT, filePath);
        if (!fullPath.startsWith(PROJECT_ROOT)) {
            return res.status(403).json({ error: 'Access denied' });
        }

        // Create backup
        if (fs.existsSync(fullPath)) {
            const backupPath = fullPath + '.bak';
            fs.copyFileSync(fullPath, backupPath);
        }

        // Create directory if needed
        const dir = path.dirname(fullPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        // Write file
        fs.writeFileSync(fullPath, content, 'utf-8');

        res.json({ ok: true, path: filePath });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

/**
 * Delete file (requires admin token)
 */
app.post('/api/delete-file', (req, res) => {
    if (!checkAdminToken(req, res)) return;

    const { path: filePath } = req.body;
    if (!filePath) return res.status(400).json({ error: 'Missing path' });

    try {
        const fullPath = path.join(PROJECT_ROOT, filePath);
        if (!fullPath.startsWith(PROJECT_ROOT)) {
            return res.status(403).json({ error: 'Access denied' });
        }

        if (fs.existsSync(fullPath)) {
            fs.unlinkSync(fullPath);
        }

        res.json({ ok: true });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ============= AI STREAMING =============

/**
 * Stream text generation from Llama (or fallback response if unavailable)
 */
app.post('/api/stream', async (req, res) => {
    const { prompt, n_predict = 2000, temperature = 0.7, top_p = 0.9 } = req.body;

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    try {
        // Try Llama with a short timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        try {
            const response = await fetch(`${LLAMA_URL}/completion`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt,
                    n_predict,
                    temperature,
                    top_p,
                    top_k: 40,
                    repeat_penalty: 1.05,
                    stream: true
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data:')) {
                            try {
                                const json = JSON.parse(line.substring(5));
                                if (json.content) {
                                    res.write(`data: ${JSON.stringify({ content: json.content })}\n\n`);
                                }
                            } catch (e) { }
                        }
                    }
                }

                res.write('data: [DONE]\n\n');
                res.end();
                return;
            }
        } catch (e) {
            clearTimeout(timeoutId);
        }

        // Fallback if Llama unavailable
        const fallbackMsg = "CodeForge Studio is ready for editing and file management. AI features require Llama server (optional). For now, you can create, edit, and save files using the editor!";
        res.write(`data: ${JSON.stringify({ content: fallbackMsg })}\n\n`);
        res.write('data: [DONE]\n\n');
        res.end();
    } catch (e) {
        res.write(`data: ${JSON.stringify({ error: 'Stream error' })}\n\n`);
        res.end();
    }
});

// ============= CREATE / FOLDER OPERATIONS =============

/**
 * Create a new file (requires admin token)
 */
app.post('/api/create-file', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    const { path: filePath, content = '' } = req.body;
    if (!filePath) return res.status(400).json({ error: 'Missing path' });

    try {
        const fullPath = path.join(PROJECT_ROOT, filePath);
        if (!fullPath.startsWith(PROJECT_ROOT)) return res.status(403).json({ error: 'Access denied' });
        const dir = path.dirname(fullPath);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(fullPath, content, 'utf-8');
        res.json({ ok: true, path: filePath });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

/**
 * Create folder (requires admin token)
 */
app.post('/api/create-folder', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    const { path: folderPath } = req.body;
    if (!folderPath) return res.status(400).json({ error: 'Missing path' });

    try {
        const fullPath = path.join(PROJECT_ROOT, folderPath);
        if (!fullPath.startsWith(PROJECT_ROOT)) return res.status(403).json({ error: 'Access denied' });
        if (!fs.existsSync(fullPath)) fs.mkdirSync(fullPath, { recursive: true });
        res.json({ ok: true, path: folderPath });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

/**
 * Import an external folder into the project (requires admin token)
 * Copies files from an absolute path into a subfolder under PROJECT_ROOT
 */
app.post('/api/import-folder', (req, res) => {
    if (!checkAdminToken(req, res)) return;
    const { folderPath } = req.body;
    if (!folderPath) return res.status(400).json({ error: 'Missing folderPath' });

    try {
        if (!fs.existsSync(folderPath)) return res.status(400).json({ error: 'Source folder not found' });

        const dest = path.join(PROJECT_ROOT, path.basename(folderPath));
        if (!dest.startsWith(PROJECT_ROOT)) return res.status(403).json({ error: 'Access denied' });

        function copyDir(src, dst) {
            if (!fs.existsSync(dst)) fs.mkdirSync(dst, { recursive: true });
            let count = 0;
            const items = fs.readdirSync(src);
            for (const item of items) {
                if (item.startsWith('.') || item === 'node_modules') continue;
                const s = path.join(src, item);
                const d = path.join(dst, item);
                const stat = fs.statSync(s);
                if (stat.isDirectory()) {
                    count += copyDir(s, d);
                } else {
                    fs.copyFileSync(s, d);
                    count++;
                }
            }
            return count;
        }

        const count = copyDir(folderPath, dest);
        res.json({ ok: true, count, dest });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

/**
 * Upload folder files from browser (requires admin token)
 * Expects multipart/form-data with field name 'files' and file names containing relative paths
 */
// Improved upload handler: accept any file field, preserve relative paths (from webkitRelativePath),
// write files to project tree and log results for debugging.
app.post('/api/upload-folder', upload.any(), (req, res) => {
    if (!checkAdminToken(req, res)) return;
    try {
        const files = req.files || [];
        if (files.length === 0) return res.status(400).json({ error: 'No files uploaded' });

        // Get target folder from form data (user specifies where to upload)
        let targetFolder = (req.body?.targetFolder || '').trim();
        if (!targetFolder) {
            targetFolder = '';
        }

        let count = 0;
        const logLines = [];

        for (const f of files) {
            // Some browsers send webkitRelativePath in the `originalname` when the 3rd arg of form.append is used.
            // Other times the browser may put the relative path in a custom property; try common fallbacks.
            let relPath = f.originalname || f.filename || f.fieldname || '';
            // If a client sent a custom property webkitRelativePath, prefer that.
            if (f.webkitRelativePath) relPath = f.webkitRelativePath;

            relPath = String(relPath).replace(/\\/g, '/').replace(/^\//, '').trim();
            if (!relPath) continue;

            // Construct full path: PROJECT_ROOT / targetFolder / relPath
            let fullPath = path.join(PROJECT_ROOT, targetFolder, relPath);
            if (!fullPath.startsWith(PROJECT_ROOT)) {
                logLines.push(`SKIP (out-of-root): ${relPath}`);
                continue;
            }

            const dir = path.dirname(fullPath);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

            // Buffer may be present for memoryStorage; for other storage engines, fallback to path
            if (f.buffer) {
                fs.writeFileSync(fullPath, f.buffer);
            } else if (f.path && fs.existsSync(f.path)) {
                fs.copyFileSync(f.path, fullPath);
            } else {
                // Nothing to write
                logLines.push(`WARN (no data): ${relPath}`);
                continue;
            }

            count++;
            logLines.push(`WROTE: ${relPath}`);
        }

        // Append to upload log for debugging
        try {
            const logPath = path.join(PROJECT_ROOT, 'codeforge_upload.log');
            const now = new Date().toISOString();
            fs.appendFileSync(logPath, `--- ${now} - uploaded ${count} files\n` + logLines.join('\n') + '\n');
        } catch (e) { }

        res.json({ ok: true, count, details: logLines.slice(0, 50) });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ============= DEPENDENCY CHECKER =============

/**
 * Check package.json and requirements.txt for outdated dependencies
 */
app.get('/api/check-deps', async (req, res) => {
    try {
        const result = { npm: [], pip: [] };

        // Check package.json
        const pkgPath = path.join(PROJECT_ROOT, 'package.json');
        if (fs.existsSync(pkgPath)) {
            try {
                const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
                const deps = Object.assign({}, pkg.dependencies || {}, pkg.devDependencies || {});
                for (const [name, ver] of Object.entries(deps)) {
                    try {
                        const r = await fetch(`https://registry.npmjs.org/${encodeURIComponent(name)}/latest`);
                        if (!r.ok) continue;
                        const j = await r.json();
                        const latest = j.version;
                        const current = ('' + ver).replace(/^[^0-9]*/g, '');
                        result.npm.push({ name, current, latest, outdated: latest && current && latest !== current });
                    } catch (e) { }
                }
            } catch (e) { }
        }

        // Check requirements.txt
        const reqPath = path.join(PROJECT_ROOT, 'requirements.txt');
        if (fs.existsSync(reqPath)) {
            try {
                const lines = fs.readFileSync(reqPath, 'utf-8').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
                for (const line of lines) {
                    const parts = line.split(/[=<>!~]+/).map(p => p.trim()).filter(Boolean);
                    const name = parts[0];
                    const current = parts[1] || '';
                    try {
                        const r = await fetch(`https://pypi.org/pypi/${encodeURIComponent(name)}/json`);
                        if (!r.ok) continue;
                        const j = await r.json();
                        const latest = j.info && j.info.version;
                        result.pip.push({ name, current: current || 'unknown', latest, outdated: latest && current && latest !== current });
                    } catch (e) { }
                }
            } catch (e) { }
        }

        res.json(result);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ============= COMMAND EXECUTION =============

/**
 * Execute shell command (requires admin token)
 */
app.post('/api/exec', (req, res) => {
    if (!checkAdminToken(req, res)) return;

    const { cmd } = req.body;
    if (!cmd) return res.status(400).json({ error: 'Missing command' });

    exec(cmd, { cwd: PROJECT_ROOT, maxBuffer: 5 * 1024 * 1024 }, (error, stdout, stderr) => {
        res.json({
            ok: !error,
            stdout,
            stderr,
            error: error ? error.message : null
        });
    });
});

// ============= GIT / SOURCE CONTROL =============

/**
 * Commit changes (requires admin token)
 */
app.post('/api/git-commit', (req, res) => {
    if (!checkAdminToken(req, res)) return;

    const { message } = req.body;
    if (!message) return res.status(400).json({ error: 'Missing message' });

    const gitCmd = `git -C "${PROJECT_ROOT}" add -A && git -C "${PROJECT_ROOT}" commit -m "${message.replace(/"/g, '\\"')}"`;

    exec(gitCmd, (error, stdout, stderr) => {
        if (error && !stdout.includes('nothing to commit')) {
            return res.status(500).json({ error: stderr });
        }
        res.json({ ok: true, message: stdout || 'Committed' });
    });
});

/**
 * Get git status
 */
app.get('/api/git-status', (req, res) => {
    exec(`git -C "${PROJECT_ROOT}" status --porcelain`, (error, stdout) => {
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
        res.json({ changes });
    });
});

/**
 * Sync files to partner (requires admin token)
 */
app.post('/api/sync', (req, res) => {
    if (!checkAdminToken(req, res)) return;

    const { partnerPath } = req.body;
    if (!partnerPath) return res.status(400).json({ error: 'Missing partnerPath' });

    try {
        if (!fs.existsSync(partnerPath)) {
            fs.mkdirSync(partnerPath, { recursive: true });
        }

        function syncDir(src, dest) {
            const items = fs.readdirSync(src);
            let count = 0;

            items.forEach(item => {
                if (item.startsWith('.') || item === 'node_modules') return;

                const srcPath = path.join(src, item);
                const destPath = path.join(dest, item);
                const stat = fs.statSync(srcPath);

                if (stat.isDirectory()) {
                    if (!fs.existsSync(destPath)) {
                        fs.mkdirSync(destPath, { recursive: true });
                    }
                    count += syncDir(srcPath, destPath);
                } else {
                    fs.copyFileSync(srcPath, destPath);
                    count++;
                }
            });

            return count;
        }

        const count = syncDir(PROJECT_ROOT, partnerPath);
        res.json({ ok: true, count, message: `Synced ${count} files` });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ============= ANALYSIS =============

/**
 * Analyze code
 */
app.post('/api/analyze-code', (req, res) => {
    const { code } = req.body;
    if (!code) return res.status(400).json({ error: 'Missing code' });

    const analysis = {
        lineCount: code.split('\n').length,
        codeQuality: 0,
        security: [],
        performance: [],
        architecture: [],
        issues: []
    };

    let quality = 50;

    if (/try\s*{[\s\S]*?}\s*catch/i.test(code)) {
        quality += 15;
    } else {
        analysis.issues.push('Add error handling');
        quality -= 10;
    }

    if (/function|class|const.*=.*\(|async/i.test(code)) {
        quality += 10;
    }

    if (/\/\/|\/\*|\*\//i.test(code)) {
        quality += 10;
    }

    if (/password|secret|key|token/i.test(code)) {
        analysis.security.push('⚠️ Sensitive data detected');
        quality -= 5;
    }

    analysis.performance.push('Consider caching');
    analysis.codeQuality = Math.min(100, Math.max(0, quality));

    res.json(analysis);
});

// ============= STARTUP =============

app.listen(PORT, () => {
    console.log(`\n╔════════════════════════════════════════════════════╗`);
    console.log(`║   CodeForge Studio Backend                         ║`);
    console.log(`║   Web: http://localhost:${PORT}/vscode_clone.html    ║`);
    console.log(`║   API: http://localhost:${PORT}/api                     ║`);
    console.log(`║   Token: ${ADMIN_TOKEN.padEnd(36)}║`);
    console.log(`╚════════════════════════════════════════════════════╝\n`);
    console.log('Ready! Open http://localhost:5050/vscode_clone.html in your browser.\n');
});

process.on('SIGINT', () => {
    console.log('\nShutting down...');
    process.exit(0);
});
