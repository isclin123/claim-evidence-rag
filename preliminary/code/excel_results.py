"""Refresh numerical cells in the supplied Excel template using standard OOXML.

Preserves the authored workbook's styles, tables, formulas and panes. This small
runtime exporter needs only Python's standard library, so offline reproduction
does not depend on a spreadsheet application or an authoring service.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
TAG = '{'+NS['s']+'}'


def table_rows(results):
    summary = sorted((r for r in results if r['model']=='ALL' and r['dataset']=='ALL'),
                     key=lambda r:(-r['asr'],r['condition_id']))
    rank = {r['condition_id']:i for i,r in enumerate(summary)}
    detail = sorted((r for r in results if r['model']!='ALL' and r['dataset']!='ALL'),
                    key=lambda r:(rank[r['condition_id']],r['model'].replace('_',' '),r['dataset']))
    return summary,detail


def refresh_workbook(template, destination, results):
    summary,detail = table_rows(results)
    if len(summary)!=14 or len(detail)!=336:
        raise ValueError('Expected fourteen methods and 336 model-dataset rows')
    lookup = {(r['model'],r['dataset'],r['condition_id']):r for r in results}
    updates = {'xl/worksheets/sheet1.xml':{},'xl/worksheets/sheet2.xml':{}}
    for i,r in enumerate(summary,2):
        rank = 1 + sum(other['asr'] > r['asr'] for other in summary)
        values = [rank,r['condition_id'],r['method'],r['successes'],r['total'],r['asr'],
                  r['delta_vs_poisonedrag_pp']]+[lookup[('ALL',ds,r['condition_id'])]['asr']
                                                for ds in ['nq','hotpotqa','msmarco']]
        for column,value in zip('ABCDEFGHIJ',values):
            updates['xl/worksheets/sheet1.xml'][f'{column}{i}']=value
    for i,r in enumerate(detail,2):
        values = [r['condition_id'],r['method'],r['model'],r['dataset'],r['successes'],r['total'],
                  r['asr'],r['delta_vs_poisonedrag_pp']]
        for column,value in zip('ABCDEFGH',values):
            updates['xl/worksheets/sheet2.xml'][f'{column}{i}']=value
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(template) as source, zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as output:
        for info in source.infolist():
            content = source.read(info.filename)
            if info.filename in updates:
                tree = ET.fromstring(content)
                cells = {c.attrib['r']:c for c in tree.findall('.//s:sheetData/s:row/s:c',NS)}
                for address,value in updates[info.filename].items():
                    cell = cells[address]
                    for child in list(cell):
                        if child.tag in {TAG+'v',TAG+'is'}:
                            cell.remove(child)
                    if isinstance(value,str):
                        cell.attrib['t']='inlineStr'
                        ET.SubElement(ET.SubElement(cell,TAG+'is'),TAG+'t').text=value
                    else:
                        cell.attrib.pop('t',None)
                        ET.SubElement(cell,TAG+'v').text=repr(value)
                content=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
            output.writestr(info,content)
