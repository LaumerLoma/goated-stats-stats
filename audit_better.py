"""Construct higher-quality all-time research tables and validate source coverage.

Stages can run separately: --section foundation, nfl, panels, hof, or report.
Tables are added to the existing historical_players.sqlite database.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from io import StringIO
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent/'historical_data'
OUT = ROOT/'derived'
AUDIT = OUT/'quality_audit.json'
audit = json.loads(AUDIT.read_text()) if AUDIT.exists() else {}
con = sqlite3.connect(OUT/'historical_players.sqlite')


def store(name, frame):
    frame.to_sql(name, con, if_exists='replace', index=False)


def checkpoint():
    AUDIT.write_text(json.dumps(audit, indent=2, allow_nan=False)+'\n')


def clean_name(name):
    value = unicodedata.normalize('NFKD',str(name)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]','',value)


def recognized():
    rows=[]
    soup=BeautifulSoup((ROOT/'recognition/nba75.html').read_bytes(),'html.parser')
    head=next(h for h in soup.find_all('h2') if 'NBA 75TH ANNIVERSARY TEAM' in h.get_text())
    names=[]
    for p in head.next_siblings:
        if getattr(p,'name',None)=='p' and '•' in p.get_text():
            names.extend(x.strip() for x in p.get_text(' ',strip=True).split('•')[1:])
    assert len(names)==len(set(names))==76
    rows.extend(dict(sport='basketball',name=n,selection='NBA75',selection_year=2021) for n in names)
    soup=BeautifulSoup((ROOT/'recognition/nhl100.html').read_bytes(),'html.parser')
    body=next(p for p in soup.find_all('p') if 'SID ABEL' in p.get_text())
    names=[]
    for line in body.get_text('\n',strip=True).splitlines():
        match=re.match(r"^([A-Z .'-]+)\s+\((?:C|LW|RW|D|G),",line)
        if match:names.append((match.group(1).strip().title(),re.search(r'\((C|LW|RW|D|G),',line).group(1)))
    assert len(names)==len(set(names))==100
    rows.extend(dict(sport='hockey',name=n,selection='NHL100',selection_year=2017,selection_role=role) for n,role in names)
    soup=BeautifulSoup((ROOT/'recognition/nfl100_quarterbacks.html').read_bytes(),'html.parser')
    names=[h.get_text(' ',strip=True).split(' (')[0] for h in soup.find_all('h3') if '(' in h.get_text()]
    assert len(names)==len(set(names))==10
    rows.extend(dict(sport='american_football',name=n,selection='NFL100_QB',selection_year=2019) for n in names)
    labels=pd.DataFrame(rows)
    # Explicit aliases preserve the league's published name and the source player ID.
    aliases={'natearchibald':'tinyarchibald','ronartest':'mettaworldpeace','turkbroda':'walterbroda','johnnybucyk':'johnbucyk','berniegeoffrion':'bernardgeoffrion','tedkennedy':'teederkennedy','tedlindsay':'robertlindsay','charlieconacher':'charlesconacher','kingclancy':'frankclancy','kingclancy':'francisclancy','redkelly':'leonardkelly','toeblake':'hectorblake'}
    # Match names only when unique; unresolved aliases stay explicit rather than fuzzy-matched.
    populations={
        'basketball':pd.read_sql_query('SELECT player_id AS id, player AS player FROM nba_baa_career_totals',con),
        'hockey':pd.concat([pd.read_sql_query('SELECT playerId AS id, skaterFullName AS player FROM nhl_skater_regular',con),pd.read_sql_query('SELECT playerId AS id, goalieFullName AS player FROM nhl_goalie_regular',con)]).drop_duplicates(),
    }
    matched=[]
    for row in rows:
        out=dict(row,source_player_id=None)
        if row['sport'] in populations:
            pop=populations[row['sport']]; key=clean_name(row['name'])
            found=pop[pop.player.map(clean_name).eq(key)].id.unique()
            if len(found)!=1:
                found=pop[pop.player.map(clean_name).eq(aliases.get(key,key))].id.unique()
            if row['sport']=='basketball' and key=='patrickewing':
                found=np.array(['ewingpa01'])  # Senior: 1985--2002; Junior has a separate ID.
            if len(found)==1:out['source_player_id']=str(found[0])
        matched.append(out)
    frame=pd.DataFrame(matched)
    store('published_all_time_recognition',frame)
    audit['recognition']={'nba75':76,'nhl100':100,'nfl100_qb':10,
                          'unresolved_identity_names':frame[frame.sport.ne('american_football') & frame.source_player_id.isna()][['sport','name']].to_dict('records'),
                          'interpretation':'Published all-time elite selections, not 186 GOATs, not a common ordinal ranking; dates and identities preserved. No performance tests use unresolved identities.'}
    # Documented international scoring totals include appearance denominators.
    soup=BeautifulSoup((ROOT/'recognition/rsssf_century.html').read_bytes(),'html.parser')
    pres=soup.find_all('pre'); source=pres[3].get_text(); records=[]
    pattern=re.compile(r'^\s*(?:\d+\.)?\s*(.*?)\s*\[([^]]+)\]\s*(\d+)\s*\(\s*(\d+)\)\s*\((\d{4})-(\d{4})\)(.*)$')
    for line in source.splitlines():
        found=pattern.match(line)
        if found:
            name,country,goals,caps,first,last,notes=found.groups()
            records.append(dict(name=name.strip(),country=country,goals=int(goals),caps=int(caps),first_year=int(first),last_year=int(last),notes=notes.strip(),goals_per_cap=int(goals)/int(caps),source_date='2026-01-01'))
    frame=pd.DataFrame(records);assert len(frame)>200 and frame.goals.min()>=30
    store('soccer_documented_international_scorers',frame)
    audit['international_scorers']={'players':len(frame),'first_career_year':int(frame.first_year.min()),'source_cutoff':'2026-01-01','selection':'Published 30+ international goals list. Not an all-player population or full club-career dataset.',
                                   'candidates':frame[frame.name.str.contains('Messi|Cristiano|Maradona|Pel',case=False)][['name','goals','caps','notes']].to_dict('records')}


def value_features():
    parts=[]
    for kind in ['bat','pitch']:
        d=pd.read_csv(ROOT/f'baseball/value/war_daily_{kind}.csv',na_values=['NULL'],low_memory=False)
        d=d[d.year_ID<=2025].copy()
        assert not d.duplicated(['player_ID','year_ID','team_ID','stint_ID','lg_ID']).any()
        store('baseball_war_'+kind,d)
        parts.append(d[['player_ID','name_common','year_ID','WAR']])
    years=pd.concat(parts).groupby(['player_ID','name_common','year_ID'],as_index=False).WAR.sum(min_count=1)
    careers=years.groupby(['player_ID','name_common'],as_index=False).agg(total_war=('WAR','sum'),seasons=('year_ID','nunique'),first_year=('year_ID','min'),last_year=('year_ID','max'))
    peak=years.groupby('player_ID').WAR.apply(lambda x:x.nlargest(7).sum()).rename('best_seven_seasons_war')
    careers=careers.merge(peak,on='player_ID',validate='one_to_one')
    store('baseball_all_contributions_war_seasons',years)
    store('baseball_all_contributions_war_careers',careers)
    ruth=careers[careers.player_ID.eq('ruthba01')].iloc[0]
    assert round(float(ruth.total_war),1)==182.6
    audit['baseball_value']={'batting_rows':len(parts[0]),'pitching_rows':len(parts[1]),'players':len(careers),'first':int(years.year_ID.min()),'last':int(years.year_ID.max()),
                            'leaders':careers.nlargest(5,'total_war')[['name_common','total_war','best_seven_seasons_war']].to_dict('records'),
                            'definition':'Batting/fielding/baserunning/position WAR plus pitching WAR; sum team stints once. Source model incorporates era and park/context adjustments. WAR is model-dependent, not direct skill or causal evidence.'}
    nba=pd.read_sql_query('SELECT * FROM nba_baa_advanced',con)
    career=nba.groupby(['player_id','player'],as_index=False).agg(career_ws=('ws','sum'),career_vorp=('vorp',lambda x:x.sum(min_count=1)),seasons=('season','nunique'),vorp_observed_seasons=('vorp','count'))
    peak=nba.groupby('player_id').ws.apply(lambda x:x.nlargest(7).sum()).rename('best_seven_seasons_ws')
    career=career.merge(peak,on='player_id',validate='one_to_one')
    career['vorp_covers_recorded_career']=career.vorp_observed_seasons.eq(career.seasons)
    store('nba_value_and_peak_careers',career)
    audit['nba_value']={'players':len(career),'rows':len(nba),'note':'Win Shares, peak seven seasons, and VORP retained as distinct measures. VORP is missing before its historical coverage; missing periods are not zeros.'}


def clock(timestamp):
    h,m,s=timestamp.split(':');return 3600*float(h)+60*float(m)+float(s)


def soccer():
    matches=pd.read_sql_query('SELECT * FROM soccer_available_matches',con).set_index('match_id')
    all_rows=[]; checks=[]; total_events=0;clock_warning_events=defaultdict(int)
    paths=sorted((ROOT/'soccer/events').glob('*.json'));assert len(paths)==1130
    for n,path in enumerate(paths,1):
        mid=int(path.stem); events=json.loads(path.read_text()); total_events+=len(events)
        assert len({e['id'] for e in events})==len(events)
        meta=matches.loc[mid]; teams={}
        for e in events:
            if e['type']['name']=='Starting XI':teams[e['team']['id']]=e['team']['name']
        duration={}
        for e in events:
            if e['type']['name']=='Half End' and e['period']<=4:duration[e['period']]=max(duration.get(e['period'],0),clock(e['timestamp']))
        periods=sorted(duration); offsets={p:sum(duration[x] for x in periods if x<p) for p in periods}
        active={tid:set() for tid in teams}; rows={}; flags=[]; warnings=[]
        def participant(pid,tid,name):
            key=(pid,tid)
            if key not in rows:rows[key]=dict(match_id=mid,player_id=pid,team_id=tid,player=name,team=teams.get(tid,''),seconds=0.,goals=0,np_goals=0,shots=0,np_xg=0.,xg=0.,missing_xg_shots=0,missing_np_xg_shots=0,assists=0,passes=0,completed_passes=0,starting_position=None)
            return rows[key]
        goals=defaultdict(int); own_for={e['id'] for e in events if e['type']['name']=='Own Goal For'}
        related_for={rel for e in events if e['id'] in own_for for rel in e.get('related_events',[])}
        for p in periods:
            previous=0.;raw_previous=0.
            for e in (x for x in events if x['period']==p):
                raw_t=clock(e['timestamp']);t=min(raw_t,duration[p]);delta=max(0.,t-previous)
                if raw_t>duration[p]+1e-6:warnings.append('event_after_period_end')
                if raw_t+1e-6<raw_previous:
                    warnings.append('nonmonotonic_event_clock');clock_warning_events[e['type']['name']]+=1
                raw_previous=max(raw_previous,raw_t)
                if t+1e-6<previous:
                    if e['type']['name'] in ['Substitution','Player Off','Player On','Bad Behaviour'] or e.get('foul_committed',{}).get('card',{}).get('name') in ['Red Card','Second Yellow']:
                        flags.append('nonmonotonic_participation_clock')
                for tid,players in active.items():
                    for pid in players:rows[(pid,tid)]['seconds']+=delta
                previous=max(previous,t)
                tid=e.get('team',{}).get('id');pid=e.get('player',{}).get('id');kind=e['type']['name']
                if kind=='Starting XI':
                    for player in e['tactics']['lineup']:
                        row=participant(player['player']['id'],tid,player['player']['name']);row['starting_position']=player['position']['name'];active[tid].add(player['player']['id'])
                if pid is not None:
                    row=participant(pid,tid,e['player']['name'])
                    if kind in ['Shot','Pass'] and pid not in active.get(tid,set()):flags.append('event_by_inactive_player')
                    if kind=='Shot':
                        row['shots']+=1
                        shot_xg=e['shot'].get('statsbomb_xg')
                        if shot_xg is None:row['missing_xg_shots']+=1
                        else:row['xg']+=shot_xg
                        penalty=e['shot'].get('type',{}).get('name')=='Penalty'
                        if not penalty:
                            if shot_xg is None:row['missing_np_xg_shots']+=1
                            else:row['np_xg']+=shot_xg
                        if e['shot']['outcome']['name']=='Goal':
                            goals[tid]+=1;row['goals']+=1
                            if not penalty:row['np_goals']+=1
                    if kind=='Pass':
                        row['passes']+=1;row['completed_passes']+=int('outcome' not in e['pass']);row['assists']+=int(e['pass'].get('goal_assist',False))
                    if kind=='Substitution':
                        active[tid].discard(pid);replacement=e['substitution']['replacement'];participant(replacement['id'],tid,replacement['name']);active[tid].add(replacement['id'])
                    if kind=='Player Off':active[tid].discard(pid)
                    if kind=='Player On':active[tid].add(pid)
                    card=e.get('foul_committed',{}).get('card',e.get('bad_behaviour',{}).get('card',{})).get('name')
                    if card in ['Red Card','Second Yellow']:active[tid].discard(pid)
                if kind=='Own Goal For':goals[tid]+=1
                if kind=='Own Goal Against' and e['id'] not in related_for and not own_for.intersection(e.get('related_events',[])):
                    opponents=set(teams)-{tid}
                    if len(opponents)==1:goals[next(iter(opponents))]+=1
                if any(len(ids)>11 for ids in active.values()):flags.append('more_than_eleven_active')
            for tid,players in active.items():
                for pid in players:rows[(pid,tid)]['seconds']+=max(0.,duration[p]-previous)
        for tid,name in teams.items():
            expected=int(meta.home_score if name==meta.home else meta.away_score)
            if goals[tid]!=expected:flags.append('score_mismatch')
        if not {1,2}.issubset(periods):flags.append('missing_period_end')
        for row in rows.values():
            if row['seconds']>sum(duration.values())+1e-5:flags.append('exposure_exceeds_match')
        for row in rows.values():
            row.update(competition=meta.competition,season=meta.season,gender=meta.gender,quality_pass=not flags)
            if row['missing_xg_shots']:row['xg']=np.nan
            if row['missing_np_xg_shots']:row['np_xg']=np.nan
        all_rows.extend(rows.values());checks.append(dict(match_id=mid,events=len(events),seconds=sum(duration.values()),flags=','.join(sorted(set(flags))),warnings=','.join(sorted(set(warnings))),quality_pass=not flags))
        if n%200==0:print(f'Football audited: {n}/{len(paths)}',flush=True)
    frame=pd.DataFrame(all_rows);check=pd.DataFrame(checks)
    store('soccer_event_player_matches',frame);store('soccer_event_quality',check)
    season=frame.groupby(['competition','season','gender','player_id','player'],as_index=False)[['seconds','goals','np_goals','shots','np_xg','xg','missing_xg_shots','missing_np_xg_shots','assists','passes','completed_passes']].sum(min_count=1)
    season.loc[season.missing_xg_shots.gt(0),'xg']=np.nan
    season.loc[season.missing_np_xg_shots.gt(0),'np_xg']=np.nan
    season['np_goals_per_90']=season.np_goals*5400/season.seconds.replace(0,np.nan)
    store('soccer_observed_player_seasons',season)
    liga=frame[frame.competition.eq('La Liga') & frame.season.eq('2015/2016')]
    assert liga.match_id.nunique()==380
    liga_stats=season[season.competition.eq('La Liga') & season.season.eq('2015/2016')]
    messi=frame[frame.competition.eq('La Liga') & frame.player_id.eq(5503)]
    audit['soccer_events']={'matches':len(paths),'events':total_events,'player_match_rows':len(frame),'players':int(frame.player_id.nunique()),'quality_pass_matches':int(check.quality_pass.sum()),'flag_counts':check['flags'].value_counts().to_dict(),'warning_counts':check['warnings'].value_counts().to_dict(),'missing_xg_shots':int(frame.missing_xg_shots.sum()),'clock_warning_events':dict(clock_warning_events),
                            'complete_liga_2015_16':{'matches':380,'players':int(liga.player_id.nunique()),'quality_pass_matches':int(check[check.match_id.isin(liga.match_id)].quality_pass.sum()),'candidate_rows':liga_stats[liga_stats.player_id.isin([5503,5246,5207])].to_dict('records')},
                            'messi_liga':{'observed_matches':int(messi.match_id.nunique()),'observed_goals':int(messi.goals.sum()),'official_matches':520,'official_goals':474,'source':'https://www.fcbarcelona.com/en/card/2214377/leo-messi'},
                            'exposure_definition':'Elapsed playing seconds, including added time and extra time, reconstructed from period clocks, Starting XI, substitutions, red cards, Player Off/On. Shootouts excluded. Roster listing is not exposure. Flags are retained; rates are descriptive, not complete skill.'}
    checkpoint()



def selection_panels():
    labels=pd.read_sql_query('SELECT * FROM published_all_time_recognition',con)
    def finish(frame,sport,role,cutoff,table):
        subset=labels[labels.sport.eq(sport)]
        if sport=='hockey':subset=subset[subset.selection_role.eq('G') if role=='goalie' else subset.selection_role.ne('G')]
        selected=set(subset.source_player_id.dropna())
        key='player_id' if sport=='basketball' else 'playerId'
        frame['all_time_selection']=frame[key].astype(str).isin(selected)
        frame['feature_last_completed_season']=cutoff
        frame['selection']= 'NBA75' if sport=='basketball' else 'NHL100'
        assert not frame[key].duplicated().any()
        store(table,frame)
        return dict(players=len(frame),selected=int(frame.all_time_selection.sum()),cutoff=cutoff,role=role,table=table)
    totals=pd.read_sql_query('SELECT * FROM nba_baa_player_seasons WHERE season<=2021',con)
    nba=totals.groupby('player_id',as_index=False).agg(player=('player','last'),games=('g','sum'),points=('pts','sum'),seasons=('season','nunique'),first_season=('season','min'))
    nba['points_per_game']=nba.points/nba.games.replace(0,np.nan)
    advanced=pd.read_sql_query('SELECT * FROM nba_baa_advanced WHERE season<=2021',con)
    measures=advanced.groupby('player_id',as_index=False).agg(win_shares=('ws',lambda x:x.sum(min_count=1)),ws_observed_seasons=('ws','count'),vorp_observed_sum=('vorp',lambda x:x.sum(min_count=1)),vorp_observed_seasons=('vorp','count'),best_seven_seasons_ws=('ws',lambda x:x.nlargest(7).sum(min_count=1)))
    nba=nba.merge(measures,on='player_id',validate='one_to_one')
    nba['vorp_covers_recorded_career']=nba.vorp_observed_seasons.eq(nba.seasons)
    panels=[finish(nba,'basketball','all NBA/BAA players',2021,'nba75_selection_panel')]
    for role in ['skater','goalie']:
        d=pd.read_sql_query(f'SELECT * FROM nhl_{role}_regular WHERE seasonId<=20152016',con)
        if role=='skater':
            frame=d.groupby('playerId',as_index=False).agg(player=('skaterFullName','last'),position=('positionCode','last'),games=('gamesPlayed','sum'),goals=('goals','sum'),assists=('assists','sum'),points=('points','sum'),seasons=('seasonId','nunique'),first_season=('seasonId','min'),best_seven_seasons_points=('points',lambda x:x.nlargest(7).sum(min_count=1)))
            frame['points_per_game']=frame.points/frame.games.replace(0,np.nan)
        else:
            frame=d.groupby('playerId',as_index=False).agg(player=('goalieFullName','last'),games=('gamesPlayed','sum'),wins=('wins',lambda x:x.sum(min_count=1)),shutouts=('shutouts',lambda x:x.sum(min_count=1)),seasons=('seasonId','nunique'),first_season=('seasonId','min'))
            observed=d[d.saves.notna() & d.shotsAgainst.notna()]
            saves=observed.groupby('playerId',as_index=False).agg(observed_saves=('saves','sum'),observed_shots_against=('shotsAgainst','sum'),save_observed_seasons=('seasonId','nunique'))
            frame=frame.merge(saves,on='playerId',how='left',validate='one_to_one')
            frame['observed_save_percentage']=frame.observed_saves/frame.observed_shots_against.replace(0,np.nan)
            frame['saves_cover_recorded_career']=frame.save_observed_seasons.eq(frame.seasons)
        panels.append(finish(frame,'hockey',role,20152016,f'nhl100_{role}_selection_panel'))
    assert panels[0]['selected']==76
    assert sum(p['selected'] for p in panels[1:])==100
    audit['selection_panels']={'panels':panels,'interpretation':'All recorded comparison players before selection; regular seasons only. NBA through 2020/21, NHL through 2015/16, before the 2021/2017 selection dates. Different endpoints and cutoff ages; no common GOAT rank or universal model. ABA/WHA contributions excluded from these league panels. Best seven seasons are not required to be consecutive.'}
    # Refresh the three actual comparison-player rows from the completed football audit.
    q=pd.read_sql_query("SELECT * FROM soccer_observed_player_seasons WHERE competition='La Liga' AND season='2015/2016' AND player_id IN (5503,5246,5207)",con)
    audit['soccer_events']['complete_liga_2015_16']['candidate_rows']=q.to_dict('records')
    checkpoint()


def primary_nfl():
    records=[];availability=[]
    for path in sorted((ROOT/'american_football/official_careers').glob('*.html')):
        try:
            tables=pd.read_html(path,na_values=['--'],flavor='lxml')
        except ValueError:
            availability.append(dict(file=path.name,status='no_stat_tables'));continue
        candidates=[t for t in tables if {'YEAR','ATT','COMP','YDS','TD','INT'}.issubset(t.columns)]
        if len(candidates)!=1:
            availability.append(dict(file=path.name,status='ambiguous_or_absent_passing_table'));continue
        d=candidates[0].copy()
        totals=d[d.YEAR.astype(str).eq('TOTAL')]
        seasons=d[~d.YEAR.astype(str).eq('TOTAL')].copy()
        for col in ['ATT','COMP','YDS','TD','INT']:
            seasons[col]=pd.to_numeric(seasons[col],errors='coerce')
        errors=[]
        if len(totals)!=1:errors.append('missing_career_total')
        else:
            for col in ['ATT','COMP','YDS','TD','INT']:
                expected=pd.to_numeric(totals[col],errors='coerce').iloc[0]
                if pd.notna(expected) and seasons[col].sum(min_count=1)!=expected:errors.append('total_mismatch_'+col)
        seasons['YEAR']=pd.to_numeric(seasons.YEAR,errors='coerce')
        seasons=seasons[seasons.YEAR.notna() & (seasons.YEAR<=2025)]
        player=BeautifulSoup(path.read_bytes(),'html.parser').title.get_text().split(' Career Stats')[0].strip()
        seasons['player']=player;seasons['source_slug']=path.stem
        seasons['quality_pass']=not errors
        records.extend(seasons.to_dict('records'));availability.append(dict(file=path.name,status='passing_table',flags=','.join(errors),seasons=len(seasons)))
    frame=pd.DataFrame(records);assert len(frame)>100
    store('nfl_official_passing_seasons',frame)
    careers=frame.groupby(['source_slug','player'],as_index=False)[['ATT','COMP','YDS','TD','INT']].sum(min_count=1)
    store('nfl_official_passing_careers',careers);store('nfl_official_page_quality',pd.DataFrame(availability))
    selected=careers[careers.player.str.contains('Montana|Brady|Unitas|Graham|Baugh')]
    audit['nfl_official']={'pages':len(availability),'passing_table_pages':sum(r['status']=='passing_table' for r in availability),'player_seasons':len(frame),'first':int(frame.YEAR.min()),'last':int(frame.YEAR.max()),'players':int(frame.source_slug.nunique()),'failed_reconciliation':sum(bool(r.get('flags')) for r in availability),'candidate_totals':selected.to_dict('records'),
                           'scope':'Primary NFL.com full recorded careers for a documented candidate roster. Not a verified census; unavailable pages, league definitions, and missing early fields remain explicit. Do not splice unreconciled nflverse values into official careers.'}
    checkpoint()



def hof_careers():
    roster=json.loads((ROOT/'american_football/hof_careers/roster.json').read_text())
    records=[];career_rows=[];statuses=[]
    for player in roster:
        path=ROOT/f"american_football/hof_careers/{player['slug']}.html"
        try: tables=pd.read_html(path,flavor='lxml',na_values=['--','-'])
        except ValueError:statuses.append(dict(player=player['player'],slug=player['slug'],status='no_tables'));continue
        blocks=[]
        for d in tables:
            for i,row in d.iterrows():
                text=[str(x).strip().lower().rstrip('.') for x in row]
                if 'comp' in text and 'att' in text and 'int' in text:
                    mapping={}
                    for dest,choices in [('ATT',['att']),('COMP',['comp']),('YDS',['yds','yards']),('TD',['td','tds']),('INT',['int'])]:
                        mapping[dest]=next(j for j,v in enumerate(text) if v in choices)
                    blocks.append((d,i,mapping));break
        if len(blocks)!=1:statuses.append(dict(player=player['player'],slug=player['slug'],status='no_unique_passing_table'));continue
        d,start,mapping=blocks[0];season_records=[];total_records=[]
        for i,row in d.iloc[start+1:].iterrows():
            label=str(row.iloc[0]).strip()
            if label.lower()=='career':label='Career Total'
            if label.lower() in ['career total','career totals']:label='Career Total'
            if label.lower()=='year':break  # Secondary defensive/kicking section.
            numeric=re.fullmatch(r'\d{4}',label)
            if not numeric and not label.lower().startswith('career total'):continue
            record={key:pd.to_numeric(str(row.iloc[j]).replace(',',''),errors='coerce') for key,j in mapping.items()}
            record.update(player=player['player'],source_slug=player['slug'])
            if numeric:
                record.update(year=int(label),team=str(row.iloc[1]),games=pd.to_numeric(row.iloc[2],errors='coerce'))
                participation=str(row.iloc[2]).lower()
                record['passing_recording_era']='before_official_1932_records' if int(label)<1932 else 'official_recording_era'
                record['participation_status']='did_not_play' if 'did not play' in participation or 'missed season' in participation else 'recorded_or_unknown'
                if record['participation_status']=='did_not_play':
                    record.update({key:0 for key in mapping});record['games']=0
                record['league_source_label']='AAFC' if 'AAFC' in record['team'] else 'AFL' if 'AFL' in record['team'] else 'unspecified'
                if player['slug']=='otto-graham' and record['year']>=1950:record['league_source_label']='NFL'
                season_records.append(record)
            else:
                record['total_scope']=label
                total_records.append(record)
        if not season_records:statuses.append(dict(player=player['player'],slug=player['slug'],status='no_year_rows'));continue
        f=pd.DataFrame(season_records);assert not f.duplicated(['year','team']).any(),player
        general=[r for r in total_records if r['total_scope'].lower()=='career total']
        errors=[]
        if (f.year<1932).any():errors.append('pre_1932_unofficial_or_incomplete')
        if len(general)!=1:errors.append('no_unique_all_leagues_career_total')
        else:
            for col in mapping:
                expected=general[0][col];observed=f[col].sum(min_count=1)
                if pd.notna(expected) and observed!=expected:errors.append('total_mismatch_'+col)
                if f[col].isna().any():errors.append('unobserved_seasons_'+col)
        f['reconciliation_pass']=not errors
        records.extend(f.to_dict('records'));career_rows.extend(total_records)
        statuses.append(dict(player=player['player'],slug=player['slug'],status='passing_table',flags=','.join(errors),seasons=len(f),first=int(f.year.min()),last=int(f.year.max())))
    frame=pd.DataFrame(records);careers=pd.DataFrame(career_rows);status=pd.DataFrame(statuses)
    store('nfl_hof_recorded_passing_seasons',frame);store('nfl_hof_published_passing_totals',careers);store('nfl_hof_page_quality',status)
    baugh=careers[careers.source_slug.eq('sammy-baugh') & careers.total_scope.eq('Career Total')].iloc[0]
    assert baugh.YDS==21886 and baugh.TD==187
    graham=careers[careers.source_slug.eq('otto-graham') & careers.total_scope.eq('Career Total')].iloc[0]
    assert graham.YDS==23584 and graham.TD==174
    # Compare explicit source scopes: NFL.com may sum correctly while omitting early careers.
    primary=pd.read_sql_query('SELECT * FROM nfl_official_passing_careers',con)
    comparison=[]
    for _,r in careers[careers.total_scope.eq('Career Total')].iterrows():
        q=primary[primary.source_slug.eq(r.source_slug)]
        if len(q)==1:
            other=q.iloc[0];comparison.append(dict(player=r.player,hof_scope=r.total_scope,hof_yards=r.YDS,nflcom_recorded_yards=other.YDS,yards_difference=r.YDS-other.YDS,source_slug=r.source_slug))
    compare=pd.DataFrame(comparison);store('nfl_primary_scope_comparisons',compare)
    audit['nfl_hof']={'profiles':len(roster),'passing_profiles':int(status.status.eq('passing_table').sum()),'player_seasons':len(frame),'first':int(frame.year.min()),'last':int(frame.year.max()),'flagged_profiles':status[status['flags'].fillna('').ne('')].fillna('').to_dict('records') if 'flags' in status else [],'candidate_published_totals':careers[careers.source_slug.isin(['sammy-baugh','otto-graham','joe-montana','johnny-unitas'])].to_dict('records'),'scope_differences':compare[compare.yards_difference.ne(0)].to_dict('records'),'scope':'Selected historical HOF quarterbacks; not an all-player census. Published combined and NFL/AAFC career totals remain separate. Missing early measures and reconciliation errors are flagged.'}
    audit['nfl_official']['scope']='NFL.com recorded passing tables for a documented candidate roster, starting in 1950. Reconciliation validates displayed totals, not career completeness. Baugh loses 1937--1949; Graham excludes AAFC. Hall of Fame records provide separately scoped historical totals. Not a verified census.'
    checkpoint()


def report():
    manifest=json.loads((ROOT/'manifest.json').read_text());size=sum(e['bytes'] for e in manifest.values())
    for name,entry in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==entry['sha256'],name
    audit['verified_raw_bytes']=size;audit['verified_source_files']=len(manifest);checkpoint()
    b=audit['baseball_value'];s=audit['soccer_events'];n=audit.get('nfl_official',{})
    text=f'''# Better data for all-time player comparisons

Verified source archive: **{size/1e9:.3f} GB**, **{len(manifest):,} files**. Raw downloads are counted once; generated tables are excluded. File hashes are verified. The [manifest](manifest.json) records URLs, retrieval dates, versions, and checksums. Analysis tables are in [historical_players.sqlite](derived/historical_players.sqlite); [quality_audit.json](derived/quality_audit.json) records coverage and flags.

## Material improvements

**Baseball value rather than home runs alone.** Direct [Baseball Reference WAR exports](https://www.baseball-reference.com/about/war_explained.shtml) provide {b['batting_rows']:,} batting/value rows and {b['pitching_rows']:,} pitching rows through 2025. They include batting, fielding, baserunning, position, pitching, and context adjustments. Summing batting/value and pitching WAR yields Ruth at **182.62**, matching his published 182.6 after rounding, and first in the retrieved career population. His pitching contributes 20.36 WAR. His absence from first place in career home runs is not evidence against comprehensive career dominance. WAR remains a model with historical measurement limits.

**Football performance and denominators.** StatsBomb exports now include **{s['events']:,} events in {s['matches']:,} matches**, producing {s['player_match_rows']:,} player-match records and {s['players']:,} player identities. Measures include goals, non-penalty goals, xG, non-penalty xG, assists, shots, passes, and reconstructed playing seconds. This includes the complete **380-match La Liga 2015/16** season and the available Messi-era seasons and men's/women's World Cups. Bench listing is not counted as playing time, and shootouts are excluded.

**Football checks.** All {s['quality_pass_matches']:,} matches reproduce source match scores and pass participation-clock and exposure bounds. Raw event clocks retain backward-clock warnings in {sum(v for k,v in s['warning_counts'].items() if 'nonmonotonic' in k)} matches (event types and counts are recorded in the audit); {sum(v for k,v in s['warning_counts'].items() if 'event_after' in k)} matches contain an event timestamp beyond its recorded period end. Elapsed exposure uses nondecreasing clocks clamped to recorded period ends; no substitution, dismissal or on/off event reverses the clock. These warnings are stored separately in `soccer_event_quality`, rather than erased. All shots have source xG values. Missing values remain missing if a later source lacks them. Rates must use an explicit quality filter and comparison population. Messi's observed La Liga sample has **{s['messi_liga']['observed_matches']} appearances and {s['messi_liga']['observed_goals']} goals**; [Barcelona documents 520 and 474](https://www.fcbarcelona.com/en/card/2214377/leo-messi). The difference is a coverage check, not an invented missing observation. Selected historical World Cup matches are not full historical careers.

**International football career denominators.** [RSSSF's documented 30+ goals list](https://www.rsssf.org/miscellaneous/century.html) supplies {audit['international_scorers']['players']} players with career caps and goals, with a stated January 2026 cutoff. This avoids treating the older incomplete goal-event list as complete career totals. It remains a selected scoring population, includes country/eligibility footnotes, and does not measure full club careers or comparable opposition strength.

**Published all-time recognition.** Official [NBA75](https://www.nba.com/news/nba-75th-anniversary-team-announced), [NHL100](https://www.nhl.com/news/100-greatest-nhl-players-complete-list-286199184), and [NFL100 quarterbacks](https://www.nfl.com/news/nfl-100-all-time-team-quarterbacks-announced-0ap3000001091949) supply 76, 100, and 10 named selections with distinct dates. These are all-time elite selections, not 186 independent GOATs or a common ranking. The source names and unresolved identity matches are retained. Future features must be cut off at each selection date to avoid using later achievements to explain an earlier selection.

**NFL primary records.** {n.get('passing_table_pages',0)} directly downloaded NFL.com passing tables yield {n.get('player_seasons',0):,} recorded player-seasons, from {n.get('first','pending')} through {n.get('last','pending')}. The candidate roster includes pre-1999 NFLverse quarterbacks, the ten NFL100 quarterbacks, and established recorded passers with at least 1,500 attempts. Each table's season sums are checked against its displayed career totals. {n.get('failed_reconciliation',0)} tables fail that check, but this does **not** verify whole-career completeness: NFL.com begins in 1950 for the retrieved historical tables. Baugh's displayed 2,386 yards omit 1937–1949. The archived 2016 NFL.com mirror is preserved as an auxiliary source but is rejected as a complete population because it omitted Montana and Graham. Primary records are not silently patched with nflverse's differing aggregates.

**Earlier NFL records and league scope.** {audit['nfl_hof']['profiles']} Hall of Fame quarterback profiles supply {audit['nfl_hof']['passing_profiles']} passing tables and {audit['nfl_hof']['player_seasons']} year rows spanning 1927–2015; two profiles contain no passing table. Pre-1932 passing records are explicitly flagged as unofficial or incomplete, including apparent zeros. [Baugh's Hall of Fame table](https://www.profootballhof.com/players/sammy-baugh) supplies his full 21,886 passing yards and 187 touchdowns. [Graham's table](https://www.profootballhof.com/players/otto-graham) distinguishes 13,499 NFL yards from 23,584 NFL-plus-AAFC yards. Tittle's displayed career total does not reconcile to the source's combined season rows and is flagged; source league totals are not silently pooled. Published source totals, observed year rows, and quality flags are separate tables.

**Recognition features fixed before selection.** The NBA75 panel contains 4,586 recorded NBA/BAA players, including all 76 selections, with features through 2020/21. NHL100 panels contain 6,673 skaters and 758 goalies through 2015/16, with all 85 selected skaters and 15 selected goalies matched by identity and published role. Regular-season total contribution, output rates, best-seven-season peaks, and missing advanced-stat coverage are explicit fields. These panels contain comparison players and avoid later-career leakage. They are inputs for testing elite recognition, not a fitted universal GOAT model. NBA/BAA and NHL features exclude ABA and WHA contributions.

## Research scope

Peak performance, accumulated contribution, output rate, longevity, team success, and recognition are distinct outcomes. These sources materially improve the available measures and comparisons, but no byte count, small scoring-rate gap, or single value model establishes a universal GOAT rule. Women's soccer events are included; historical player populations for women's basketball, handball, volleyball, and water polo remain gaps. Missing early-era fields stay missing. Football xG is a provider model; elapsed seconds include stoppage time and are not identical to published regulation-minute denominators.

Reproduce the base archive and database with `python collect_historical.py` and `python audit_historical.py`, then run `python collect_better.py` and `python audit_better.py`. Python dependencies are pandas, NumPy, Beautiful Soup and lxml. Collection is resumable; the downloaded manifest is the authoritative snapshot, while a fresh collection can reflect later source releases. The auditor adds tables to the existing database without replacing the original source files. The raw data remain subject to their source agreements; StatsBomb attribution is required for shared findings.

![StatsBomb](soccer/StatsBomb-logo.png)
'''
    (ROOT/'QUALITY.md').write_text(text)
    (ROOT/'COVERAGE.md').write_text('# Historical research data\n\nSee the current [data quality and coverage report](QUALITY.md), with verified source counts, historical populations, performance measures, recognition sources, and remaining gaps.\n')
    print('Quality report saved:',ROOT/'QUALITY.md',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--section',choices=['foundation','nfl','panels','hof','report']);options=parser.parse_args()
    if options.section in [None,'foundation']:recognized();value_features();soccer();checkpoint()
    if options.section in [None,'nfl']:primary_nfl()
    if options.section in [None,'panels']:selection_panels()
    if options.section in [None,'hof']:hof_careers()
    if options.section in [None,'report']:report()
    con.close()
