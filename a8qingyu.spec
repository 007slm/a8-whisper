# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

# Collect compiled frontend and assets
datas = [
    ('src/assets', 'src/assets'),
    ('gui_web/dist', 'gui_web/dist'),  # Include built frontend
]

# Fix: setuptools/jaraco.text needs Lorem ipsum.txt
# Using absolute path to ensure certainty
jaraco_file = r'e:\a8-turbo\whisper\.venv\Lib\site-packages\setuptools\_vendor\jaraco\text\Lorem ipsum.txt'

if os.path.exists(jaraco_file):
    print(f"SUCCESS: Found jaraco text resource at: {jaraco_file}")
    # Add to multiple locations to cover PyInstaller _internal structure changes
    datas.append((jaraco_file, 'setuptools/_vendor/jaraco/text'))
    datas.append((jaraco_file, '_internal/setuptools/_vendor/jaraco/text'))
else:
    print(f"WARNING: Could not find jaraco file at {jaraco_file}. Trying relative search...")
    # Fallback usually not needed if verify succeeds
    pass

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
    'src.ui.native_overlay.manager'
]

# Manual collection of llama_cpp libraries
from PyInstaller.utils.hooks import get_package_paths
import os
try:
    datas.append(('.venv/Lib/site-packages/llama_cpp/lib', 'llama_cpp/lib'))
except:
    pass

a = Analysis(
    ['src\\\\main_webview.py'],
    pathex=[],
    # Manually collect zlibwapi.dll from torch (needed for cudnn)
    binaries=[
       ('.venv/Lib/site-packages/torch/lib/zlibwapi.dll', '.') 
    ],
    datas=datas,
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
