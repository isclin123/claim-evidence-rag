"""Offline verification of every preliminary input, response and summary."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import OUTPUT, write_json
from evaluation import evaluate

if __name__ == '__main__':
    _,report = evaluate()
    write_json(OUTPUT/'verification.json',report)
    print(json.dumps(report,indent=2))
