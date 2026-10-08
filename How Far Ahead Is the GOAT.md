# How Far Ahead Is the GOAT?

Oct 3, 2026 · @LaumerLoma

Every team sport has one name that ends the debate. This note asks two questions. Is the GOAT also ahead on team wins? And does the gap get smaller when the player pool gets bigger?

## Method

Team sports only. The KPI is **team titles at the highest level**, counted over the whole career. "Highest level" means:

- **NHL, NFL, NBA:** the league championship.
- **Football:** titles in the top five European leagues plus the European Cup / Champions League. Domestic cups, other leagues and national-team events do not count. This removes trophy counts built in weaker leagues.
- **Handball, volleyball, water polo:** the European club Champions League.
- **Lacrosse:** professional league titles (NLL, MLL).
- **Cycling:** Grand Tour wins. Riders race as a team, but one rider wins.

Two measures: **margin** = GOAT ÷ best other − 1, and **z** = (GOAT − mean of the next 10) ÷ SD of the next 10. League N is the number of players in the GOAT's competition today: teams × roster size. No statistical significance. The point is the mechanics.

## Data

| GOAT | Team titles | GOAT | Best other | Margin | z | League N |
| --- | --- | --- | --- | --- | --- | --- |
| Brady (NFL) | Super Bowls | 7 | 5 (Haley) | +40% | +9.2σ | \~1,700 (32 × 53) |
| Merckx (cycling) | Grand Tours | 11 | 10 (Hinault) | +10% | +2.7σ | \~180 (23 × 8) |
| Messi (football) | Top-5 leagues + UCL | 16 | 18 (Gento) | −11% | +0.9σ | \~2,400 (96 × 25) |
| Jordan (NBA) | NBA titles | 6 | 11 (Russell) | −45% | −1.3σ | \~450 (30 × 15) |
| Karabatić (handball) | EHF Champions League | 3 | 7 (Xepkin) | −57% | −7.8σ\* | \~260 (16 × 16) |
| Gretzky (NHL) | Stanley Cups | 4 | 11 (H. Richard) | −64% | −3.0σ | \~740 (32 × 23) |
| Estiarte (water polo) | European Cups | 2 | 7 (Figlioli) | −71% | −4.6σ\* | \~240 (16 × 15) |
| Kiraly (volleyball) | CEV Champions League | 1 | ≥5 (Mikhaylov) | ≤ −80% | n/a | \~280 (20 × 14) |
| Gait (lacrosse) | Pro league titles | 6 | not found | n/a | n/a | n/a |

\*Fewer than 10 comparison players found.

## Decomposition

- **Ahead on team titles:** Brady, Merckx.
- **Behind on team titles:** Messi, Jordan, Karabatić, Gretzky, Estiarte, Kiraly.
- **No data:** Gait.

Four GOATs also lead an individual stat: Gretzky (career points, +49%), Messi (Golden Shoes, +50%), Jordan (scoring titles, +43%) and Brady (passing TDs, +14%). Only Brady leads on both.

## Result

Team margin vs 1/N (eight sports): **ρ = −0.29**, p = 0.49. Team z vs 1/N (seven sports): ρ = −0.32, p = 0.48. The sign is negative: smaller competitions show smaller GOAT leads, not larger. Neither result is significant.

## What this shows

1. **Team titles reward dynasties, not the best player.** Most record holders are core players of dominant clubs: the 1960s Celtics and Canadiens, 1950s Real Madrid, Partizan, Pro Recco, 1990s Barcelona handball.
2. **The two leaders convert the team's work alone.** A quarterback finishes every drive. A Grand Tour rider wins after the team works for him.
3. **Era decides the rest.** Fewer teams made repeat titles easier.

## Teamwork index (first draft)

"GOAT team" vs "GOAT player". The **GOAT team** is the club with the most titles in any window as long as the GOAT player's career (L seasons). **Teamwork index** = GOAT team titles ÷ GOAT player titles. Below 1: the best player beats the best dynasty. Above 1: the best dynasty beats the best player.

### Men

