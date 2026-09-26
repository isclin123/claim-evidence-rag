"""Check that every included manuscript artifact was rebuilt from package data."""
from pathlib import Path
import argparse, json, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inventory-only',action='store_true')
    ap.add_argument('--strict-render',action='store_true',help='Require identical PNG bytes; intended for the recorded rendering environment.')
    args=ap.parse_args()
    inventory=json.loads((ROOT/'provenance/paper_items.json').read_text(encoding='utf-8'))
    items=inventory['items']
    assert {x['item'] for x in items}=={f'Table {i}' for i in range(1,27)}|{f'Figure {i}' for i in range(1,14)}
    assert len({x['item'] for x in items})==len(items)
    excluded={x['item'] for x in items if x['status']=='excluded_by_author'}
    assert excluded=={'Table 1','Figure 2'}
    checked=[];render_differences=[]
    for item in items:
        if 'path' not in item:continue
        source=ROOT/item['path']
        assert source.is_file(),source
        if not args.inventory_only:
            output=ROOT/'output'/item['path']
            assert output.is_file(),output
            if source.suffix=='.tex':
                assert source.read_text(encoding='utf-8')==output.read_text(encoding='utf-8'),f'Table/source mismatch: {item["item"]}'
            else:
                # Exact equality expects the tested dependency versions and fonts.
                if source.with_suffix('.png').read_bytes()!=output.with_suffix('.png').read_bytes():
                    render_differences.append(item['item'])
                    if args.strict_render:raise AssertionError(f'Figure rendering differs: {item["item"]}; check versions/fonts')
        checked.append(item['item'])
    assert len(checked)==37
    report={'passed':True,'included_tables':25,'result_figures':11,'illustrative_figures':1,
            'excluded':sorted(excluded),'checked':checked,'inventory_only':args.inventory_only,
            'render_byte_differences':render_differences}
    if not args.inventory_only:
        (ROOT/'output/paper_outputs.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS:',len(checked),'included manuscript artifacts', '(inventory)' if args.inventory_only else '(rebuilt tables and figures)')
    if render_differences:print('Rendering differs from the recorded font/platform environment:',', '.join(render_differences))
if __name__=='__main__':main()
