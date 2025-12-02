
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

const PORT = process.argv[2] || 5050;
const LLAMA_PORT = 8000;
const LLAMA_URL = `http://127.0.0.1:${LLAMA_PORT}`;

const app = express();

// Simple admin token for sensitive operations (set via env ADMIN_TOKEN). Default only for local dev.
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'localdev';
if (!process.env.ADMIN_TOKEN) {
    console.warn('⚠️ ADMIN_TOKEN not set. Using default localdev token. Do NOT expose this server publicly.');
}

function checkAdminHeader(req, res) {
    const token = req.get('x-admin-token') || req.get('X-Admin-Token') || '';
    if (token !== ADMIN_TOKEN) {
        res.status(403).json({ ok: false, error: 'Unauthorized - invalid admin token' });
        return false;
    }
    return true;
}

// Error handling
process.on('uncaughtException', (err) => {
    console.error('⚠️  Uncaught Exception:', err.message);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('⚠️  Unhandled Rejection:', reason);
});

// Middleware
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: false
}));

app.use(express.json({
    limit: '500mb',
    strict: false
}));

app.use(express.urlencoded({
    extended: true,
    limit: '500mb',
    parameterLimit: 100000
}));

app.use(express.static(__dirname));

// ----------------- File and Exec Endpoints (require admin token) -----------------
// List files under workspace root
app.get('/list-files', async (req, res) => {
    try {
        const root = path.resolve(__dirname);
        const files = await fs.readdir(root, { withFileTypes: true });
        const result = files.filter(f => !f.name.startsWith('node_modules') && !f.name.startsWith('.')).map(f => ({ name: f.name, isDirectory: f.isDirectory() }));
        res.json({ ok: true, files: result });
    } catch (err) {
        console.error('/list-files error', err);
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Save a file from the frontend into the workspace. Body: { path: string, content: string }
app.post('/save-file', async (req, res) => {
    try {
        if (!checkAdminHeader(req, res)) return;
        const { path: relPath, content } = req.body || {};
        if (!relPath || typeof content !== 'string') return res.status(400).json({ ok: false, error: 'Missing path or content' });
        const safePath = path.normalize(relPath).replace(/^([A-Za-z]:)?[\\/]+/, '');
        const abs = path.join(__dirname, safePath);
        await fs.mkdir(path.dirname(abs), { recursive: true });

        // Backup existing file if present
        try {
            const existing = await fs.readFile(abs, 'utf8').catch(() => null);
            if (existing !== null) {
                await fs.writeFile(abs + '.bak', existing, 'utf8');
            }
        } catch (e) {
            // ignore backup errors
            console.warn('Backup failed for', abs, e.message);
        }

        await fs.writeFile(abs, content, 'utf8');
        console.log(`Saved file: ${abs}`);
        res.json({ ok: true, path: safePath });
    } catch (err) {
        console.error('/save-file error', err);
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Rollback file from .bak
app.post('/rollback-file', async (req, res) => {
    try {
        if (!checkAdminHeader(req, res)) return;
        const { path: relPath } = req.body || {};
        if (!relPath) return res.status(400).json({ ok: false, error: 'Missing path' });
        const safePath = path.normalize(relPath).replace(/^([A-Za-z]:)?[\\/]+/, '');
        const abs = path.join(__dirname, safePath);
        const bak = abs + '.bak';
        const existingBak = await fs.readFile(bak, 'utf8').catch(() => null);
        if (existingBak === null) return res.status(404).json({ ok: false, error: 'No backup found' });
        await fs.writeFile(abs, existingBak, 'utf8');
        res.json({ ok: true, restored: safePath });
    } catch (err) {
        console.error('/rollback-file error', err);
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Delete file
app.post('/delete-file', async (req, res) => {
    try {
        if (!checkAdminHeader(req, res)) return;
        const { path: relPath } = req.body || {};
        if (!relPath) return res.status(400).json({ ok: false, error: 'Missing path' });
        const safePath = path.normalize(relPath).replace(/^([A-Za-z]:)?[\\/]+/, '');
        const abs = path.join(__dirname, safePath);
        await fs.unlink(abs).catch(() => null);
        res.json({ ok: true, deleted: safePath });
    } catch (err) {
        console.error('/delete-file error', err);
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Execute a shell command (local only). Body: { cmd: string }
app.post('/exec', async (req, res) => {
    try {
        if (!checkAdminHeader(req, res)) return;
        const { cmd } = req.body || {};
        if (!cmd) return res.status(400).json({ ok: false, error: 'Missing cmd' });
        console.log(`Executing command: ${cmd}`);
        const { exec } = require('child_process');
        exec(cmd, { cwd: __dirname, timeout: 5 * 60 * 1000, maxBuffer: 5 * 1024 * 1024 }, (error, stdout, stderr) => {
            if (error) {
                res.json({ ok: false, error: error.message, stdout, stderr });
            } else {
                res.json({ ok: true, stdout, stderr });
            }
        });
    } catch (err) {
        console.error('/exec error', err);
        res.status(500).json({ ok: false, error: err.message });
    }
});

// Sync changed files to a partner directory. Body: { files: [{path, content}], partnerPath: string }
app.post('/sync', async (req, res) => {
    try {
        if (!checkAdminHeader(req, res)) return;
        const { files, partnerPath } = req.body || {};
        if (!Array.isArray(files) || !partnerPath) return res.status(400).json({ ok: false, error: 'Missing files or partnerPath' });
        const destRoot = path.resolve(partnerPath);
        for (const f of files) {
            const safe = path.normalize(f.path).replace(/^([A-Za-z]:)?[\\/]+/, '');
            const dest = path.join(destRoot, safe);
            await fs.mkdir(path.dirname(dest), { recursive: true });
            await fs.writeFile(dest, f.content, 'utf8');
            console.log(`Synced file to partner: ${dest}`);
        }
        res.json({ ok: true, count: files.length });
    } catch (err) {
        console.error('/sync error', err);
        res.status(500).json({ ok: false, error: err.message });
    }
});


// Logging
const LOG_DIR = './chat_logs';

async function ensureLogDir() {
    try {
        await fs.mkdir(LOG_DIR, { recursive: true });
    } catch (err) {
        console.error('Failed to create log directory:', err);
    }
}

async function logChat(data) {
    try {
        const timestamp = new Date().toISOString();
        const logFile = path.join(LOG_DIR, `${timestamp.split('T')[0]}.jsonl`);
        const logEntry = JSON.stringify({
            timestamp,
            ...data
        }) + '\n';

        await fs.appendFile(logFile, logEntry);
    } catch (err) {
        // Silent fail for logging errors
    }
}

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'codeforge.html'));
});

app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'CodeForge Pro Server v2.5',
        timestamp: new Date().toISOString(),
        llamaServer: LLAMA_URL,
        features: [
            'Expert Code Generation',
            'Production-Ready Output',
            'Split View Support',
            'Advanced Debugging',
            'High Token Output (24K+)'
        ],
        version: '2.5'
    });
});

// STREAMING ENDPOINT - Optimized for large code generation
app.post('/stream', async (req, res) => {
    const startTime = Date.now();
    console.log(`\n${'='.repeat(70)}`);
    console.log(`[${new Date().toISOString()}] 🌊 Expert Stream Request`);

    try {
        const {
            prompt,
            n_predict = 24000,
            temperature = 0.3,
            top_p = 0.95,
            top_k = 50,
            repeat_penalty = 1.2,
            stop = [
                '\nUSER:',
                '\nUser:',
                'USER REQUEST:',
                '\n\nUSER REQUEST:'
            ]
        } = req.body;

        if (!prompt) {
            console.error('❌ No prompt provided');
            return res.status(400).json({ error: 'Prompt required' });
        }

        console.log(`📊 Expert Stream Parameters:`);
        console.log(`   - Max Tokens: ${n_predict} (Expert Mode)`);
        console.log(`   - Temperature: ${temperature}`);
        console.log(`   - Prompt: ${prompt.length} chars`);

        const params = {
            prompt,
            n_predict,
            temperature,
            top_p,
            top_k,
            repeat_penalty,
            stop,
            cache_prompt: true,
            slot_id: 0,
            n_keep: -1,
            stream: true,
            // Enhanced sampling for code generation
            min_p: 0.05,
            typical_p: 1.0,
            tfs_z: 1.0,
            mirostat: 0,
            mirostat_tau: 5.0,
            mirostat_eta: 0.1
        };

        // Setup SSE headers with optimizations
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache, no-transform');
        res.setHeader('Connection', 'keep-alive');
        res.setHeader('X-Accel-Buffering', 'no');
        res.setHeader('Transfer-Encoding', 'chunked');
        res.flushHeaders();

        console.log(`⏳ Starting expert stream...`);

        const llamaResp = await axios.post(
            `${LLAMA_URL}/completion`,
            params,
            {
                responseType: 'stream',
                timeout: 0,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                },
                maxContentLength: Infinity,
                maxBodyLength: Infinity,
                decompress: true
            }
        );

        let buffer = '';
        let totalTokens = 0;
        let lastFlush = Date.now();

        llamaResp.data.on('data', (chunk) => {
            try {
                buffer += chunk.toString();
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim() || !line.startsWith('data: ')) continue;

                    const jsonStr = line.substring(6).trim();
                    if (jsonStr === '[DONE]') continue;

                    try {
                        const data = JSON.parse(jsonStr);
                        if (data.content) {
                            totalTokens++;
                            res.write(`data: ${JSON.stringify({ content: data.content })}\n\n`);

                            // Force flush every 100ms for better streaming
                            const now = Date.now();
                            if (now - lastFlush > 10) {
                                res.flush();
                                lastFlush = now;
                            }
                        }
                    } catch (e) {
                        // Skip malformed JSON
                    }
                }
            } catch (e) {
                console.error('Stream processing error:', e.message);
            }
        });

        llamaResp.data.on('end', () => {
            const duration = Date.now() - startTime;
            const tokensPerSec = totalTokens > 0 ? (totalTokens / (duration / 1000)).toFixed(2) : '0';

            console.log(`✅ Expert stream complete:`);
            console.log(`   - Tokens: ${totalTokens}`);
            console.log(`   - Duration: ${(duration / 1000).toFixed(2)}s`);
            console.log(`   - Speed: ${tokensPerSec} t/s`);
            console.log(`${'='.repeat(70)}\n`);

            logChat({
                type: 'expert_stream',
                tokens: totalTokens,
                duration,
                tokensPerSecond: tokensPerSec,
                maxTokens: n_predict
            }).catch(() => { });

            res.write('data: [DONE]\n\n');
            res.end();
        });

        llamaResp.data.on('error', (err) => {
            console.error('❌ Stream error:', err.message);
            try {
                res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
                res.end();
            } catch (e) {
                // Client disconnected
            }
        });

        // Handle client disconnect
        req.on('close', () => {
            console.log('⚠️  Client disconnected');
            llamaResp.data.destroy();
        });

    } catch (error) {
        console.error('❌ Stream setup error:', error.message);

        let statusCode = 500;
        if (error.code === 'ECONNREFUSED') {
            statusCode = 503;
        }

        console.log(`${'='.repeat(70)}\n`);

        if (!res.headersSent) {
            res.status(statusCode).json({
                error: 'Stream failed',
                message: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }
});

// LEGACY COMPLETION ENDPOINT - For backward compatibility
app.post('/completion', async (req, res) => {
    const startTime = Date.now();
    console.log(`\n${'='.repeat(70)}`);
    console.log(`[${new Date().toISOString()}] 🚀 Completion Request`);

    try {
        const {
            prompt,
            n_predict = 8000,
            temperature = 0.75,
            top_p = 0.95,
            top_k = 60,
            repeat_penalty = 1.18,
            stop = ['\nUSER:', 'USER:', '\n\nUSER:'],
            min_p = 0.06,
            typical_p = 1.0,
            tfs_z = 1.0
        } = req.body;

        if (!prompt) {
            console.error('❌ No prompt provided');
            return res.status(400).json({
                error: 'Prompt is required',
                content: 'Please provide a prompt'
            });
        }

        console.log(`📊 Parameters:`);
        console.log(`   - Max Tokens: ${n_predict}`);
        console.log(`   - Temperature: ${temperature}`);
        console.log(`   - Prompt Length: ${prompt.length} chars`);

        const params = {
            prompt,
            n_predict,
            temperature,
            top_p,
            top_k,
            repeat_penalty,
            min_p,
            typical_p,
            tfs_z,
            stop,
            cache_prompt: true,
            slot_id: 0,
            n_keep: -1,
            stream: false
        };

        console.log(`⏳ Sending to llama-server...`);

        const response = await axios.post(
            `${LLAMA_URL}/completion`,
            params,
            {
                timeout: 600000, // 10 minutes for large generations
                headers: {
                    'Content-Type': 'application/json',
                    'Connection': 'keep-alive'
                },
                maxContentLength: Infinity,
                maxBodyLength: Infinity,
                validateStatus: (status) => status < 500
            }
        );

        const duration = Date.now() - startTime;

        if (response.status !== 200) {
            throw new Error(`Llama server returned status ${response.status}`);
        }

        const content = response.data.content || response.data.completion || '';
        const tokens = response.data.tokens_predicted || response.data.tokens_evaluated || 0;
        const tokensPerSec = tokens > 0 ? (tokens / (duration / 1000)).toFixed(2) : '0';

        console.log(`✅ Complete:`);
        console.log(`   - Tokens: ${tokens}`);
        console.log(`   - Duration: ${(duration / 1000).toFixed(2)}s`);
        console.log(`   - Speed: ${tokensPerSec} t/s`);
        console.log(`${'='.repeat(70)}\n`);

        await logChat({
            type: 'completion',
            promptLength: prompt.length,
            responseLength: content.length,
            tokens,
            duration,
            tokensPerSecond: tokensPerSec
        });

        res.json({
            content: content,
            tokens_predicted: tokens,
            timings: {
                predicted_per_second: parseFloat(tokensPerSec)
            }
        });

    } catch (error) {
        const duration = Date.now() - startTime;
        console.error(`❌ Error after ${duration}ms:`, error.message);

        let errorMessage = 'Request failed';
        let errorDetails = error.message;
        let statusCode = 500;

        if (error.code === 'ECONNREFUSED') {
            errorMessage = 'Cannot connect to llama-server';
            errorDetails = `llama-server is not running on port ${LLAMA_PORT}. Start with: python run_codeforge.py`;
            statusCode = 503;
        } else if (error.code === 'ETIMEDOUT' || error.code === 'ECONNRESET') {
            errorMessage = 'Request timeout';
            errorDetails = 'Generation took too long. Try a simpler request.';
            statusCode = 504;
        }

        console.error(`   Type: ${errorMessage}`);
        console.error(`   Details: ${errorDetails}`);
        console.log(`${'='.repeat(70)}\n`);

        res.status(statusCode).json({
            error: errorMessage,
            message: errorDetails,
            content: `Error: ${errorDetails}`,
            timestamp: new Date().toISOString()
        });
    }
});

// Stats endpoint
app.get('/stats', async (req, res) => {
    try {
        const files = await fs.readdir(LOG_DIR).catch(() => []);
        const logFiles = files.filter(f => f.endsWith('.jsonl'));

        let totalRequests = 0;
        let totalTokens = 0;
        let totalDuration = 0;
        let expertRequests = 0;

        for (const file of logFiles) {
            try {
                const content = await fs.readFile(path.join(LOG_DIR, file), 'utf-8');
                const logs = content.split('\n')
                    .filter(Boolean)
                    .map(line => {
                        try {
                            return JSON.parse(line);
                        } catch {
                            return null;
                        }
                    })
                    .filter(Boolean);

                totalRequests += logs.length;
                totalTokens += logs.reduce((sum, log) => sum + (log.tokens || 0), 0);
                totalDuration += logs.reduce((sum, log) => sum + (log.duration || 0), 0);
                expertRequests += logs.filter(log => log.type === 'expert_stream').length;
            } catch (err) {
                // Skip corrupted files
            }
        }

        res.json({
            totalRequests,
            expertRequests,
            totalTokens,
            totalDuration: Math.round(totalDuration / 1000),
            averageTokensPerRequest: totalRequests > 0 ? Math.round(totalTokens / totalRequests) : 0,
            averageDuration: totalRequests > 0 ? Math.round(totalDuration / totalRequests / 1000) : 0,
            averageSpeed: totalDuration > 0 ? (totalTokens / (totalDuration / 1000)).toFixed(2) : 0
        });

    } catch (error) {
        console.error('Stats error:', error.message);
        res.status(500).json({ error: 'Failed to fetch stats' });
    }
});

// Check llama server connectivity
async function checkLlamaServer() {
    try {
        const response = await axios.get(`${LLAMA_URL}/health`, { timeout: 5000 });
        return response.status === 200;
    } catch (error) {
        return false;
    }
}

// NEW: Code analysis endpoint - Security, performance, and architecture scoring
app.post('/analyze-code', async (req, res) => {
    try {
        const { code, mode = 'architect' } = req.body;
        
        const analysis = {
            codeQuality: analyzeCodeQuality(code),
            security: analyzeSecurityMetrics(code),
            performance: analyzePerformanceMetrics(code),
            architecture: analyzeArchitecture(code, mode),
            issues: findCodeIssues(code),
            coverage: estimateTestCoverage(code)
        };

        res.json(analysis);
    } catch (error) {
        console.error('Analysis error:', error);
        res.status(500).json({ error: 'Analysis failed' });
    }
});

// Code Quality Analysis
function analyzeCodeQuality(code) {
    let score = 50;
    const lines = code.split('\n').length;

    // Length assessment
    if (lines > 1000) score += 10;
    if (lines > 500) score += 5;

    // Complexity & style
    if ((code.match(/function /g) || []).length > 5) score += 10;
    if ((code.match(/class /g) || []).length > 1) score += 10;
    if ((code.match(/\/\//g) || []).length > lines / 10) score += 15; // Comment ratio

    // Type safety
    if ((code.match(/:\s*(string|number|boolean|interface|type)/g) || []).length > 10) score += 15;

    // Error handling
    if ((code.match(/try\s*{/g) || []).length > 2) score += 10;
    if ((code.match(/catch\s*\(/g) || []).length > 1) score += 10;

    return Math.min(100, score);
}

// Security Metrics
function analyzeSecurityMetrics(code) {
    const items = [];
    const hasAuth = /auth|jwt|oauth|passport/i.test(code);
    const hasEncryption = /encrypt|hash|bcrypt|crypto|aes|sha/i.test(code);
    const hasValidation = /validate|sanitize|escape|xss|sql.injection/i.test(code);
    const hasCors = /cors|origin|credentials/i.test(code);
    const hasEnv = /process\.env|config\.|environment/i.test(code);

    if (hasAuth) items.push('✅ Authentication implemented');
    else items.push('⚠️ Add authentication mechanism');

    if (hasEncryption) items.push('✅ Encryption detected');
    else items.push('⚠️ Implement encryption for sensitive data');

    if (hasValidation) items.push('✅ Input validation present');
    else items.push('⚠️ Add input validation');

    if (hasCors) items.push('✅ CORS configured');
    else items.push('⚠️ Configure CORS properly');

    if (hasEnv) items.push('✅ Environment variables used');
    else items.push('⚠️ Use environment variables for secrets');

    return { score: items.filter(i => i.startsWith('✅')).length * 20, items };
}

// Performance Metrics
function analyzePerformanceMetrics(code) {
    const items = [];
    const hasAsync = /async|await|Promise/i.test(code);
    const hasCache = /cache|redis|memcache|memoize/i.test(code);
    const hasLazyLoad = /lazy|defer|dynamic.import|code.split/i.test(code);
    const hasIndex = /index|database.*index|\.createIndex/i.test(code);
    const hasOptimization = /optimize|compress|minif|tree.shak/i.test(code);

    if (hasAsync) items.push('✅ Async/await pattern used');
    else items.push('⚠️ Use async/await for I/O operations');

    if (hasCache) items.push('✅ Caching strategy implemented');
    else items.push('⚠️ Implement caching for hot data');

    if (hasLazyLoad) items.push('✅ Lazy loading detected');
    else items.push('⚠️ Add lazy loading for large datasets');

    if (hasIndex) items.push('✅ Database indexing present');
    else items.push('⚠️ Add database indexes for queries');

    if (hasOptimization) items.push('✅ Performance optimization applied');
    else items.push('⚠️ Add performance optimizations');

    return { score: items.filter(i => i.startsWith('✅')).length * 20, items };
}

// Architecture Analysis
function analyzeArchitecture(code, mode) {
    const items = [];
    const hasModules = /export|import|module/i.test(code);
    const hasLayers = /controller|service|repository|model|api/i.test(code);
    const hasPatterns = /factory|singleton|observer|strategy|decorator/i.test(code);
    const hasSolid = /interface|abstract|dependency.injection/i.test(code);
    const hasMicroservices = /microservices|service.discovery|api.gateway/i.test(code);

    if (hasModules) items.push('✅ Modular structure');
    if (hasLayers) items.push('✅ Layered architecture');
    if (hasPatterns) items.push('✅ Design patterns applied');
    if (hasSolid) items.push('✅ SOLID principles followed');
    if (hasMicroservices && mode === 'architect') items.push('✅ Microservices architecture');

    if (!hasModules) items.push('⚠️ Improve modularity');
    if (!hasLayers) items.push('⚠️ Apply layered architecture');

    return { score: items.filter(i => i.startsWith('✅')).length * 25, items };
}

// Find Code Issues
function findCodeIssues(code) {
    const issues = [];
    
    // Common issues
    if (/var\s+\w+\s*=/g.test(code)) issues.push('Use const/let instead of var');
    if (/console\.log/g.test(code)) issues.push('Remove console.log in production');
    if (/\/\/ TODO|\/\/ FIXME/i.test(code)) issues.push('Resolve TODO/FIXME comments');
    if (/any\s*[,)]/g.test(code)) issues.push('Avoid TypeScript "any" type');
    if (/==\s*(?!==)/g.test(code)) issues.push('Use === instead of ==');
    if (/catch\s*\(\s*\)/.test(code)) issues.push('Handle caught errors');
    if (/Math\.random\(\).*token|session|id/i.test(code)) issues.push('Use cryptographic RNG for security');

    return issues.slice(0, 5); // Top 5 issues
}

// Estimate Test Coverage
function estimateTestCoverage(code) {
    const hasTests = /test|spec|describe|it\(/i.test(code);
    const testCount = (code.match(/it\(|test\(/g) || []).length;
    return hasTests ? `Includes ${testCount} test cases` : 'Add unit tests';
}

// Graceful shutdown
function gracefulShutdown() {
    console.log('\n\n🛑 Shutting down gracefully...');
    process.exit(0);
}

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// Start server
async function startServer() {
    await ensureLogDir();

    // ---------------------- PROJECT GENERATOR ENDPOINT ----------------------
    const { exec } = require("child_process");

    app.post("/generate-project", (req, res) => {
        const { projectType, projectName, minLines } = req.body;

        console.log("Incoming Project Generator Request:", req.body);

        const cmd = `python project_generator.py ${projectType} ${projectName} --min-lines ${minLines}`;

        exec(cmd, { cwd: "./" }, (error, stdout, stderr) => {
            if (error) {
                console.error("GENERATOR ERROR:", error);
                return res.status(500).json({ error: String(error) });
            }

            console.log("GENERATOR OUTPUT:", stdout);
            res.json({ success: true, output: stdout });
        });
    });


    const server = app.listen(PORT, async () => {
        console.log('\n' + '='.repeat(70));
        console.log('  ⚡ CodeForge Pro Server v2.5 - EXPERT EDITION');
        console.log('='.repeat(70));
        console.log(`\n  📡 Port: ${PORT}`);
        console.log(`  🧠 Llama: ${LLAMA_URL}`);
        console.log(`  📁 Logs: ${LOG_DIR}`);
        console.log(`\n  ✨ Expert Features:`);
        console.log(`     ✅ High-volume streaming (24K+ tokens)`);
        console.log(`     ✅ Production code generation`);
        console.log(`     ✅ Advanced debugging capabilities`);
        console.log(`     ✅ Split-view interface support`);
        console.log(`     ✅ Optimized sampling parameters`);
        console.log(`\n  🌐 Access: http://localhost:${PORT}`);
        console.log('\n' + '='.repeat(70));

        console.log('\n  🔍 Checking llama-server...');
        const llamaRunning = await checkLlamaServer();
        if (llamaRunning) {
            console.log('  ✅ Llama server: Connected & Ready');
        } else {
            console.log('  ⚠️  WARNING: Cannot connect to llama-server');
            console.log('  ⚠️  Start with: python run_codeforge.py');
        }
        console.log('\n' + '='.repeat(70) + '\n');
    });

    // Extended timeouts for large code generation
    server.timeout = 600000; // 10 minutes
    server.keepAliveTimeout = 610000;
    server.headersTimeout = 620000;
}

startServer();