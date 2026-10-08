"""Collect measures and historical coverage useful for all-time comparisons.

Uses the existing resumable collector and manifest. Football events are the
complete available event exports for the 1,130 already inventoried matches,
not an assertion that StatsBomb covers every historical football match.
"""
import argparse
import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from collect_historical import ROOT, MANIFEST, entries, batch, get, download


def war():
    batch([dict(relative=f'baseball/value/war_daily_{kind}.csv',
                url=f'https://www.baseball-reference.com/data/war_daily_{kind}.txt',
                source='Baseball Reference historical WAR and components', sport='baseball',
                source_page='https://www.baseball-reference.com/about/war_explained.shtml')
           for kind in ['bat','pitch']], workers=2)


def nfl_history():
    repo = 'varadparchure/NFL-Stats-Pipeline'
    revision = json.loads(get(f'https://api.github.com/repos/{repo}/commits/main')[0])['sha']
    tree = json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1')[0])
    batch([dict(relative='american_football/historical_nflcom/'+item['path'],
                url=f'https://raw.githubusercontent.com/{repo}/{revision}/'+quote(item['path']),
                source='Kendall Gillies NFL.com historical archive, Varad Parchure public mirror',
                sport='american_football', revision=revision, expected_bytes=item['size'],
                source_page='https://github.com/kendallgillies/NFL-Statistics-Scrape')
           for item in tree['tree'] if item['path'].endswith('.csv') or item['path'] in ['README.md','LICENSE']])


def soccer_events():
    revision = entries['soccer/competitions.json']['revision']
    matches = sorted(int(p.stem) for p in (ROOT/'soccer/lineups').glob('*.json'))
    assert len(matches) == 1130
    # Batches checkpoint progress and leave the complete intended scope reproducible.
    for start in range(0,len(matches),100):
        batch([dict(relative=f'soccer/events/{mid}.json',
                    url=f'https://raw.githubusercontent.com/hudl/open-data/{revision}/data/events/{mid}.json',
                    source='StatsBomb Open Data performance events', sport='soccer',
                    revision=revision, match_id=mid, source_page='https://github.com/hudl/open-data')
               for mid in matches[start:start+100]], workers=3)


def recognition():
    sources = {
        'nba75.html': ('https://www.nba.com/news/nba-75th-anniversary-team-announced','NBA 75th Anniversary Team, 2021'),
        'nhl100.html': ('https://www.nhl.com/news/100-greatest-nhl-players-complete-list-286199184','NHL 100 Greatest Players, 2017'),
        'nfl100_quarterbacks.html': ('https://www.nfl.com/news/nfl-100-all-time-team-quarterbacks-announced-0ap3000001091949','NFL 100 All-Time Team quarterbacks, 2019'),
        'rsssf_century.html': ('https://www.rsssf.org/miscellaneous/century.html','RSSSF documented international goals and appearance denominators'),
    }
    batch([dict(relative='recognition/'+name, url=url, source=source) for name,(url,source) in sources.items()], workers=2)


