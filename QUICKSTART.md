# 🚀 CodeForge Studio - Quick Start Guide

## One-Click Startup

### For Users (Easiest Way)

**Step 1:** Download and extract CodeForge Studio

**Step 2:** Run one of these:

#### Option A: Python Script (Recommended)
```
Double-click: start.py
```

#### Option B: Batch File (Windows)
```
Double-click: start.bat
```

#### Option C: Standalone Executable
```
1. Run: build.bat
2. Double-click: dist/CodeForge Studio.exe
```

### Step 3: Wait for Startup
- First time: 1-3 minutes (loading model)
- Subsequent: 10-30 seconds
- Browser opens automatically

### Step 4: Set Authentication
1. Right panel → Click "Set Auth Token"
2. Enter: `localdev`
3. Click OK

## 🎯 What Happens When You Start

```
[1/3] Checking environment
      ✅ Python 3.14.0
      ✅ Node.js v24.11.0
      ✅ Model: 2.75GB

[2/3] Starting Llama Server
      🚀 Loading AI model (port 8000)
      ⏳ This may take a minute...
      ✅ Llama ready!

[3/3] Starting Node.js Backend
      🚀 Backend starting (port 5050)
      ✅ Backend ready!

🎉 All systems ready!
🌐 Browser opens automatically
```

## 💻 System Requirements

### Minimum
- Windows 7+ / Mac / Linux
- Python 3.8+
- Node.js 18+
- 4GB RAM
- 3GB free disk space

### Recommended
- Windows 10+
- Python 3.10+
- Node.js 20+
- 8GB+ RAM
- NVIDIA GPU (faster code generation)
- 10GB free disk space

## 🖥️ Files Created

```
codeforge-ai/
├── start.py               ← Use this! (all-in-one startup)
├── start.bat              ← Or this on Windows
├── build.bat              ← Build standalone exe
├── launcher.py            ← Windows app launcher
├── README.md              ← Full documentation
└── Other files...
```

## ❓ Troubleshooting

### Issue: "Python not found"
**Fix:** Install Python from https://python.org (check "Add to PATH")

### Issue: "Node.js not found"
**Fix:** Install Node from https://nodejs.org

### Issue: "Llama still loading" (stuck)
**Fix:** Normal first startup. Wait 2-3 minutes for model to load.

### Issue: "Address already in use"
**Fix:** Another app using port 8000 or 5050. Close it and try again.

### Issue: Browser doesn't open
**Fix:** Manually open: http://localhost:5050/vscode_clone.html

## 🎮 Using CodeForge Studio

### Edit Files
1. Click files in left panel (Explorer)
2. Edit in center editor
3. Auto-saves with backup

### Chat with AI
1. Type in right panel (Chat)
2. Choose mode: Chat / Code / Refactor / Explain
3. Press Enter
4. AI responds in real-time

### Save & Commit
1. Right-click file → Save
2. Or use Git (🌿 icon)
3. Type commit message
4. Click Commit

### Share Code
1. Click 🌿 icon (Source Control)
2. Click "Share Repository"
3. Enter partner folder path
4. Click Share

## 📦 Building Standalone Windows App

To create a .exe file that works anywhere:

```
1. Run: build.bat
2. Wait 1-2 minutes
3. Result: dist/CodeForge Studio.exe
4. Can run standalone on any Windows PC
```

## 🚀 Performance Tips

### Faster Startup
- Keep app running (servers stay loaded)
- Second startup is much faster
- Model caches after first load

### Faster Code Generation
- Use GPU (NVIDIA GPU recommended)
- Shorter prompts generate faster
- Use "Chat" mode for quick responses

### Smooth Editing
- Close unused tabs
- Limit large file sizes
- Restart if UI gets slow

## 🔐 Security Notes

- Admin token is `localdev` for development
- For production: change the token
- Don't expose to untrusted networks
- Use VPN or local-only for sensitive code

## 📚 File Locations

### Settings
- Model: `./models/deepseek-coder-6.7b-instruct-Q3_K_S.gguf`
- Server: `codeforge_studio_server.js`
- Frontend: `vscode_clone.html`

### Ports
- Llama AI: Port 8000
- Web Backend: Port 5050
- Browser: http://localhost:5050/vscode_clone.html

## 💡 Tips & Tricks

### Keyboard Shortcuts
- `Enter` (in chat) - Send message
- `Ctrl+S` - Save file (in editor)
- `Ctrl+Tab` - Switch tabs
- `Ctrl+/` - Comment code

### AI Features
- **Chat Mode** - General questions
- **Code Mode** - Generate code
- **Refactor Mode** - Improve code
- **Explain Mode** - Understand code

### File Operations
- New File - Type in Explorer
- New Folder - Right-click Explorer
- Delete - Right-click file
- Rename - Double-click name

## 🆘 Getting Help

1. **Check README.md** - Full documentation
2. **View browser console** - Press F12 for errors
3. **Check terminal** - Error messages appear there
4. **Restart application** - Close and run start.py again

## 🎉 You're Ready!

Just run `python start.py` and you're good to go!

Happy coding! 🚀
