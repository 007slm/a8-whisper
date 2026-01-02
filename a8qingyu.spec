# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_all, collect_submodules
import os

# 完整收集 numpy 模块以避免重复加载问题
numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')
print(f"Collected {len(numpy_hiddenimports)} numpy hidden imports")

# Fix: Collect ctranslate2 and faster_whisper to ensure DLLs and dependencies are included
ct2_datas, ct2_binaries, ct2_hiddenimports = collect_all('ctranslate2')
print(f"Collected {len(ct2_hiddenimports)} ctranslate2 hidden imports")

fw_datas, fw_binaries, fw_hiddenimports = collect_all('faster_whisper')
print(f"Collected {len(fw_hiddenimports)} faster_whisper hidden imports")

# Collect compiled frontend and assets
datas = [
    ('src/assets', 'src/assets'),
    ('gui_web/dist', 'gui_web/dist'),  # Include built frontend
]

# Fix: setuptools/jaraco.text needs Lorem ipsum.txt
# Use dynamic path detection instead of hardcoded path
jaraco_files = []
try:
    # Try multiple possible locations
    possible_paths = [
        os.path.join('.venv', 'Lib', 'site-packages', 'setuptools', '_vendor', 'jaraco', 'text', 'Lorem ipsum.txt'),
        os.path.join('.venv', 'lib', 'python3.11', 'site-packages', 'setuptools', '_vendor', 'jaraco', 'text', 'Lorem ipsum.txt'),
        # Add more paths as needed
    ]
    
    for jaraco_path in possible_paths:
        if os.path.exists(jaraco_path):
            print(f"SUCCESS: Found jaraco text resource at: {jaraco_path}")
            # Add to multiple locations to cover PyInstaller _internal structure changes
            datas.append((jaraco_path, 'setuptools/_vendor/jaraco/text'))
            datas.append((jaraco_path, '_internal/setuptools/_vendor/jaraco/text'))
            jaraco_files.append(jaraco_path)
            break
    
    if not jaraco_files:
        print("WARNING: Could not find jaraco Lorem ipsum.txt file. This may cause runtime issues.")
        
except Exception as e:
    print(f"WARNING: Error searching for jaraco files: {e}")

# Fix: Add setuptools/_vendor to pathex to support 'backports' module used by jaraco
extra_pathex = []
try:
    vendor_path = os.path.join('.venv', 'Lib', 'site-packages', 'setuptools', '_vendor')
    if os.path.exists(vendor_path):
        print(f"Adding vendor path to pathex: {vendor_path}")
        extra_pathex.append(os.path.abspath(vendor_path))
    else:
        # Fallback for other environments or global install
        print("WARNING: setuptools/_vendor not found, checking standard paths...")
except Exception as e:
    print(f"Error checking vendor path: {e}")

# Hidden imports for system components
hiddenimports = [
    'pystray',
    'PIL', 
    'PIL.Image',
    'PIL.ImageDraw',
    'json',
    'threading',
    'src.ui.native_overlay',
    'src.ui.native_overlay.qt_overlay',
    'src.ui.native_overlay.manager',
    # 修复 jaraco.context 依赖问题
    'jaraco.context',
    'jaraco.functools',
    'jaraco.text',
    'importlib_metadata',
    'importlib_resources',
    # 修复 setuptools 相关问题
    'setuptools._vendor.jaraco.text',
    'setuptools._vendor.jaraco.context',
    'setuptools._vendor.importlib_metadata',
]

# 合并 hidden imports
hiddenimports.extend(numpy_hiddenimports)
hiddenimports.extend(ct2_hiddenimports)
hiddenimports.extend(fw_hiddenimports)

# Manual collection of llama_cpp libraries
from PyInstaller.utils.hooks import get_package_paths
import os

# Try to collect torch zlibwapi.dll if available (optional)
torch_binaries = []
try:
    torch_lib_path = os.path.join('.venv', 'Lib', 'site-packages', 'torch', 'lib', 'zlibwapi.dll')
    if os.path.exists(torch_lib_path):
        torch_binaries.append((torch_lib_path, '.'))
        print(f"Found torch zlibwapi.dll at: {torch_lib_path}")
    else:
        print("torch zlibwapi.dll not found, skipping...")
except Exception as e:
    print(f"Could not locate torch binaries: {e}")

# Try to collect llama_cpp libraries if available (optional)
try:
    llama_cpp_lib_path = os.path.join('.venv', 'Lib', 'site-packages', 'llama_cpp', 'lib')
    if os.path.exists(llama_cpp_lib_path):
        datas.append((llama_cpp_lib_path, 'llama_cpp/lib'))
        print(f"Found llama_cpp lib at: {llama_cpp_lib_path}")
except Exception as e:
    print(f"Could not locate llama_cpp libraries: {e}")

a = Analysis(
    ['src/main_webview.py'],
    pathex=extra_pathex,
    # Use dynamic torch binaries (may be empty if torch not available)
    # Use dynamic torch binaries (may be empty if torch not available)
    binaries=torch_binaries + numpy_binaries + ct2_binaries + fw_binaries,
    datas=datas + numpy_datas + ct2_datas + fw_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclude heavy/unused packages to speed up analysis
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'unittest', 'pdb', 'pydoc', 'torch',
        'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebChannel',
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput',
        'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning',
        'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtSql',
        'PySide6.QtTest', 'PySide6.QtXml',
        'IPython', 'jupyter', 'notebook', 'pytest',
        'black', 'flake8', 'mypy', 'pylint',
        # 排除可能导致冲突的模块
        'numpy.distutils',
        'numpy.f2py',
        'numpy.testing',
    ],
    noarchive=False,
    optimize=0, # Must be 0 for numpy (needs docstrings)
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='A8轻语',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Hide console for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    entitlements_file=None,
    icon='src/assets/icon.ico', 
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='A8轻语',
)
