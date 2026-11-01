#!/usr/bin/env python3
"""Deprecated one-time SQL migration tool; archived for provenance only.

The repository's JSON records are now authoritative. Run only against a
separate, empty scratch directory to inspect the historical conversion.
The SQL export is treated as an input snapshot, not executed.
Unidentified season columns are retained in positional form.
Season and movie Amazon URLs are normalized without affiliate parameters.
"""
import argparse
import json
from pathlib import Path
import re
import sys

FIELDS = ['prodcode','type','title','epnum','tcode','airdate','season','sepisode','SHOWCODE','SNPP','Wikipedia']
LINE = re.compile(r'^INSERT INTO `([^`]+)` VALUES \((.*)\);$')


def clean_amazon_url(url, asin):
    if not url and not asin:
        return ''
    if not isinstance(asin, str) or not re.fullmatch(r'[A-Z0-9]{10}', asin):
        raise ValueError(f'invalid Amazon ASIN: {asin!r}')
    match = re.fullmatch(r'https?://www\.amazon\.ca/dp/([A-Z0-9]{10})(?:\?[^#]*)?', url or '')
    if not match or match.group(1) != asin:
        raise ValueError(f'Amazon URL and ASIN disagree: {url!r}, {asin!r}')
    return f'https://www.amazon.ca/dp/{asin}'

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
    parser.add_argument('--data',type=Path,required=True,
                        help='empty scratch output directory; never the canonical data/ tree')
    args=parser.parse_args()
    args.data=args.data.resolve()
    canonical=(Path(__file__).resolve().parents[1]/'data').resolve()
    if args.data == canonical or args.data.is_relative_to(canonical):
        parser.error('the canonical data/ tree is the source of truth; use a scratch directory')
    if args.data.exists() and any(args.data.iterdir()):
        parser.error('scratch output directory must be empty')
    counts={'episodes':0,'specials':0,'seasons':0,'movies':0}
    movie=None
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
                if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', str(raw['airdate'])):
                    raise ValueError(f'legacy movie needs a release year: {line_no}')
                ident=f"movie-{raw['airdate'][:4]}";folder='movies'
            else:
                ident=str(raw['prodcode']);folder={'short':'shorts/tracey-ullman','commercial':'commercials','webisode':'specials'}.get(kind)
                if not folder:raise ValueError(f'unknown kind {kind} line {line_no}')
            if (folder,ident) in seen:raise ValueError('duplicate '+ident)
            seen.add((folder,ident))
            record={'id':ident,'titles':{'en':raw['title']},'production_code':raw['prodcode']}
            if raw['airdate'] not in ('','0000-00-00'):
                record['release_date' if kind=='movie' else 'original_air_date']=raw['airdate']
            if raw['epnum']:record['overall_number']=raw['epnum']
            if kind not in ('episode','movie'):record['type']=kind
            # Preserve site-specific and historical columns exactly, including zero/blank values.
            episode_legacy={k:raw[k] for k in ('type','epnum','tcode','season','sepisode','SHOWCODE','SNPP','Wikipedia')}
            if kind=='movie':
                if movie is not None:raise ValueError('multiple legacy movie rows')
                record['legacy']={'episode_row':episode_legacy}
                movie=record
            else:
                record['legacy']=episode_legacy
                write(args.data/folder/(ident+'.json'),record)
            counts[folder if folder in counts else 'specials']+=1
        elif table=='seasons':
            if len(vals)!=8:raise ValueError(f'line {line_no}: expected 8 season values, got {len(vals)}')
            row_id,code,label,years,url1,asin1,url2,asin2=vals
            is_movie=str(code).lower()=='movie'
            ident='movie' if is_movie else f's{int(code):02}'
            if ('seasons',ident) in seen:raise ValueError('duplicate season '+ident)
            seen.add(('seasons',ident))
            items=[]
            for slot,(url,asin) in enumerate(((url1,asin1),(url2,asin2))):
                if url or asin:
                    clean_url=clean_amazon_url(url,asin)
                    vals[4+slot*2]=clean_url
                    items.append({'url':clean_url,'asin':asin,'format':'dvd' if slot==0 else 'blu_ray'})
            rec={'id':ident,'titles':{'en':label},'legacy':{'row_id':row_id,'season_code':code,'years':years,'original_columns':vals}}
            if items:rec['amazon_listings']=items
            if is_movie:
                if movie is None or 'catalogue_row' in movie['legacy']:
                    raise ValueError('unexpected legacy movie catalogue row')
                movie['legacy']['catalogue_row']=rec['legacy']
                if items:movie['amazon_listings']=items
            else:
                write(args.data/'seasons'/(ident+'.json'),rec)
                counts['seasons']+=1
    if movie is None or 'catalogue_row' not in movie['legacy']:
        raise ValueError('incomplete legacy movie data')
    write(args.data/'movies'/(movie['id']+'.json'),movie)
    print('Imported:', counts)
    if counts['episodes']+counts['specials']+counts['movies']!=549 or counts['seasons']!=22 or counts['movies']!=1:
        raise ValueError('unexpected row counts: '+str(counts))

if __name__=='__main__':main()