| Sport | GOAT player | Titles | GOAT team (best run within L) | L | Titles | Index |
| --- | --- | --- | --- | --- | --- | --- |
| NFL | Brady | 7 | Patriots 2001–2018 ‡ (Brady's own team) | 23 | 6 | 0.9 |
| Cycling | Merckx | 11 | Sky/Ineos 2011–2021† | 14 | 12 | 1.1 |
| Football | Messi | 16 | Real Madrid 1953/54–1971/72† ‡½ (Messi's Barcelona is 2nd with 15) | 19 | 19 | 1.2 |
| NBA | Jordan | 6 | Celtics 1957–1969 | 15 | 11 | 1.8 |
| Handball | Karabatić | 3 | Barcelona 1991–2005† | 23 | 8 | 2.7 |
| NHL | Gretzky | 4 | Canadiens 1956–1975† | 20 | 11 | 2.8 |
| Water polo | Estiarte | 2 | Pro Recco 2003–2023† | 24 | 9 | 4.5 |
| Volleyball | Kiraly | 1 | Zenit Kazan 2008–2018† | 13 | 6 | 6.0 |

### Women

| Sport | GOAT player | Titles | GOAT team (best run within L) | L | Titles | Index |
| --- | --- | --- | --- | --- | --- | --- |
| Basketball (WNBA) | Taurasi | 3 | Comets 1997–2000, Lynx 2011–2017, Storm 2004–2020 (tie) | 20 | 4 | 1.3 |
| Football (UWCL) | Marta | 1† | Lyon 2011–2022 | 22 | 8 | 8.0 |
| Handball (EHF CL) | Neagu | 1 | Hypo Niederösterreich 1989–2000† | 20 | 8 | 8.0 |
| Cycling (Grand Tours) | van Vleuten | 6 | not yet counted | 16 | n/a | n/a |
| Ice hockey, volleyball, water polo, lacrosse | — | — | no long-running pro club competition with checked data | — | — | n/a |

†Counted from memory, not yet checked against a source. ‡Too much overlap: the GOAT team is the GOAT player's own team, so the index cannot separate player from team. ‡½ Partial overlap: the GOAT's own club is a close second.

First reading: only the NFL is below 1, but that row is flagged (‡): Brady's Patriots are the GOAT team. Cycling and men's football are close to 1; football has partial overlap (‡½). Handball, hockey, water polo and volleyball are clearly team-driven (index above 2.5). The women's numbers are much more team-driven than the men's: one club (Lyon, Hypo) won eight titles while the GOAT won one.

### Supplementary: national-team sports

*Caveat: these sports have no main club competition, so titles are Olympic golds won with a national team. A national team picks from a whole country, so the results are weighted by population and state funding. Use them as supplementary data only, whatever they suggest.*

| Sport | GOAT player | Titles | GOAT team (best run within L) | L | Titles | Index |
| --- | --- | --- | --- | --- | --- | --- |
| Rowing (all events) | Redgrave | 5 | East Germany 1972–1988† | 5 Games | \~30 | \~6 |
| Ice hockey (men) | Tretiak | 3 | USSR 1964–1976† ‡ | 4 Games | 4 | 1.3 |
| Ice hockey (women) | Wickenheiser | 4 | Canada 2002–2014 ‡ | 5 Games | 4 | 1.0 |
| Water polo (men) | Gyarmati | 3 | Hungary 1952–1964† ‡ | 5 Games | 3 | 1.0 |
| Water polo (women) | Steffens | 3 | USA 2012–2020 ‡ | 4 Games | 3 | 1.0 |
| Volleyball (women) | Regla Torres | 3 | Cuba 1992–2000 ‡ | 3 Games | 3 | 1.0 |

Five of six national rows are flagged (‡): the GOAT is the core of the dominant national team, so GOAT player and GOAT team are the same squad and the index sits near 1 by construction. Rowing is the exception, because one nation can win many boat classes at the same Games.

### With/without test for flagged rows (‡)

Overlap can mean two things: the GOAT made the team, or the team made the GOAT. To separate them, compare the team's title rate **with** the GOAT and **without** the GOAT. Ratio = rate with ÷ rate without. A high ratio means the team is less important than the player.

| Team | GOAT | With GOAT | Without GOAT | Ratio | Reading |
| --- | --- | --- | --- | --- | --- |
| Patriots (NFL) | Brady | 6 in 20 seasons | 0 in 46 seasons | ∞ | Player-driven\* |
| USA women (water polo) | Steffens | 3 of 4 Games | 0 of 3 Games | ∞ | Player-driven |
| Cuba women (volleyball) | Torres | 3 of 3 Games | 0 of 3 Games | ∞ | Player-driven |
| Canada women (ice hockey) | Wickenheiser | 4 of 5 Games | 1 of 3 Games | 2.4 | Player-driven |
| Barcelona (football) | Messi | 14 in 17 seasons | 10 in 22 seasons | 1.8 | Player-driven |
| Hungary (water polo) | Gyarmati | 3 of 5 Games | 3 of 5 Games | 1.0 | Team/system-driven |
| USSR (ice hockey) | Tretiak | 3 of 4 Games | 4 of 5 Games | 0.94 | Team/system-driven |

\*The Patriots' coach (Belichick) was there for the same 20 seasons, so this ratio measures Brady and Belichick together. Values are from memory†, except Canada's 2018–2026 results. Field hockey (Dhyan Chand) is excluded: too few competitions (three Olympic tournaments, with only three teams in 1932). The other Olympic rows also rest on only 3–5 Games per side, so treat them as weak evidence.

Result: in five of the seven flagged rows, the overlap means the GOAT made the team, so these sports move toward "player-driven". The USSR and Hungary kept winning at the same rate without their GOAT, so in those rows the team (or the national system) was the driver.

### Is there a split between team-driven and GOAT-driven sports?

Test: 10 clean club rows (men's and women's tables, NFL excluded for overlap). Model: log(teamwork index) is normal, and the mean depends on one sport feature. Fit by maximum likelihood (MLE) and compare with a model where all sports share one mean.

| Axis | Effect on index | LR test p | AIC (lower is better) |
| --- | --- | --- | --- |
| None (one mean for all) | — | — | **26.2** |
| Open European club system vs North American capped league | ×1.9 higher in open systems | 0.20 | 26.5 |
| Women vs men | ×1.8 higher for women | 0.23 | 26.7 |
| Open system + sex | ×1.9 and ×1.9 | 0.17 | 26.6 |
| Players on the field | ×1.0 per player | 0.76 | 28.1 |

Result: no axis beats "one mean for all". The best candidate is the league system. Open European systems (Champions League sports, no salary cap) let one rich club stack titles: Pro Recco, Zenit, Lyon, Hypo, Barcelona. Capped North American leagues (NBA, NHL, WNBA) spread titles, so the GOAT player gets closer to the GOAT team. The women-vs-men effect is mostly the same axis, because most women's rows are European. The number of players on the field shows no effect.

With 10 rows and many values from memory, this is a direction to test, not a finding.

### Deeper data: top-5 soccer leagues

One consensus GOAT per league. KPI = league titles in that league only. The full dataset (all rows, with formulas) is in the companion spreadsheet `goat_dataset.xlsx`.

| League | GOAT player | Titles | Best other | GOAT team (best run within L) | L | Team titles | Index |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Premier League | Henry\* | 2 | 13 (Giggs) | Man Utd 1992/93–1999/2000† | 8 | 6 | 3.0 |
| La Liga | Messi | 10 | 12 (Gento) | Real Madrid 1953/54–1969/70† ‡½ | 17 | 12 | 1.2 |
| Serie A | Maldini\* | 7 | 10 (Buffon) | Juventus 1995/96–2019/20† | 25 | 13 | 1.9 |
| Bundesliga | Gerd Müller | 4 | 13 (T. Müller, Neuer) | Bayern 2012/13–2025/26 | 14 | 13 | 3.3 |
| Ligue 1 | Mbappé\* | 7 | 11 (Marquinhos) | PSG 2017/18–2025/26 ‡ | 9 | 8 | 1.1 |

\*Contested consensus pick.

**Updated split test.** With the clean league rows added (Premier League, Serie A, Bundesliga) there are 11 clean club rows. Cycling is left out, because it has no club league. The open European system vs capped North American league model now beats "one mean for all": index ×2.2 higher in open systems, LR test p = 0.02, AIC 22.9 → 19.9. This depends on coding: if cycling counts as an open system, p rises to 0.11. The soccer league rows are also not independent of each other. So the league-system axis is now the leading candidate, but not yet a finding.

## Takeaway

GOATs separate on individual output, not on team wins. The next iteration: divide titles by the number of teams in the competition each season.

*Caveat: league sizes use today's teams and roster limits, not the size in each GOAT's era. Some title counts are from incomplete lists. Treat this as a method demo, not a ranking.*
