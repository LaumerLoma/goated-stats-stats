"""Audit downloads, construct historical player tables, and report career comparisons.

Run after collect_historical.py. Requires pandas and numpy. Never substitutes
zero for unavailable historical measures or duplicates multi-team totals.
"""
from pathlib import Path
import hashlib
import json
import sqlite3
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent / 'historical_data'
manifest = json.loads((ROOT / 'manifest.json').read_text())
output = ROOT / 'derived'
output.mkdir(exist_ok=True)
conn = sqlite3.connect(output / 'historical_players.sqlite')
audit = {'files': {}, 'coverage': {}, 'comparisons': {}}


def read(relative):
    return pd.read_csv(ROOT / relative, low_memory=False, encoding='utf-8-sig')


def save(name, data):
    data.to_sql(name, conn, if_exists='replace', index=False)


def coverage(name, data, season, player, key, note):
    assert not data.duplicated(key).any(), f'Duplicate observations: {name}'
    row = dict(rows=len(data), players=int(data[player].nunique()),
               first=int(data[season].min()), last=int(data[season].max()),
               seasons=int(data[season].nunique()), note=note)
    audit['coverage'][name] = row
    return row


def nba_canonical(data):
    keys = ['player_id', 'season', 'lg']
    assert not data.duplicated(keys + ['team']).any()
    aggregate = data.team.str.match(r'\dTM')
    agg_keys = pd.MultiIndex.from_frame(data.loc[aggregate, keys])
    split_keys = pd.MultiIndex.from_frame(data[keys])
    selected = data.loc[aggregate | ~split_keys.isin(agg_keys)].copy()
    assert not selected.duplicated(keys).any()
    return selected


