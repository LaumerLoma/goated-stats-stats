"""Download public historical sports data with a resumable, checksummed manifest.

Run: python collect_historical.py
No credentials, browser sessions, or paid services are used.
Raw responses are preserved; schema and coverage are audited separately.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import re
import time

ROOT = Path(__file__).resolve().parent / 'historical_data'
ROOT.mkdir(exist_ok=True)
MANIFEST = ROOT / 'manifest.json'
entries = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def get(url):
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'HistoricalSportsResearch/1.0'}), timeout=60) as response:
                return response.read(), response.headers.get('Content-Type', '')
        except Exception as error:
            if isinstance(error, HTTPError) and error.code in (401,403,404):
                raise
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def download(relative, url, source, **metadata):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    old = entries.get(relative)
    if old and path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == old['sha256']:
        return relative, old
    data, content_type = get(url)
    if relative.endswith('.json'):
        json.loads(data)
    elif relative.endswith('.csv'):
        head = data[:1000].decode('utf-8-sig', errors='replace')
        if '<html' in head.lower() or '<!doctype' in head.lower() or ',' not in head.splitlines()[0]:
            raise ValueError(f'Not a CSV: {relative}')
    path.write_bytes(data)
    record = dict(url=url, source=source, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                  downloaded_utc=datetime.now(timezone.utc).isoformat(), content_type=content_type, **metadata)
    return relative, record


def batch(jobs, workers=3):
    failures = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download, **job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                relative, record = future.result()
                entries[relative] = record
                MANIFEST.write_text(json.dumps(entries, indent=2, sort_keys=True) + '\n')
            except Exception as error:
                failures.append({'job': job, 'error': str(error)})
    if failures:
        (ROOT / 'download_failures.json').write_text(json.dumps(failures, indent=2))
        raise RuntimeError(f'{len(failures)} downloads failed; inspect download_failures.json and rerun.')
    failure_log = ROOT / 'download_failures.json'
    if failure_log.exists():
        completed = {j['relative'] for j in jobs}
        remaining = [f for f in json.loads(failure_log.read_text()) if f['job']['relative'] not in completed]
        if remaining:
            failure_log.write_text(json.dumps(remaining, indent=2))
        else:
            failure_log.unlink()
    print(f'{len(jobs)} files complete; {sum(e["bytes"] for e in entries.values()) / 1048576:.1f} MiB downloaded', flush=True)


def baseball():
    shared = 'y1prhc795jk8zvmelfd3jq7tl389y6cd'
    jobs = []
    for page in (1, 2):
        url = f'https://sabr.box.com/s/{shared}?page={page}'
        data, _ = get(url)
        state = json.loads(re.search(r'Box.postStreamData = (.*?);\s*</script>', data.decode(), re.S).group(1))
        for item in state['/app-api/enduserapp/shared-folder']['items']:
            jobs.append(dict(relative='baseball/' + item['name'],
                             url='https://sabr.box.com/index.php?' + urlencode(dict(rm='box_download_shared_file', shared_name=shared, file_id='f_' + str(item['id']))),
                             source='SABR / Sean Lahman official 2025 release', sport='baseball',
                             source_page='https://sabr.org/lahman-database/', expected_bytes=item['itemSize']))
    assert len({j['relative'] for j in jobs}) == 28
    batch(jobs)
    for j in jobs:
        assert entries[j['relative']]['bytes'] == j['expected_bytes'], j['relative']


def basketball():
    repo = 'cmuchina3/nba-stats-1947-present-curated'
    tree = json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/main?recursive=1')[0])
    revision = tree['sha']
    jobs = []
    for item in tree['tree']:
        name = item['path']
        if name.startswith('data/raw/') and name.endswith('.csv') or name in ['README.md', 'docs/data-dictionary.md', 'docs/processing-notes.md']:
            jobs.append(dict(relative='basketball/' + name.split('/')[-1],
                             url=f'https://raw.githubusercontent.com/{repo}/{revision}/' + quote(name),
                             source='Sumitro Datta / Basketball Reference, Clarence Muchina public mirror',
                             sport='basketball', revision=revision, expected_bytes=item['size'],
                             source_page=f'https://github.com/{repo}'))
    batch(jobs)
    for j in jobs:
        assert entries[j['relative']]['bytes'] == j['expected_bytes'], j['relative']


def hockey():
    jobs = []
    for report in ('skater/summary', 'goalie/summary', 'team/summary'):
        for game_type in (2, 3):
            for start in range(1917, 2026, 5):
                end = min(start + 4, 2025)
                query = dict(isAggregate='false', isGame='false', start=0, limit=-1,
                             cayenneExp=f'gameTypeId={game_type} and seasonId>={start}{start+1} and seasonId<={end}{end+1}')
                jobs.append(dict(relative=f'hockey/{report.replace("/", "_")}_{game_type}_{start}_{end}.json',
                                 url='https://api.nhle.com/stats/rest/en/' + report + '?' + urlencode(query),
                                 source='NHL official statistics API', sport='hockey', game_type=game_type,
                                 start_season=start, end_season=end, source_page='https://www.nhl.com/stats/'))
    batch(jobs, workers=2)
    for j in jobs:
        response = json.loads((ROOT / j['relative']).read_text())
        assert len(response['data']) == response['total'] < 10000, j['relative']
        rows = response['data']
        identity = 'teamId' if j['relative'].startswith('hockey/team') else 'playerId'
        assert len({(r[identity], r['seasonId']) for r in rows}) == len(rows), j['relative']


def football():
    # REG and POST are separate; REG+POST would duplicate the same outcomes.
    release = json.loads(get('https://api.github.com/repos/nflverse/nflverse-data/releases/tags/stats_player')[0])
    jobs = []
    for asset in release['assets']:
        if re.fullmatch(r'stats_player_(reg|post)_\d{4}\.csv', asset['name']) and int(asset['name'][-8:-4]) <= 2025:
            jobs.append(dict(relative='american_football/' + asset['name'], url=asset['browser_download_url'],
                             source='nflverse player summary statistics', sport='american_football',
                             expected_bytes=asset['size'], source_page=release['html_url']))
    assert len(jobs) == 54
    batch(jobs)
    for j in jobs:
        assert entries[j['relative']]['bytes'] == j['expected_bytes'], j['relative']


def soccer():
    # Collect every available competition-season metadata file. Lineups cover
    # La Liga's Messi-era sample and men's/women's World Cups, including historic games.
    repo = 'statsbomb/open-data'
    revision = json.loads(get(f'https://api.github.com/repos/{repo}/commits/master')[0])['sha']
    base = f'https://raw.githubusercontent.com/{repo}/{revision}/'
    batch([dict(relative='soccer/competitions.json', url=base+'data/competitions.json',
                source='StatsBomb Open Data', sport='soccer', revision=revision,
                source_page='https://github.com/statsbomb/open-data'),
           dict(relative='soccer/README.md', url=base+'README.md', source='StatsBomb Open Data', sport='soccer', revision=revision)])
    competitions = json.loads((ROOT / 'soccer/competitions.json').read_text())
    jobs = []
    for comp in competitions:
        cid, sid = comp['competition_id'], comp['season_id']
        jobs.append(dict(relative=f'soccer/matches/{cid}_{sid}.json', url=base+f'data/matches/{cid}/{sid}.json',
                         source='StatsBomb Open Data', sport='soccer', revision=revision,
                         competition=comp['competition_name'], season=comp['season_name'], gender=comp['competition_gender']))
    batch(jobs)
    match_ids = set()
    for comp in competitions:
        if comp['competition_name'] in ('La Liga', 'FIFA World Cup', "Women's World Cup"):
            data = json.loads((ROOT / f'soccer/matches/{comp["competition_id"]}_{comp["season_id"]}.json').read_text())
            match_ids.update(m['match_id'] for m in data)
    batch([dict(relative=f'soccer/lineups/{mid}.json', url=base+f'data/lineups/{mid}.json',
                source='StatsBomb Open Data', sport='soccer', revision=revision, match_id=mid)
           for mid in sorted(match_ids)], workers=3)


def international_soccer():
    repo = 'martj42/international_results'
    revision = json.loads(get(f'https://api.github.com/repos/{repo}/commits/master')[0])['sha']
    batch([dict(relative='soccer/internationals/' + name,
                url=f'https://raw.githubusercontent.com/{repo}/{revision}/' + name,
                source='Mart Jürisoo international football results', sport='soccer', revision=revision,
                source_page=f'https://github.com/{repo}')
           for name in ['results.csv', 'goalscorers.csv', 'shootouts.csv', 'former_names.csv', 'README.md', 'LICENSE']])


def support():
    revision = entries['soccer/competitions.json']['revision']
    batch([dict(relative='soccer/StatsBomb-logo.png',
                url=f'https://raw.githubusercontent.com/hudl/open-data/{revision}/img/SB%20-%20Icon%20Lockup%20-%20Colour%20positive.png',
                source='StatsBomb attribution media', sport='soccer', revision=revision),
           dict(relative='soccer/LICENSE.pdf', url=f'https://raw.githubusercontent.com/hudl/open-data/{revision}/LICENSE.pdf',
                source='StatsBomb Open Data source agreement', sport='soccer', revision=revision),
           dict(relative='american_football/LICENSE', url='https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md',
                source='nflverse data license', sport='american_football')])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', choices=['baseball','basketball','hockey','football','soccer','international_soccer','support'])
    options = parser.parse_args()
    for name, collect in [('Baseball', baseball), ('Basketball', basketball), ('Hockey', hockey),
                          ('American football', football), ('Soccer', soccer),
                          ('International soccer', international_soccer), ('Attribution', support)]:
        if options.only and collect.__name__ != options.only:
            continue
        print(name, flush=True)
        collect()
    print('Completed. Sources and hashes: historical_data/manifest.json', flush=True)
