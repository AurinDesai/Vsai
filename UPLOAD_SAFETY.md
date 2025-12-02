# Upload Safety - Folder Selection Feature

## Problem
Previously, when uploading a folder, all files were saved directly to the **project root** directory. This caused issues when a user accidentally uploaded a large project (like `node_modules`), mixing thousands of files with the core CodeForge files.

## Solution
**New Folder Selection Dialog** - Users must now specify a destination folder before uploading:

### How It Works

1. **Click "Add Existing Folder (Upload)"** from the File menu
2. **Enter destination folder** (e.g., `imports`, `my_project`)
   - If blank, a confirmation dialog appears warning about root upload
   - Default suggestion: `imports` folder
3. **Select files** from your computer
4. **Files upload to the specified folder**, not the project root

### Safe Upload Examples

✅ **Good** - Upload to `imports/react-app/`:
```
/imports/
  /react-app/
    package.json
    src/
    public/
    ...
```

✅ **Good** - Upload to `projects/data-analysis/`:
```
/projects/
  /data-analysis/
    dataset.csv
    analysis.py
    ...
```

❌ **Bad** - Upload to root (now requires confirmation):
```
/                          ← Mixes with CodeForge files
  codeforge_server.js
  vscode_clone.html
  node_modules/            ← Could be thousands of files!
  ...
```

### Technical Changes

**Frontend (`vscode_clone.html`):**
- Added prompt dialog asking for destination folder
- Added warning confirmation if user selects empty (root)
- Passes `targetFolder` parameter to server

**Backend (`codeforge_studio_server.js`):**
- `/api/upload-folder` endpoint now accepts `targetFolder` parameter
- Constructs paths as: `PROJECT_ROOT / targetFolder / relPath`
- Files are isolated in their specified folder

### Recommendations

1. **Create a folder first** (optional but recommended):
   - File → New Folder → name it `imports`
   - Then upload projects into `imports/project-name/`

2. **Organize by project type**:
   ```
   /uploads/
     /react-apps/
     /python-projects/
     /data-files/
   ```

3. **Avoid root uploads** - Always specify a destination folder

## Preventing Future Mistakes

The upload dialog now:
- ✅ Defaults to `imports` folder (safer option)
- ✅ Shows a warning if you try to use root
- ✅ Requires explicit confirmation for root upload
- ✅ Keeps CodeForge project files clean and isolated

## Cleanup After Accidental Upload

If files are accidentally in the root directory:

**Option 1:** Delete manually
- Select files in the file explorer
- Right-click → Delete

**Option 2:** Move to correct folder
- Create destination folder: File → New Folder
- Move files: Cut/Paste via editor

**Option 3:** Start fresh
- Create a new subfolder (e.g., `imports/`)
- Re-upload files to the correct location
