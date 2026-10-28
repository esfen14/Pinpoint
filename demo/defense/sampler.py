"""Record host RAM, swap and disk samples during a rehearsal and summarize them.

Usage: python3 -I demo/defense/sampler.py record FILE SECONDS [INTERVAL]
       python3 -I demo/defense/sampler.py summary FILE
Rows are: epoch seconds, available MiB, cumulative swap-in pages, swap-out pages,
free disk MiB. Read-only; it never touches the lab.
"""
from pathlib import Path
import os
import shutil
import sys
import time

MAX_SECONDS=86400


def check_limits(seconds,interval):
    if type(seconds) is not int or type(interval) is not int or not 1<=seconds<=MAX_SECONDS or not 1<=interval<=60:
        raise ValueError('Sampling duration or interval is out of range')


def observe(root=Path.home()):
    available=None
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            available=int(line.split()[1])//1024
    counters={}
    for line in Path('/proc/vmstat').read_text().splitlines():
        name,_,value=line.partition(' ')
        if name in ('pswpin','pswpout'):
            counters[name]=int(value)
    if available is None or set(counters)!={'pswpin','pswpout'}:
        raise ValueError('Host counters unavailable')
    return int(time.time()),available,counters['pswpin'],counters['pswpout'],shutil.disk_usage(root).free//(1024*1024)


def append(path,row):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'a') as stream:
        stream.write(' '.join(str(value) for value in row)+'\n')


def read(path):
    rows=[]
    for line in Path(path).read_text().splitlines():
        fields=line.split()
        if len(fields)!=5 or not all(field.isdigit() for field in fields):
            raise ValueError('Malformed sample file')
        rows.append(tuple(int(field) for field in fields))
    return rows


def summarize(rows):
    if not rows:
        raise ValueError('No samples')
    peak=0.0
    for before,after in zip(rows,rows[1:]):
        if after[2]<before[2] or after[3]<before[3] or after[0]<before[0]:
            raise ValueError('Sample counters went backwards')
        seconds=max(after[0]-before[0],1)
        peak=max(peak,((after[2]-before[2])+(after[3]-before[3]))/seconds)
    seconds=rows[-1][0]-rows[0][0]
    return {'samples':len(rows),'seconds':seconds,'min_available_mib':min(r[1] for r in rows),
            'swap_in_pages':rows[-1][2]-rows[0][2],'swap_out_pages':rows[-1][3]-rows[0][3],
            'max_swap_pages_per_second':round(peak,1),'min_free_disk_mib':min(r[4] for r in rows)}


def main(argv):
    if len(argv)>=3 and argv[0]=='record':
        seconds=int(argv[2]);interval=int(argv[3]) if len(argv)>3 else 5
        check_limits(seconds,interval)
        end=time.time()+seconds
        while time.time()<end:
            append(argv[1],observe())
            time.sleep(interval)
    elif len(argv)==2 and argv[0]=='summary':
        for key,value in summarize(read(argv[1])).items():
            print(key,value)
    else:
        raise SystemExit(__doc__)


if __name__=='__main__':
    main(sys.argv[1:])