def main():
    # This audits raw bytes, rather than counting generated database copies as downloads.
    for relative, entry in manifest.items():
        path = ROOT / relative
        assert path.stat().st_size == entry['bytes'], relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], relative
        info = {'bytes': entry['bytes']}
        if relative.endswith('.csv'):
            frame = read(relative)
            info.update(rows=len(frame), columns=list(frame.columns))
        audit['files'][relative] = info

    people = read('baseball/People.csv')
    batting = read('baseball/Batting.csv')
    coverage('baseball_batting_stints', batting, 'yearID', 'playerID',
             ['playerID', 'yearID', 'stint', 'teamID', 'lgID'],
             'Recorded league history including Negro Leagues; a team stint is not an independent athlete.')
    save('baseball_people', people)
    save('baseball_batting_stints', batting)
    for filename in ['Pitching','BattingPost','PitchingPost','Fielding','AwardsPlayers','AwardsSharePlayers','HallOfFame','Teams','SeriesPost']:
        save('baseball_' + filename.lower(), read('baseball/' + filename + '.csv'))
    # Simple total HR comparisons use AL/NL only; all other leagues remain in the raw database.
    mlb = batting[batting.lgID.isin(['AL', 'NL'])]
    hitters = mlb.groupby('playerID', as_index=False)[['AB','H','HR','BB']].sum(min_count=1)
    hitters = hitters.merge(people[['playerID','nameFirst','nameLast']], validate='one_to_one')
    hitters['name'] = hitters.nameFirst.fillna('') + ' ' + hitters.nameLast.fillna('')
    hitters['hr_per_ab'] = hitters.HR / hitters.AB.replace(0, np.nan)
    save('baseball_al_nl_careers', hitters)
    audit['comparisons']['baseball_hr'] = hitters.nlargest(5, 'HR')[['name','HR']].to_dict('records')
    assert int(hitters.loc[hitters.playerID.eq('ruthba01'), 'HR'].iloc[0]) == 714

    raw_nba = read('basketball/Player_Totals.csv')
    nba = raw_nba[(raw_nba.season <= 2025) & raw_nba.lg.isin(['NBA', 'BAA'])].copy()
    aggregate = nba.team.str.match(r'\dTM')
    split = nba[~aggregate].groupby(['player_id','season','lg'])[['g','pts']].sum()
    agg = nba[aggregate].set_index(['player_id','season','lg'])[['g','pts']]
    assert agg.eq(split.reindex(agg.index)).all().all(), 'Multi-team totals do not reconcile'
    nba = nba_canonical(nba)
    coverage('nba_baa_player_seasons', nba, 'season', 'player_id', ['player_id','season','lg'],
             'Season is ending year. NBA/BAA regular seasons through 2024/25; ABA separate; partial 2025/26 excluded.')
    save('nba_baa_player_seasons', nba)
    advanced = read('basketball/Advanced.csv')
    advanced = nba_canonical(advanced[(advanced.season <= 2025) & advanced.lg.isin(['NBA', 'BAA'])])
    save('nba_baa_advanced', advanced)
    for filename, table in [('Player Career Info.csv','nba_career_info'),('Player Award Shares.csv','nba_award_shares'),('Team_Summaries.csv','nba_team_summaries')]:
        save(table, read('basketball/'+filename))
    nc = nba.groupby('player_id', as_index=False).agg(player=('player','last'), points=('pts','sum'), games=('g','sum'), seasons=('season','nunique'))
    nc['points_per_game'] = nc.points / nc.games
    save('nba_baa_career_totals', nc)
    audit['comparisons']['nba_points'] = nc.nlargest(5,'points')[['player','points']].to_dict('records')
    audit['comparisons']['nba_ppg_500_games'] = nc[nc.games >= 500].nlargest(5,'points_per_game')[['player','points','games','points_per_game']].to_dict('records')
    audit['comparisons']['nba_excluded_partial_rows'] = int((raw_nba.season >= 2026).sum())
    jordan = nc[nc.player_id.eq('jordami01')].iloc[0]
    assert int(jordan.points) == 32292 and int(jordan.games) == 1072

    for report in ['skater','goalie','team']:
        for kind in [2,3]:
            data = pd.DataFrame([row for p in sorted((ROOT/'hockey').glob(f'{report}_summary_{kind}_*.json')) for row in json.loads(p.read_text())['data']])
            identity = 'teamId' if report == 'team' else 'playerId'
            name = f'nhl_{report}_{"regular" if kind==2 else "postseason"}'
            coverage(name, data, 'seasonId', identity, [identity,'seasonId'],
                     'NHL official API; traded players combined by season. Earliest fields can be unavailable.')
            save(name, data)
            if report == 'skater' and kind == 2:
                hc = data.groupby('playerId', as_index=False).agg(player=('skaterFullName','last'), points=('points','sum'), goals=('goals','sum'), assists=('assists','sum'), games=('gamesPlayed','sum'), seasons=('seasonId','nunique'))
                hc['points_per_game'] = hc.points / hc.games
                save('nhl_skater_career_totals', hc)
                audit['comparisons']['nhl_points'] = hc.nlargest(5,'points')[['player','points']].to_dict('records')
                audit['comparisons']['nhl_ppg_500_games'] = hc[hc.games >= 500].nlargest(5,'points_per_game')[['player','points','games','points_per_game']].to_dict('records')
                gretzky = hc[hc.player.eq('Wayne Gretzky')].iloc[0]
                assert int(gretzky.points) == 2857 and int(gretzky.games) == 1487

    for kind in ['reg','post']:
        nf = pd.concat([read(str(p.relative_to(ROOT))) for p in sorted((ROOT/'american_football').glob(f'stats_player_{kind}_*.csv'))], ignore_index=True)
        coverage('nfl_'+kind, nf, 'season','player_id',['player_id','season'],
                 '1999 onward only; earlier careers are truncated or absent. All recorded positions, not only quarterbacks.')
        save('nfl_'+kind, nf)
        if kind == 'reg':
            fc = nf.groupby('player_id', as_index=False).agg(player=('player_display_name','last'), passing_yards=('passing_yards','sum'), passing_tds=('passing_tds','sum'), attempts=('attempts','sum'), seasons=('season','nunique'))
            save('nfl_since_1999_career_totals', fc)
            audit['comparisons']['nfl_passing_yards_since_1999'] = fc.nlargest(5,'passing_yards')[['player','passing_yards']].to_dict('records')
            brady = fc[fc.player.eq('Tom Brady')].iloc[0]
            assert int(brady.passing_tds) == 649
            audit['comparisons']['nfl_brady_reconciliation'] = dict(
                archive_yards=int(brady.passing_yards), official_yards=89214,
                archive_attempts=int(brady.attempts), official_attempts=12050,
                source='https://www.nfl.com/players/tom-brady/stats/career',
                note='Archive totals differ by +2 yards and +2 attempts. Preserve raw data; exact career-rate claims require reconciliation.')

    matches = {}
    competitions = json.loads((ROOT/'soccer/competitions.json').read_text())
    for comp in competitions:
        for row in json.loads((ROOT/f'soccer/matches/{comp["competition_id"]}_{comp["season_id"]}.json').read_text()):
            mid = row['match_id']
            flattened = dict(match_id=mid, date=row['match_date'], competition=comp['competition_name'], season=comp['season_name'], gender=comp['competition_gender'], home=row['home_team']['home_team_name'], away=row['away_team']['away_team_name'], home_score=row['home_score'], away_score=row['away_score'])
            if mid in matches:
                assert matches[mid] == flattened
            matches[mid] = flattened
    sm = pd.DataFrame(matches.values())
    save('soccer_available_matches', sm)
    lineup_rows = []
    for path in sorted((ROOT/'soccer/lineups').glob('*.json')):
        mid = int(path.stem)
        for team in json.loads(path.read_text()):
            for player in team['lineup']:
                lineup_rows.append(dict(match_id=mid, team_id=team['team_id'], team=team['team_name'], player_id=player['player_id'], player=player['player_name'],
                                        has_playing_position=bool(player.get('positions')), positions=json.dumps(player.get('positions',[])), cards=json.dumps(player.get('cards',[]))))
    sl = pd.DataFrame(lineup_rows)
    assert not sl.duplicated(['match_id','team_id','player_id']).any()
    save('soccer_selected_lineups', sl)
    audit['coverage']['soccer_metadata'] = dict(matches=len(sm), first=sm.date.min(), last=sm.date.max(), competition_seasons=len(competitions), lineups_matches=int(sl.match_id.nunique()), lineup_players=int(sl.player_id.nunique()), lineup_rows=len(sl), note='Metadata for all available competitions; selected La Liga and World Cup lineups include substitutes. No event output data downloaded. Historical matches are selected, not full league history.')
    if (ROOT/'soccer/internationals/results.csv').exists():
        results = read('soccer/internationals/results.csv')
        goals = read('soccer/internationals/goalscorers.csv')
        save('soccer_mens_international_results', results)
        save('soccer_mens_international_goals', goals)
        keys = ['date','home_team','away_team']
        ambiguous = results.duplicated(keys, keep=False)
        recorded = goals.groupby(keys).size().rename('recorded_goals').reset_index()
        check = results[~ambiguous].merge(recorded, on=keys, how='left', validate='one_to_one')
        total_goals = results.home_score.sum() + results.away_score.sum()
        excess = check.recorded_goals.fillna(0) > check.home_score + check.away_score
        audit['coverage']['soccer_internationals'] = dict(matches=len(results), first=results.date.min(), last=results.date.max(), goal_rows=len(goals), first_goal=goals.date.min(), last_goal=goals.date.max(), documented_fraction=float(len(goals)/total_goals), ambiguous_match_keys=results[ambiguous].to_dict('records'), excess_goal_matches=check[excess].to_dict('records'), note='Men\'s internationals only; goalscorer coverage is incomplete, with no player appearance denominator or stable person IDs. Not a full career goals ranking. Ambiguous match keys are excluded from reconciliation.')

    audit['raw_bytes'] = sum(entry['bytes'] for entry in manifest.values())
    audit['raw_files'] = len(manifest)
    (output/'audit.json').write_text(json.dumps(audit, indent=2, allow_nan=False) + '\n')
    write_report(audit)
    conn.close()
    print(json.dumps({k:v for k,v in audit.items() if k != 'files'}, indent=2, allow_nan=False))


