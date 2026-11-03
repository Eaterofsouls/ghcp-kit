# One-shot environment setup. Everything goes to D:\ (nothing on C: except the Python install itself).
$ErrorActionPreference = "Stop"
$root = "D:\ghcp"
New-Item -ItemType Directory -Force -Path "$root\data", "$root\tmp", "$root\pip-cache" | Out-Null
python -m venv "$root\venv"
& "$root\venv\Scripts\Activate.ps1"
$env:PIP_CACHE_DIR = "$root\pip-cache"
$env:TMP = "$root\tmp"; $env:TEMP = "$root\tmp"
$env:GHCP_BASE = "$root\data"
pip install -r requirements.txt
python -c "import duckdb,polars,psutil,matplotlib;print('duckdb',duckdb.__version__,'polars',polars.__version__)"
python -c "import psutil;v=psutil.virtual_memory();d=psutil.disk_usage('D:\\');print('RAM available MB',v.available//2**20,'| D: free GB',d.free//2**30)"
Write-Host "`nNext: python -m ghcp selftest   (keep this shell: GHCP_BASE=$env:GHCP_BASE)"
