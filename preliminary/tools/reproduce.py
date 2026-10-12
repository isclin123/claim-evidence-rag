"""Rescore all preliminary responses and refresh the Excel result tables."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import OUTPUT, ROOT, write_json
from evaluation import evaluate
from excel_results import refresh_workbook

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reruns',action='store_true',help='Score a complete matrix of newly generated local responses.')
    args = ap.parse_args()
    results,report = evaluate(OUTPUT/'reruns' if args.reruns else None)
    destination = OUTPUT/('rescored_reruns' if args.reruns else '')
    write_json(destination/'asr.json',results)
    refresh_workbook(ROOT/'results/preliminary_results.xlsx',destination/'preliminary_results.xlsx',results)
    report['excel'] = str((destination/'preliminary_results.xlsx').relative_to(ROOT.parent))
    write_json(destination/'reproduction.json',report)
    print(json.dumps(report,indent=2))
