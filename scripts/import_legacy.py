#!/usr/bin/env python3
"""Import the supplied legacy SQL excerpt without requiring a MySQL server.

The SQL export is intentionally treated as an input snapshot, not executed.
Unidentified season columns are retained in positional form.
"""
import argparse
import json
from pathlib import Path
import re
import sys

FIELDS = ['prodcode','type','title','epnum','tcode','airdate','season','sepisode','SHOWCODE','SNPP','Wikipedia']
LINE = re.compile(r'^INSERT INTO `([^`]+)` VALUES \((.*)\);$')

def parse_values(text):
    values=[]; i=0
    while i<len(text):
        while i<len(text) and text[i].isspace(): i+=1
        if i>=len(text): break
        if text[i]=="'":
            i+=1; buf=[]
            while i<len(text):
                ch=text[i]
                if ch=='\\' and i+1<len(text):
                    i+=1
                    escapes={'0':'\0','n':'\n','r':'\r','t':'\t','Z':'\x1a'}
                    buf.append(escapes.get(text[i],text[i]))
                elif ch=="'":
                    if i+1<len(text) and text[i+1]=="'":buf.append("'");i+=1
                    else:i+=1;break
                else:buf.append(ch)
                i+=1
            value=''.join(buf)
        else:
            start=i
            while i<len(text) and text[i]!=',':i+=1
            token=text[start:i].strip()
            value=None if token.upper()=='NULL' else int(token) if re.fullmatch(r'-?\d+',token) else token
        values.append(value)
        while i<len(text) and text[i].isspace():i+=1
        if i<len(text):
            if text[i]!=',':raise ValueError('expected comma at '+str(i))
            i+=1
    return values

def write(path,record):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old!=record:
            raise ValueError(f'existing record differs; refusing overwrite: {path}')
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('dump',type=Path)
    parser.add_argument('--data',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    args=parser.parse_args()
    counts={'episodes':0,'specials':0,'seasons':0}
    seen=set()
    for line_no,line in enumerate(args.dump.read_text(encoding='utf-8').splitlines(),1):
        m=LINE.match(line)
        if not m:continue
        table=m.group(1)
        if table not in ('episodes','seasons'):
            raise ValueError(f'Unsupported INSERT in table {table} line {line_no}')
        vals=parse_values(m.group(2))
        if table=='episodes':
            if len(vals)!=len(FIELDS):raise ValueError(f'line {line_no}: {len(vals)} episode columns')
            raw=dict(zip(FIELDS,vals)); kind=raw['type']
            if kind=='episode':
                season=int(raw['season']); episode=int(raw['sepisode'])
                if season<=0 or episode<=0:raise ValueError(f'bad season episode: {line_no}')
                ident=f's{season:02}e{episode:02}'; folder='episodes'
            elif kind=='movie':
                ident=str(raw['prodcode']);folder='specials'
            else:
                ident=str(raw['prodcode']);folder={'short':'shorts/tracey-ullman','commercial':'commercials','webisode':'specials'}.get(kind)
                if not folder:raise ValueError(f'unknown kind {kind} line {line_no}')
            if (folder,ident) in seen:raise ValueError('duplicate '+ident)
            seen.add((folder,ident))
            record={'id':ident,'titles':{'en':raw['title']},'production_code':raw['prodcode']}
            if raw['airdate'] not in ('','0000-00-00'):record['original_air_date']=raw['airdate']
            if raw['epnum']:record['overall_number']=raw['epnum']
            if kind!='episode':record['type']=kind
            # Preserve site-specific and historical columns exactly, including zero/blank values.
            record['legacy']={k:raw[k] for k in ('type','epnum','tcode','season','sepisode','SHOWCODE','SNPP','Wikipedia')}
            write(args.data/folder/(ident+'.json'),record)
            counts[folder if folder in counts else 'specials']+=1
        elif table=='seasons':
            if len(vals)!=8:raise ValueError(f'line {line_no}: expected 8 season values, got {len(vals)}')
            row_id,code,label,years,url1,asin1,url2,asin2=vals
            ident='movie' if str(code).lower()=='movie' else f's{int(code):02}'
            if ('seasons',ident) in seen:raise ValueError('duplicate season '+ident)
            seen.add(('seasons',ident))
            items=[]
            for url,asin in ((url1,asin1),(url2,asin2)):
                if url or asin:items.append({'url':url,'asin':asin})
            rec={'id':ident,'titles':{'en':label},'legacy':{'row_id':row_id,'season_code':code,'years':years,'original_columns':vals}}
            if items:rec['amazon_listings']=items
            write(args.data/'seasons'/(ident+'.json'),rec)
            counts['seasons']+=1
    print('Imported:', counts)
    if counts['episodes']+counts['specials']!=549 or counts['seasons']!=23:
        raise ValueError('unexpected row counts: '+str(counts))

if __name__=='__main__':main()
