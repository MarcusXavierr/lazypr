# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import copy_metadata

# Bundle package metadata for packages that call importlib.metadata.version()
pkg_metadata = (
    copy_metadata('genai_prices') +
    copy_metadata('pydantic_ai') +
    copy_metadata('pydantic_ai_slim') +
    copy_metadata('pydantic') +
    copy_metadata('pydantic_core')
)

a = Analysis(
    ['src/lazypr/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=pkg_metadata,
    hiddenimports=[
        # pydantic-ai model backends
        'pydantic_ai.models.openai',
        'pydantic_ai.models.anthropic',
        'pydantic_ai.models.google',
        'pydantic_ai.models.gemini',
        'pydantic_ai.models.cerebras',
        # pydantic-ai providers (resolved dynamically from LAZYPR_MODEL string)
        'pydantic_ai.providers.openai',
        'pydantic_ai.providers.anthropic',
        'pydantic_ai.providers.google',
        'pydantic_ai.providers.google_gla',
        'pydantic_ai.providers.cerebras',
        'pydantic_ai.providers.deepseek',
        'pydantic_ai.providers.ollama',
        # pydantic internals lost by reflection
        'pydantic._internal._generate_schema',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='lazypr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
