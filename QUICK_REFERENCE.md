# CodeForge Studio - Quick Reference

## 🚀 Getting Started

### 1. Start the Server
```powershell
python start_codeforge.py
```
Or double-click: `start_codeforge.bat`

### 2. Authenticate
- Click "Set Token" in AI panel (right side)
- Enter: `localdev`
- Status changes to ✅

### 3. Create or Load Files
- **New File:** File → New File
- **Upload Folder:** File → Add Existing Folder (Upload)
  - Choose destination folder (e.g., `imports`)
  - Select files
  - ✅ Safe upload!

---

## 💻 Editor Features

| Keyboard | Action |
|----------|--------|
| **Ctrl+P** | Fuzzy file search |
| **Ctrl+S** | Save current file |
| **Ctrl+//** | Toggle comment |
| **Ctrl+Enter** | Send AI message |
| **Shift+Enter** | New line in chat |

## 🎨 UI Layout

```
┌─────────────────────────────────────────────┐
│ File Edit Selection View Go Run             │  ← Menu Bar
├────┬───────────────────────┬────────────────┤
│ 📁 │ File Explorer         │  💜 CodeForge  │
│ 🔍 │ (empty at start)      │     AI         │
│ 🌿 │                       │  ⭐ Welcome   │
│ 📦 │ Create or upload      │  💬 Chat      │
│    │ files here            │  📝 Code      │
│    │                       │  🔧 Refactor  │
│    │                       │  💡 Explain   │
│    │                       │                │
│    │                       │ ⚡ Fast AI  ☑  │
│    │                       │ 🤖 Auto AI  ☐  │
│    │                       │                │
│    │                       │ [Set Token]    │
│    │                       │ [Clear]        │
├────┴───────────────────────┴────────────────┤
│  Tabs | Editor Content      | 🔒 Token: OK  │  ← Status Bar
└─────────────────────────────────────────────┘
```

---

## 🤖 AI Chat Guide

### How to Use
1. **Type a message** in the chat input (bottom right)
2. **Press Ctrl+Enter** to send
3. **Wait** for AI response (streams in real-time)
4. **Copy** code by selecting and Ctrl+C

### Chat Modes

| Mode | Use For | Example |
|------|---------|---------|
| 💬 Chat | General questions | "How do I use async/await?" |
| 📝 Code | Generate code | "Create a login form in React" |
| 🔧 Refactor | Improve code | Open file + ask "Refactor this" |
| 💡 Explain | Understand code | "Explain what this function does" |

### Features
- **Fast AI ⚡:** Quick responses (shorter context)
- **Auto AI 🤖:** Disabled by default
- **Code Highlighting:** Syntax highlighting in responses
- **File Context:** AI sees current file content

---

## 📁 Safe File Upload

### Step-by-Step
1. Click **File → Add Existing Folder (Upload)**
2. Enter folder name (suggestions: `imports`, `projects`, `data`)
3. Select files from your computer
4. Upload happens to: `/your-folder-name/`
5. ✅ Root stays clean!

### Examples
```
✅ Good:  /imports/my-project/
❌ Bad:   /  (root - now asks for confirmation)
✅ Good:  /projects/react-app/
✅ Good:  /uploads/data-files/
```

---

## 🎯 Common Tasks

### Create a New Project
```
1. File → New Folder
2. Enter: "my-project"
3. File → New File
4. Enter: "my-project/index.js"
5. Start coding!
```

### Upload an Existing Project
```
1. File → Add Existing Folder (Upload)
2. Enter: "my-uploaded-project"
3. Select all files from your project
4. Click upload
5. Files appear in explorer
```

### Generate Code
```
1. Chat mode: "📝 Code"
2. Ask: "Create a Python function that..."
3. Copy response
4. Create new file
5. Paste code
6. Edit as needed
```

### Understand Code
```
1. Open a file
2. Chat mode: "💡 Explain"
3. Ask: "What does this function do?"
4. AI explains with examples
```

---

## ⚙️ Settings

### Authentication
- **Token:** `localdev` (default)
- **Storage:** Browser localStorage
- **Persistence:** Saves between sessions
- **Reset:** Click "Clear" button

### Auto-Save
- **Enabled by default**
- **Toggle:** Autosave checkbox in UI
- **Saves:** Every change (if enabled)

### Fast AI Mode
- **Reduces token limit** for quick responses
- **Useful for:** Coding questions, quick fixes
- **Toggle:** ⚡ Fast AI checkbox

---

## 🐛 Troubleshooting

### No Files Showing in Explorer
- ✅ Normal at startup (we disabled auto-load)
- Create a file: **File → New File**
- Or upload: **File → Add Existing Folder**

### AI Not Responding
- Check token: Click "Set Token" → confirm `localdev`
- Check if Llama server running (optional)
- Try **⚡ Fast AI** mode for faster response
- Check browser console for errors (F12)

### Upload Files to Root Accidentally
- Don't worry! Just move them:
  - Create a folder: **File → New Folder**
  - Move files manually
  - Or re-upload to correct folder

### Can't Save File
- Check token is set
- Check file path is valid
- Try: **File → Save** (Ctrl+S)

---

## 📚 File Manager

### Sidebar Actions
| Action | How |
|--------|-----|
| **New File** | File menu or + button |
| **New Folder** | File menu or 📁 button |
| **Open File** | Click in explorer |
| **Delete File** | Right-click (future) |
| **Search Files** | Ctrl+P or 🔍 icon |

### File Organization
```
Project/
├── imports/          ← Upload external projects here
│   ├── lib-name/
│   └── another-lib/
├── src/              ← Your code
│   ├── index.js
│   └── utils.js
└── data/             ← Data files
    └── config.json
```

---

## 🎮 Editor Tips

### Split Editor
- **Split Right:** View 2 files side-by-side
- **Split Down:** Vertical split
- **Close Split:** Click X button

### Fuzzy Search (Ctrl+P)
- Start typing file name
- Arrow keys to navigate
- Enter to open
- Esc to close

### Syntax Highlighting
- **Automatic** by file extension
- Supports: JS, Python, Java, C++, Go, Rust, PHP, Ruby, HTML, CSS, JSON, YAML, SQL, and more!

---

## 🔗 Useful Links

- **Home:** http://localhost:5050/vscode_clone.html
- **API Docs:** See server console
- **Help:** Ask CodeForge AI!

---

## 💡 Pro Tips

1. **Use folders for organization:** uploads/, projects/, src/, data/
2. **Set token once:** Saved in browser, persists between sessions
3. **Use chat modes:** Different mode = better AI responses
4. **Enable Fast AI:** For quick questions (faster, less context)
5. **Read AI responses carefully:** Copy-paste and test code
6. **Use Ctrl+P:** Search faster than scrolling explorer

---

## 📞 Support

**Having issues?**
1. Check troubleshooting section above
2. Ask CodeForge AI (💬 Chat mode)
3. Check browser console (F12 → Console tab)
4. Restart server: Ctrl+C then `python start_codeforge.py`

---

**Last Updated:** December 2, 2025
**Version:** CodeForge Studio v1.0