def nfl_primary():
    import pandas as pd
    from bs4 import BeautifulSoup
    import sqlite3
    batch([dict(relative='american_football/players_crosswalk.csv',
                url='https://github.com/nflverse/nflverse-data/releases/download/players/players.csv',
                source='nflverse player identity crosswalk', sport='american_football')])
    identities = pd.read_csv(ROOT/'american_football/players_crosswalk.csv', low_memory=False)
    names = set(identities.loc[(identities.position.eq('QB')) & (identities.rookie_season<=1998), 'display_name'])
    source = BeautifulSoup((ROOT/'recognition/nfl100_quarterbacks.html').read_bytes(), 'html.parser')
    names.update(h.get_text(' ',strip=True).split(' (')[0] for h in source.find_all('h3') if '(' in h.get_text())
    con = sqlite3.connect(ROOT/'derived/historical_players.sqlite')
    modern = pd.read_sql_query('SELECT player, attempts FROM nfl_since_1999_career_totals', con)
    con.close()
    names.update(modern.loc[modern.attempts>=1500,'player'])
    archived = pd.read_csv(ROOT/'american_football/historical_nflcom/Career_Stats_Passing.csv', na_values=['--'])
    archived['attempts'] = pd.to_numeric(archived['Passes Attempted'].astype(str).str.replace(',',''),errors='coerce')
    totals = archived.groupby('Name').attempts.sum()
    for name in totals[totals>=1500].index:
        last,first = name.split(',',1)
        names.add(first.strip()+' '+last.strip())
    jobs = []
    for name in sorted(names):
        slug = unicodedata.normalize('NFKD', name).encode('ascii','ignore').decode().lower()
        slug = re.sub(r'[^a-z0-9 -]','',slug).replace(' ','-')
        jobs.append(dict(relative=f'american_football/official_careers/{slug}.html',
                         url=f'https://www.nfl.com/players/{slug}/stats/career',
                         source='NFL.com official career and season statistics', sport='american_football',
                         player=name, sampling_rule='NFLverse QB rookie<=1998 OR NFL100 QB OR recorded career attempts>=1500'))
    availability = []
    def request(job):
        time.sleep(0.5)
        return download(**job)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(request,job):job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                relative,record = future.result()
                entries[relative] = record
                MANIFEST.write_text(json.dumps(entries,indent=2,sort_keys=True)+'\n')
                status = 'downloaded; tables require audit'
            except Exception as error:
                status = str(error)
            availability.append(dict(player=job['player'],url=job['url'],status=status))
            if len(availability)%50 == 0:
                print(f'NFL career pages checked: {len(availability)}/{len(jobs)}',flush=True)
    (ROOT/'american_football/official_careers/availability.json').write_text(json.dumps(availability,indent=2)+'\n')
    print(f'NFL career page inventory complete: {len(availability)} candidates',flush=True)



def nfl_hof():
    from bs4 import BeautifulSoup
    batch([dict(relative='american_football/hof_positions.html',
                url='https://www.profootballhof.com/hall-of-famers/positions',
                source='Pro Football Hall of Fame published position index',sport='american_football')])
    soup=BeautifulSoup((ROOT/'american_football/hof_positions.html').read_bytes(),'html.parser')
    jobs=[]; roster=[]
    for h in soup.find_all('h3'):
        heading=h.get_text(' ',strip=True)
        if not heading.startswith(('QB (','RB/QB (')):continue
        for a in h.parent.find_all('a',href=True):
            context=''
            for sibling in a.next_siblings:
                if getattr(sibling,'name',None)=='br':break
                context+=str(sibling)
            if heading.startswith('RB/QB') and '(QB)' not in context:continue
            slug=a['href'].rstrip('/').split('/')[-1]
            roster.append(dict(player=a.get_text(' ',strip=True),slug=slug,index_context=context.strip()))
            jobs.append(dict(relative=f'american_football/hof_careers/{slug}.html',url=a['href'],
                             source='Pro Football Hall of Fame historical career tables',sport='american_football',
                             player=a.get_text(' ',strip=True),sampling_rule='QB-tagged players in the published HOF position index'))
    (ROOT/'american_football/hof_careers').mkdir(exist_ok=True)
    (ROOT/'american_football/hof_careers/roster.json').write_text(json.dumps(roster,indent=2)+'\n')
    print('Hall of Fame quarterback profiles:',len(jobs),flush=True)
    batch(jobs,workers=2)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', choices=['war','nfl_history','soccer_events','recognition','nfl_primary','nfl_hof'])
    options = parser.parse_args()
    for collect in [war, nfl_history, recognition, soccer_events, nfl_primary, nfl_hof]:
        if options.only and collect.__name__ != options.only:
            continue
        print(collect.__name__, flush=True)
        collect()
