# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\..\\VS_ModsUpdater.py'],
    pathex=[],
    binaries=[],
datas=[
    ('vintagestory.ico', '.'),  
    ('file_version_info.txt', '.'),
],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VS_ModsUpdater',
	icon='vintagestory.ico',
    version='file_version_info.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