def write_report(audit):
    c, a = audit['coverage'], audit['comparisons']
    total_gap = 100 * (a['nhl_points'][0]['points']/a['nhl_points'][1]['points']-1)
    hockey_rate_gap = 100 * (a['nhl_ppg_500_games'][0]['points_per_game']/a['nhl_ppg_500_games'][1]['points_per_game']-1)
    nba_rate_gap = 100 * (a['nba_ppg_500_games'][0]['points_per_game']/a['nba_ppg_500_games'][1]['points_per_game']-1)
    rows = []
    for directory, label, scope, records in [
        ('baseball','Baseball','1871–2025',f"{c['baseball_batting_stints']['rows']:,} batting stints; {c['baseball_batting_stints']['players']:,} players"),
        ('basketball','Basketball','1946/47–2024/25',f"{c['nba_baa_player_seasons']['rows']:,} canonical NBA/BAA player-seasons; {c['nba_baa_player_seasons']['players']:,} players"),
        ('hockey','Hockey','1917/18–2025/26',f"{c['nhl_skater_regular']['rows']:,} regular-season skater records; {c['nhl_skater_regular']['players']:,} skaters"),
        ('american_football','American football','1999–2025',f"{c['nfl_reg']['rows']:,} regular-season player records; {c['nfl_reg']['players']:,} players"),
        ('soccer','Soccer','1872–2026 results; selected player data',f"{c['soccer_internationals']['matches']:,} men's internationals; {c['soccer_metadata']['lineups_matches']:,} StatsBomb lineups")]:
        size = sum(v['bytes'] for k,v in manifest.items() if k.startswith(directory+'/')) / 1048576
        rows.append(f'| {label} | {scope} | {size:.2f} | {records} |')
    text = f'''# Historical GOAT research archive

Downloaded **{audit['raw_bytes']:,} bytes ({audit['raw_bytes']/1048576:.2f} MiB)** in **{audit['raw_files']:,} source files**. This counts downloaded source bytes once and excludes the derived database, scripts, and reports. Every file has a source URL, retrieval timestamp, size, and SHA-256 checksum in [manifest.json](manifest.json).

The earlier recent-season and opening-month samples could assess encounter arithmetic. They could not establish all-time player greatness. This archive supplies historical comparison populations and complete recorded careers in several leagues; its remaining gaps are explicit.

## Coverage

| Sport | Analyzed historical scope | Raw MiB | Core records |
|---|---|---:|---|
''' + '\n'.join(rows) + f'''

Baseball also includes pitching, fielding, postseason, teams, awards, and Hall of Fame voting. NHL data include goalies, teams, and playoffs. NFL regular season and postseason are separate. Basketball includes advanced measures, team records, awards, and career metadata; its source covers regular seasons and preserves ABA records separately in raw files.

## What the historical data actually show

- **Gretzky:** 2,857 NHL regular-season points versus Jagr's 1,921, a **{total_gap:.2f}%** lead in accumulated points. Among skaters with at least 500 NHL games, Gretzky's 2,857/1,487 = 1.9213 points per game versus Lemieux's 1,723/915 = 1.8831 gives a **{hockey_rate_gap:.2f}%** lead. Those are two different dominance measures.
- **Jordan:** 32,292/1,072 = 30.1231 points per game versus Chamberlain's 31,419/1,045 = 30.0660, a **{nba_rate_gap:.2f}%** rate lead among NBA/BAA players with at least 500 games. Jordan ranks fifth in accumulated points through 2024/25; LeBron's total is 42,184 at that cutoff.
- **Ruth:** 714 AL/NL home runs rank behind Bonds (762) and Aaron (755). Raw accumulated home runs alone do not isolate the original selected GOAT candidate.

These are reproducible descriptive rankings, not significance tests or percentages of complete skill. Per-game rates do not adjust for pace, role, league strength, era, injuries, or career length. The 500-game filter defines the comparison population; it is not a validated greatness threshold. Changing the metric can change the ranking, without establishing that no other common pattern exists.

## Quality checks and limits

1. All downloaded files passed byte-count and SHA-256 verification. NHL requests are split into five-season windows: each response's returned count equals its advertised total, stays below the API's 10,000-record cap, and has unique player-season or team-season keys. That prevents silent global truncation.
2. Basketball's multi-team aggregate games and points exactly reconcile to their component team stints. Career totals keep the aggregate once and discard those overlapping stints. The archive contains **{a['nba_excluded_partial_rows']:,} partial 2025/26 rows**, retained raw and excluded from career comparisons.
3. Reference checks reproduce Ruth's 714 home runs, Jordan's 32,292 points in 1,072 games, and Gretzky's 2,857 points in 1,487 games. The NFL archive reports Brady at 89,216 yards and 12,052 attempts; [NFL.com](https://www.nfl.com/players/tom-brady/stats/career) reports 89,214 and 12,050. Raw values remain intact; that mismatch is flagged in the audit, and NFL-derived career rates are not presented as fully reconciled official records.
4. **NFL coverage is not all-time:** pre-1999 players are absent and careers straddling 1999 are truncated. It covers Brady's career but cannot supply a fair Montana–Brady or Unitas–Brady population comparison.
5. **Soccer coverage is not complete career coverage.** StatsBomb supplies {c['soccer_metadata']['matches']:,} available matches across {c['soccer_metadata']['competition_seasons']} competition-seasons, including women's competitions. Downloaded player lineups cover {c['soccer_metadata']['lineups_matches']:,} selected La Liga and men's/women's World Cup matches, with {c['soccer_metadata']['lineup_players']:,} named players and {c['soccer_metadata']['lineup_rows']:,} roster rows. A roster row can be a bench player. No football event-level performance archive has been collected here, and the Messi-era selection is not a league-wide historical census.
6. The international soccer archive has {c['soccer_internationals']['goal_rows']:,} goalscorer rows, starting {c['soccer_internationals']['first_goal']}, covering only **{100*c['soccer_internationals']['documented_fraction']:.1f}%** of all goals in its match results. Names lack stable person IDs and appearances are absent. Those rows cannot support full career scoring rates. Two Tahiti–New Caledonia results share the same date and teams with opposite scores; their ambiguous join key is quarantined from reconciliation. No other matched goalscorer group exceeds its match's total goals.
7. Missing early-era fielding, minutes, shots, or advanced statistics stay missing. Historical league coverage and Negro League record completeness differ. The principal baseball, basketball, NHL, and NFL populations are men's professional records; they do not establish a rule for women or all team sports. Historical handball, volleyball, and water-polo player populations are not supplied by this archive.
8. **GOAT recognition is not yet a measured outcome.** The named candidates come from the original question. Awards and Hall of Fame data can support recognition analyses but are not interchangeable with GOAT status, and recognition may itself use the statistics being tested. More rows do not create thousands of independently labelled GOATs.

## Sources and attribution

- [SABR / Sean Lahman Baseball Database](https://sabr.org/lahman-database/), official 2025 CSV release, including Negro League data credited to Seamheads. Downloaded directly from SABR's public Box folder. Copyright and CC BY-SA 3.0 terms are preserved in `baseball/readme2025.txt`.
- [Clarence Muchina's preserved basketball dataset](https://github.com/cmuchina3/nba-stats-1947-present-curated), originally compiled by Sumitro Datta from Basketball Reference. This is a public mirror, not a download from the NBA. Original source documentation and upstream rights cautions are retained; download URLs pin the repository revision.
- [NHL official statistics](https://www.nhl.com/stats/), via `api.nhle.com/stats/rest/en`, regular seasons and playoffs from 1917/18 through 2025/26. Old fields can be unavailable; source records are retained unmodified.
- [nflverse Player Summary Stats](https://github.com/nflverse/nflverse-data/releases/tag/stats_player), 1999–2025 REG and POST assets. [The project's documentation](https://nflreadr.nflverse.com/reference/load_player_stats) describes the goal of matching official statistics; the Brady check demonstrates a small discrepancy.
- [StatsBomb Open Data](https://github.com/hudl/open-data), historical match metadata and selected lineups. The source agreement and README are preserved locally. This independent analysis does not represent StatsBomb's views.
- [Mart Jürisoo's international football archive](https://github.com/martj42/international_results), men's results and partial goalscorer data. Original README and CC0 license are preserved; current team names represent historical successors.

![StatsBomb](soccer/StatsBomb-logo.png)

## Reproduce and query

Run `python collect_historical.py` to resume downloads, then `python audit_historical.py` to rebuild and audit the database. The collector uses public URLs without credentials; the auditor requires pandas and NumPy.

[historical_players.sqlite](derived/historical_players.sqlite) contains canonical player-season tables, career totals, separate postseason tables, selected source tables, and soccer metadata. [audit.json](derived/audit.json) contains machine-readable coverage, per-CSV row counts and schemas, rankings, and reconciliation flags. The database is a derived research artifact; the raw source files and manifest are the provenance record.
'''
    (ROOT/'COVERAGE.md').write_text(text)


if __name__ == '__main__':
    main()
