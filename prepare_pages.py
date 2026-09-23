"""Stage public website assets, excluding maintenance scripts and sync state."""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parent
destination=root/'_site'
destination.mkdir(exist_ok=True)
for path in root.iterdir():
    if path.is_file() and (path.suffix in ('.html','.css','.js','.png','.svg','.ico') or path.name in ('.nojekyll','sitemap.xml','robots.txt')):
        shutil.copy2(path,destination/path.name)
print('Staged',len(list(destination.iterdir())),'public website files.')
