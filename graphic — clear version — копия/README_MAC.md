# macOS Migration Guide for Scientific Visualization Project

This guide will help you migrate your project from Windows to macOS 12 (Monterey) or later.

---

## Prerequisites

- **macOS**: 12 (Monterey) or later
- **Python**: 3.8 or higher (check with `python3 --version`)
- **USB drive**: For transferring project files
- **Disk space**: At least 1GB free (including ~330MB of generated graphs)

---

## Step 1: Transfer Files from Windows to Mac

### On Windows Machine:
1. Copy the entire `D:\graphic` folder to your USB flash drive
2. Verify that all files are copied (~330MB in `output/` folder + source code)
3. Safely eject the USB drive

### On Mac:
1. Insert the USB drive
2. Create a project directory (choose one):
   ```bash
   mkdir -p ~/Documents/graphic
   # OR
   mkdir -p ~/Projects/graphic
   ```
3. Copy all files from USB to your chosen directory:
   ```bash
   cp -R /Volumes/YOUR_USB_NAME/graphic/* ~/Documents/graphic/
   ```
4. Navigate to the project folder:
   ```bash
   cd ~/Documents/graphic
   ```

---

## Step 2: Set Up Python Virtual Environment

It's highly recommended to use a virtual environment to avoid dependency conflicts.

```bash
# Navigate to project directory
cd ~/Documents/graphic

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your terminal prompt should now show (venv) prefix
```

**Important:** Always activate the virtual environment before working on the project:
```bash
source venv/bin/activate
```

To deactivate when done:
```bash
deactivate
```

---

## Step 3: Install Dependencies

With the virtual environment activated:

```bash
# Upgrade pip to the latest version
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

This will install:
- numpy (numerical computing)
- scipy (scientific computing, ODE solvers)
- sympy (symbolic mathematics)
- matplotlib (plotting)
- pandas (data processing)
- openpyxl (Excel file support)
- PyYAML (configuration files)

**Verification:**
```bash
python3 -c "import numpy, scipy, sympy, matplotlib, pandas, yaml; print('All dependencies installed successfully!')"
```

---

## Step 4: Fix Font Issues (if needed)

The project uses **Times New Roman** font, which may not be available on macOS.

### Option A: Use Default Serif Font (Recommended)

No action needed - matplotlib will automatically fall back to a similar serif font.

### Option B: Use the macOS-Compatible Version

If you experience font warnings or rendering issues:

1. A macOS-compatible version is provided: `core/base_plotter_mac.py`
2. This version uses `DejaVu Serif` instead of `Times New Roman`
3. To use it, you would need to temporarily rename files (but **don't modify original files**):

```bash
# Backup original (optional)
cp core/base_plotter.py core/base_plotter_windows.py

# Use macOS version
cp core/base_plotter_mac.py core/base_plotter.py
```

### Option C: Install Times New Roman on macOS

1. Download Times New Roman font files (.ttf)
2. Open Font Book application (Applications → Font Book)
3. Drag and drop the font files into Font Book
4. Restart your terminal

---

## Step 5: Test the Project

### Test 1: Simple Function Plot
```bash
python3 main.py --config configs/example_function.yaml
```

Expected output:
```
График создан: output/example_function.svg
```

### Test 2: ODE Time Series
```bash
python3 main.py --config configs/example_ode_time.yaml
```

### Test 3: Phase Portrait
```bash
python3 main.py --config configs/example_phase_portrait.yaml
```

### Test 4: Excel Batch Processing
```bash
python3 main.py --config test_excel/test_basic.yaml
```

**Check results:**
```bash
ls -lh output/
# Should show newly created SVG files
```

---

## Step 6: IDE Setup (Optional)

### Visual Studio Code:
1. Install Python extension
2. Open the project folder: `File → Open Folder → ~/Documents/graphic`
3. Select the virtual environment:
   - Press `Cmd+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose `./venv/bin/python`

### PyCharm:
1. Open the project folder
2. Go to `Preferences → Project → Python Interpreter`
3. Click gear icon → Add
4. Select "Existing environment"
5. Navigate to `~/Documents/graphic/venv/bin/python`

---

## Common Issues and Solutions

### Issue 1: Permission Denied when Saving Graphs

**Symptom:** Error when trying to save to `output/` folder

**Solution:**
```bash
chmod -R 755 output/
```

### Issue 2: "No module named 'X'" Error

**Symptom:** Import errors when running scripts

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 3: Matplotlib Backend Error

**Symptom:** GUI-related errors

**Solution:** Already handled in code - the project uses `matplotlib.use('Agg')` which works headlessly on all platforms.

### Issue 4: Multiprocessing Issues

**Symptom:** Parallel processing not working

**Solution:** Already handled - the code has proper `if __name__ == '__main__':` blocks.

---

## What Works Out of the Box

✅ **File paths** - All paths use `os.path.join()`, compatible with macOS
✅ **Matplotlib backend** - Non-GUI 'Agg' backend works on all platforms
✅ **Multiprocessing** - Proper guards for Windows/macOS compatibility
✅ **Excel processing** - pandas and openpyxl work identically on macOS
✅ **SVG output** - Vector graphics format is platform-independent

---

## Performance Notes

- macOS version should have **similar or better performance** than Windows
- If using M1/M2 Mac (Apple Silicon):
  - NumPy/SciPy are optimized for ARM architecture
  - Expect 20-30% faster numerical computations
- Multiprocessing will use all available CPU cores

---

## Directory Structure

After migration, your project should look like:

```
~/Documents/graphic/
├── main.py                      # Main entry point
├── params_global.py             # Global configuration
├── requirements.txt             # Dependencies (NEW)
├── README_MAC.md               # This file (NEW)
├── MIGRATION_INSTRUCTIONS.txt   # Quick guide (NEW)
├── core/
│   ├── base_plotter.py         # Original (Windows)
│   ├── base_plotter_mac.py     # macOS version (NEW)
│   ├── function_plotter.py
│   ├── ode_plotter.py
│   └── function_wrapper.py
├── models/
│   └── ode_system.py
├── utils/
│   ├── validators.py
│   ├── config_loader.py
│   ├── config_merger.py
│   ├── excel_loader.py
│   └── equilibrium_finder.py
├── configs/                     # 28 YAML configuration files
├── output/                      # Generated graphs (~330MB)
├── test_excel/                  # Excel test files
└── venv/                        # Virtual environment (created by you)
```

---

## Additional Tips

1. **Backup your work:** Consider setting up Git for version control
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Windows to macOS migration"
   ```

2. **Use .gitignore:** If using Git, create a `.gitignore` file:
   ```
   venv/
   __pycache__/
   *.pyc
   .DS_Store
   output/*.svg
   output/*.png
   ```

3. **Monitor resources:** Use Activity Monitor to check CPU/memory usage during batch processing

4. **Update regularly:** Keep dependencies updated
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## Getting Help

If you encounter issues:

1. Check this README for common solutions
2. Read `MIGRATION_INSTRUCTIONS.txt` for quick reference
3. Review the original Russian documentation:
   - `Документация к проекту дополненная.txt`
   - `Документация к проекту.txt`

---

## Summary

Your project is **highly compatible** with macOS. The only potential issue is font rendering, which has easy solutions. All core functionality (ODE solving, plotting, Excel processing, parallelization) will work identically on macOS.

**Estimated setup time:** 10-15 minutes

Good luck with your coursework! 🎓
