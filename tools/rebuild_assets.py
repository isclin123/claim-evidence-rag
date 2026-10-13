"""Rebuild manuscript plots and tables in output/paper_assets; frozen originals stay unchanged."""
import shutil
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]

def main():
    dest=ROOT/'output/paper_assets';dest.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'paper_assets/figstyle.py',dest/'figstyle.py')
    generated=[]
    for folder in sorted((ROOT/'paper_assets').iterdir()):
        if not folder.is_dir() or folder.name=='__pycache__':continue
        scripts=sorted(folder.glob('make_*.py'))
        shutil.copytree(folder,dest/folder.name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
        for script in scripts:
            subprocess.run([sys.executable,'-B',str(dest/folder.name/script.name)],cwd=ROOT,check=True)
            generated.append(f'{folder.name}/{script.name}')
    print('Rebuilt',len(generated),'generators in output/paper_assets.')
if __name__=='__main__':main()
