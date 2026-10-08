# GOAT statistical audit

3 October 2026

There are formal statistical signals in the supplied numbers, but no established cross-sport explanation of greatness. The strongest relevant candidate is an association between competition system and the dynasty-to-player title ratio. It is worth investigating. It is sensitive to the sample, inferential method, and multiple testing. The strongest within-team contrast is the Patriots' championship era. That contrast does not identify a separate Brady effect. An eigenvalue analysis also detects co-movement among title counts; it supplies no evidence about an unmeasured talent or teamwork factor.

## What was actually available

I read all three supplied files: the Markdown note, both sheets of the workbook, and the standalone LaTeX source. The workbook has **24 mixed records**, comprising nine men's sport rows, four women's sport rows, five soccer league rows, and six national-team rows. Seventeen have numerical rival-title counts, 22 have dynasty-title counts, and 13 have a league-player-count estimate. These are different kinds of records and are not 24 independent sport experiments.

The LaTeX report describes **2,875 athlete-period records**, with **1,554 eligible rows** in its output analyses. Its underlying CSVs, analysis scripts, manifests, source caches, and results files were not included. I could independently reproduce its aggregate ratio comparison and audit its reported regression probabilities from its plotted confidence intervals. I could not rerun the player-level regressions, inspect their residuals, verify encounter unions, or investigate their secondary outcomes.

All 48 workbook margin/index formula cells, including legitimate blank results, agree with independent calculations from the underlying input cells. This verifies arithmetic, not the truth of the input counts. Some inputs are expressly marked as memory-based, approximate, contested, or incomplete. The next-ten title distributions needed to recalculate the reported z scores are also absent.

## Results that answer the proposed relationships

| Proposed relationship | Reanalysis | Assessment |
|---|---|---|
| GOAT team-title margin versus inverse league-player count | Original eight rows: Spearman rho = -0.286; exact permutation p = 0.501 | No detected association. No evidence for the proposed positive inverse-pool pattern. |
| Title z score versus inverse league-player count | Seven rounded z values: rho = -0.321; exact p = 0.498 | No detected association; the underlying comparator distributions cannot be audited. |
| Dynasty/player title ratio versus inverse league-player count | Original eight rows: rho = +0.286; exact p = 0.501 | No detected association. |
| Individual-record margin versus inverse league-player count | Four examples: rho = -0.400; exact p = 0.750 | Too few selected, incompatible KPI examples to establish a general pattern. |
| European system versus capped North American system | Selected 11 club rows: geometric ratio = 2.184 | Strongest cross-sport candidate; model and sample sensitivity described below. |
| Women's versus men's dynasty/player ratio | Same 11 rows: multiplier = 1.467, t-test p = 0.373 | No established sex effect. Only three women's rows are available. |
| Sex after adjustment for system | Multiplier = 1.571, p = 0.202 | Still inconclusive. |
| Career duration versus dynasty/player ratio | Same 11 rows: single-axis p approximately 1.000 | No association detected in this selected sample. |
| Number of players on the field | Note reports p = 0.76 | No supplied field-count column; cannot independently reproduce that model. |
| Encounter threshold versus output gap | Four primary reported models: all Holm-adjusted p > 0.05 | No corrected primary finding. Raw records are absent. |
| Count ratios mutually independent after talent adjustment | No fitted talent variables supplied; exact count identity also applies | The proposed conditional claim was not tested. |
| Talent superiority or teamwork explains GOAT recognition | No full skill vectors, validated coordination inputs, or independent recognition outcomes | Not estimable from these files. |

Exact probabilities above enumerate all assignments for the small correlations. They replace large-sample Spearman approximations. They remain conditional diagnostics on selected rows, rather than establishing that the rows are representative and exchangeable sport samples. [SciPy's Spearman documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html) recommends permutation testing for small samples.

Dropping volleyball's bounded rival count leaves the original margin result nonsignificant: rho = -0.286, exact p = 0.556. The workbook uses more precise league sizes than the rounded Markdown table; this does not change their ranks. The title-gap direction therefore does not depend on those rounding choices.

The z values are descriptive standardised differences relative to selected title holders. Brady's 9.2 sigma value is **not** a Gaussian-tail significance test. Career championships are discrete, dependent, era-sensitive counts, and the comparison players were selected by their high title totals.

## The competition-system candidate

To reproduce the updated note, I used rows 5–9, 11–13, 15, 17, and 18 of `Data`: NBA, men's handball, NHL, men's water polo, men's volleyball, WNBA, women's football, women's handball, Premier League, Serie A, and Bundesliga. Cycling, NFL, aggregate men's football, La Liga, and Ligue 1 are excluded. The exclusions remove trade-team cycling and the stated overlap rows. They also leave just **three capped-system observations**, NBA, NHL, and WNBA, versus eight European observations. Basketball contributes two of the three capped rows.

The geometric mean dynasty/player ratio is **4.123 in the European group** and **1.887 in the capped group**, a multiplier of **2.184**. The ordinary log-linear model's nominal 95% multiplier interval is **1.012–4.717**, assuming independent, normal, common-variance log errors.

| Test or specification | Result |
|---|---:|
| Asymptotic likelihood-ratio test used in the note | p = 0.0243 |
| Finite-sample common-variance t test | p = 0.0473 |
| Exact permutation of the difference in mean log ratios, absolute statistic | p = 0.0545 |
| Exact permutation of the rank-based group contrast, including ties | p = 0.0424 |
| HC3 covariance with t reference, one-axis model | p = 0.0405 |
| Holm correction of the t tests across system, sex, and career-duration axes | system p = 0.1419 |
| Add cycling to the European group | multiplier = 1.884; t p = 0.156; exact mean-log p = 0.182 |
| Include every available club row, including overlap rows | multiplier = 1.890; t p = 0.138; exact mean-log p = 0.142 |
| Collapse related rows into six sport families using geometric means | multiplier = 2.199; exact mean-log p = 0.0667 |

This is weak-to-moderate exploratory evidence of a system association. The difference between p = 0.047 and p = 0.055 is not a meaningful reversal of scientific evidence. More consequential issues are sample definition, only three capped controls, related soccer rows, comparison opportunities, and the analytical search. The three-axis correction is only a limited local correction; it does not cover every specification ever attempted in the project.

Deleting individual rows preserves a positive multiplier, ranging from **1.836 to 2.637**, but the exact mean-log p value ranges from **0.025 to 0.200**. The WNBA row is particularly influential for significance. The signal's direction is more stable than its significance.

Adding sex gives an ordinary system p of 0.0359, but HC3 raises it to 0.179; its held-out row prediction also becomes worse. The single-system model has leave-one-row-out log RMSE **0.541**, versus **0.630** for the single-mean model and **0.645** for the system-plus-sex model. This is modest internal predictive improvement, not external validation, because related observations can remain in training. Adding career duration gives system p = 0.0619 and duration p = 0.916.

The reported AIC improvement reproduces: **22.949 to 19.877**. The small-sample AICc improvement is only **24.449 to 23.306**. These compare models on the same 11 rows; AIC values from different row selections cannot be compared directly.

The original ten-row analysis, treating cycling as European/open, approximately reproduces its null conclusion: multiplier **1.835**, LR p **0.212**, AIC **26.138 to 26.579**. Small differences from the note's rounded estimates are not material. Coding cycling as capped would give a different result and contradict its trade-team status.

Even a stronger system association would concern **dynasty concentration relative to a selected player's titles**. It would not by itself measure dependence on coordination. Wealth concentration, competition format, era, eligibility, and where the selected GOAT played can all produce the same association. A high ratio can result from a player spending few seasons in the particular competition being counted.

## With/without the selected GOAT

For one championship per season or Olympic tournament, I used two-sided Fisher tests on the supplied win/non-win counts. For Barcelona, I used a conditional Poisson rate comparison, which allows multiple titles per season. This is a diagnostic model; it still assumes independent, constant-rate periods and cannot account for season-level title clustering from aggregate totals alone.

| Team | Supplied counts with / without | Unadjusted p | Holm p across these seven comparisons |
|---|---|---:|---:|
| Patriots | 6/20 versus 0/46 | 0.000427 | 0.00299 |
| USA women's water polo | 3/4 versus 0/3 | 0.143 | 0.714 |
| Cuba women's volleyball | 3/3 versus 0/3 | 0.100 | 0.600 |
| Canada women's ice hockey | 4/5 versus 1/3 | 0.464 | 1.000 |
| Barcelona | 14 titles/17 seasons versus 10/22 | 0.155 | 0.714 |
| Hungary men's water polo | 3/5 versus 3/5 | 1.000 | 1.000 |
| USSR men's ice hockey | 3/4 versus 4/5 | 1.000 | 1.000 |

The Patriots' difference passes this formal season-level test, even after the local correction. The conclusion is a championship-era association. It does not establish that Brady alone caused the change. Belichick overlaps the entire 20-season Brady interval, but his full coaching tenure lasted 24 seasons, including four seasons after Brady. That is confirmed by the [Patriots' official announcement](https://www.patriots.com/news/the-patriots-and-bill-belichick-have-mutually-agreed-to-part-ways). A much smaller comparison retaining those four post-Brady coaching seasons, 6/20 versus 0/4, gives Fisher p **0.539**. It has little power and neither confirms nor refutes a separate Brady effect. Periods also differ in roster, league competition, strategy, and franchise conditions; seasons in dynasties are not independent trials.

An infinite observed rate ratio arises from dividing by zero. It does not imply an infinite population effect or statistical certainty. That is particularly clear in the USA and Cuba Olympic rows, whose unadjusted p values remain 0.143 and 0.100 despite infinite reported ratios.

Barcelona's numerator counts trophies rather than championship-winning seasons. The club confirms [Messi's ten league and four Champions League titles over 17 seasons](https://www.fcbarcelona.com/en/football/first-team/news/3642383/leo-messi-becomes-the-most-decorated-player-in-history). The same season can supply both titles. A tempting Fisher test treating 14 titles as 14 distinct successful seasons would incorrectly produce p = 0.0244. The count-rate diagnostic instead gives **p = 0.1548**, conditional on the supplied, not fully verified, without-period counts. A credible causal comparison needs season-level records, fixed period boundaries, and contextual adjustment.

These results do not support classifying five of seven sports as player-driven from the rate ratios. Likewise, Hungary and USSR p values of 1.000 do not prove equivalence or a system-driven causal mechanism.

## The larger reported encounter analyses

The paper describes complete MLB seasons for 2023 and 2024, EPL 2015/16, WSL 2023/24, and the NHL's opening 100 games of 2023/24. Eligible rows are 293, 286, 305, 145, and 525. The NHL period is substantially shorter than the others.

| Reported primary output model | Eligible rows | Club clusters | Nominal p independently reconstructed | Holm p independently reconstructed |
|---|---:|---:|---:|---:|
| MLB, pooled seasons | 579 | 30 | 0.02164 | 0.08656 |
| EPL | 305 | 20 | 0.91800 | 0.91800 |
| WSL | 145 | 12 | 0.23863 | 0.47727 |
| NHL sample | 525 | 32 | 0.09046 | 0.27139 |

These probabilities reconstruct the stated cluster-t calculations from the report's slope estimates and plotted 95% intervals. They do not independently verify the regression fits. The paper reports MLB sensitivity p = 0.006 at 150 PA and p = 0.145 at 502 PA, versus the primary 300-PA analysis. Selecting the favourable cutoff would not validate the original hypothesis. For NHL, the reported quality sensitivity reverses the slope from +2.236 to -0.948 after excluding flagged games, with p = 0.420. That is material instability.

The older five-famous-athlete regression reports nominal p = 0.139 and permutation p = 0.183. Its inputs were not supplied for reanalysis. Unspecified secondary outcomes mentioned in the paper cannot be audited or promoted to findings.

The encounter inequality admits **43.2–55.6%** of eligible athlete-periods, depending on cohort. It is therefore a broad above-average-output condition in these samples. It has not been tested as a GOAT classifier, because no independent recognition labels were measured. It also changes with the observation period: the same athlete can face far more distinct opponents over a season than over a game without changing underlying ability.

## Why the near-zero ratio correlation is misleading

From the paper's more precise chart coordinates, the five-cohort aggregate comparison reproduces **Pearson r = 0.025313**, nominal p = 0.9678, exact absolute-statistic permutation p = 0.925. Collapsing the two MLB years to one point gives r = -0.0904 and exact p = 0.9167.

Removing the much shorter NHL sample produces **r = 0.9045** for the remaining four rows, with exact absolute-statistic p = 0.0417. This is a post-hoc sensitivity involving repeated MLB samples, not a newly validated finding. It demonstrates how unstable the aggregate near-zero result is. An illustrative independent-row Fisher-transform 95% correlation interval for all five rows is approximately **-0.877 to +0.888**. The actual dependence makes that interval unsuitable as validated population inference; even the optimistic calculation does not establish practical zero.

More fundamentally, the computed ratios satisfy the exact identity

\[
A=\frac{1}{N+1},\qquad B=\frac{N}{KL}
\quad\Longrightarrow\quad
B=\frac{1/A-1}{KL}.
\]

At fixed opposing-club count K and league-team count L, B is a strictly decreasing deterministic function of A. If N varies, their rank correlation is -1. Combining different K, L, and periods can conceal that relationship. Skill adjustment cannot transform these quantities into independently measured dimensions. An independent ratio or recognition outcome would be required to test the substantive claim.

## Eigenvalues, PCA, and broad relationship screening

I log-transformed and standardised primitive measurements rather than inserting several derived ratios that reuse the same counts. The first specification used the 13 complete rows and five columns: GOAT titles, rival titles, dynasty titles, career duration, and current league-player count. It has no women's rows because their league-player estimates are missing.

Its correlation-matrix eigenvalues are **2.522, 1.262, 0.809, 0.348, and 0.060**. The first component explains **50.4%** of variance. Against 20,000 independent column-shuffling simulations, its nominal parallel-analysis p is **0.01175**. Correcting the five component comparisons gives **0.05875**. Dropping the aggregate Messi football row, retaining his La Liga row, reduces first-component variance to **41.0%** and nominal p to **0.283**. The leading dimension mostly tracks the three title-count variables.

A second specification omitted league-player count so it could include both sexes: 16 rows, four primitive columns. Its leading component explains **57.2%** of variance, with nominal parallel-analysis p **0.00290** and four-component Holm p **0.01160**. Omitting the duplicated aggregate Messi row gives nominal p **0.0172**; omitting all five soccer league rows gives nominal p **0.00705**. Thus there is evidence of title-count covariance under this column-shuffling diagnostic. It is not evidence of a new physiological talent or coordination dimension. These variables contain championships and duration; the analysis cannot recover qualities it never measured. Related rows and heterogeneous competition units also limit the permutation interpretation, and correction within an individual PCA does not cover the full exploration across specifications.

For the ten pairs among the five primitive columns in the 13-row panel, I ran 100,000 rank-correlation permutations per pair. None survives Holm correction. The strongest is GOAT versus dynasty titles: rho **0.613**, nominal p approximately **0.029**, adjusted p approximately **0.289**. Monte Carlo uncertainty is small enough to leave that conclusion unchanged.

The apparent correlation between the dynasty/player ratio and the player/rival ratio is especially strong: rho **-0.923**. But both reuse the selected player's title count in opposite positions:

\[
\log(T/H)+\log(H/J)=\log(T/J).
\]

This relationship is materially induced by arithmetic coupling. It cannot independently establish a tradeoff between individual greatness and teamwork. Including both ratios in a PCA would amplify that artificial dimension.

## Definition and source problems that matter

- **Title maxima need a consistent historical scope.** The volleyball row names Zenit's six-title run as the best available 13-season dynasty. CEV's [historical winners list](https://championsleague.test.cev.eu/en/history/) shows CSKA winning in 1982, 1983, 1986, 1987, 1988, 1989, and 1991: seven wins in a ten-season span that fits inside 13 seasons. If predecessor European Cups count, as the Kiraly-era comparison implies, six is not the maximum. Substituting seven as a sensitivity changes the system multiplier to 2.227, while leaving the substantive exploratory assessment unchanged.
- **Handball mixes historical scopes.** The supplied Hypo total includes predecessor cups. The [EHF's 1994–2026 table](https://ehfcl.eurohandball.com/women/2025-26/history/ehf-champions-league-women-all-time-statistics/) lists four Hypo Champions League titles and seven for Györ, all within a 20-season span. Counting only that modern competition implies a seven-title dynasty maximum; counting predecessors can retain Hypo's historical eight. This needs a declared rule. The men's Barcelona row also attaches eight titles to a displayed 1991–2005 run containing seven; a longer allowed window reaching 2011 can contain eight. The [club's history](https://www.fcbarcelona.com/en/handball/history) identifies 2011 as its eighth European title.
- **A global GOAT and a local KPI can mismatch.** A player's whole career is not automatically a career of eligibility for the particular European club competition. The ratio can penalise time spent in another league or another form of the sport. This affects what the measure means before any significance test is run.
- **Maxima and averages are not interchangeable.** A dynasty selected by maximising over all clubs and all historical windows has more selection opportunities than one chosen player's career. A ratio exceeding one is not an unbiased estimate of teamwork's causal importance.
- **Today's player pool is not historical exposure.** The workbook's rough player counts cannot be substituted for contemporaneous populations or measured distinct opponents. League teams, squad players, active players, and directly faced individuals answer different questions.
- **National rows are not comparable club observations.** Rowing aggregates many boat-event golds per Games, whereas a person generally competes in one or a few events. Several other national rows overlap the selected player's own squad, and the without-period definitions are not fully sourced. Their index values cannot be pooled into the club inference.
- **A single output is not a complete skill vector.** Hits, goals, points, or titles leave role, opposition, teammates, opportunity, defence, tactics, and error partly unmeasured. The paper's demonstration teamwork scores of 40, 65, and 75 are explicitly invented illustrations and are not observations.

This was a mathematical/statistical audit with targeted primary-source checks, not a complete recertification of every memory-based trophy count or every GOAT choice.

## What the evidence supports

The chosen GOATs frequently trail title-record holders: six of the original eight do so. That is a descriptive warning against treating team championship counts as a complete measure of individual greatness. It does not prove that the entire difference is caused by teamwork or dynasties.

The competition-system association merits a focused next study of championship concentration. The Patriots' era difference is large, but does not isolate individual causation. PCA provides a common title-count dimension, not a validated greatness score. The pool-size relationship, sex effect, encounter-output relationship after correction, and conditional-independence or recognition claims remain unestablished.

The next useful work is to fix the competition and historical-scope definitions, verify every input against complete season records, and obtain the player-period CSVs referred to in the paper. A championship-concentration study should use complete competition-season panels and contemporaneous sizes. A greatness study additionally needs comparison athletes, independently dated recognition outcomes, measured skill components, and appropriately grouped held-out evaluation. Equivalence requires a prespecified practical margin; large ordinary p values cannot substitute for it.

## Computation and verification

Small-sample correlation and system-label tests use exhaustive permutations where feasible. The reported mean-log permutation uses the absolute difference statistic; the rank version permutes ranks with ties retained. These two-sided conventions are explicitly defined because asymmetric randomisation distributions can yield different two-sided tail conventions. Regression estimates use an intercept and finite-sample t probabilities; HC3 is a sensitivity. Multiple comparisons use Holm within explicitly stated local families, following the [documented Holm procedure](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html). [Fisher tests](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html) use conditional hypergeometric probabilities.

Independent checks reproduce the system t-test p value with SciPy, reproduce the Patriots p value from binomial-coefficient enumeration, reconstruct the PCA correlation matrix from its eigenvalues/eigenvectors to within 1.3e-15, verify the exact count identity numerically, verify the reported four-test Holm adjustment, and verify all 48 workbook formula caches. Original input files were left unchanged.

## Complete supplied workbook synopsis

Values below are recalculated from the supplied counts, not newly certified historical records. The volleyball rival count is a lower bound, so its margin is an upper bound. National rows have no rival comparison in the workbook. Missing inputs remain missing.

| Group | Sport / league | Player | Player titles | Rival titles | Margin | Dynasty titles | Index | Career duration | League-player estimate |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Club - men | NFL | Tom Brady | 7 | 5 | +40.0% | 6 | 0.857 | 23 | 1700 |
| Club - men | Cycling (Grand Tours) | Eddy Merckx | 11 | 10 | +10.0% | 12 | 1.091 | 14 | 184 |
| Club - men | Football (top-5 leagues + UCL) | Lionel Messi | 16 | 18 | -11.1% | 19 | 1.188 | 19 | 2400 |
| Club - men | NBA | Michael Jordan | 6 | 11 | -45.5% | 11 | 1.833 | 15 | 450 |
| Club - men | Handball (EHF CL) | Nikola Karabatic | 3 | 7 | -57.1% | 8 | 2.667 | 23 | 256 |
| Club - men | NHL | Wayne Gretzky | 4 | 11 | -63.6% | 11 | 2.750 | 20 | 736 |
| Club - men | Water polo (LEN CL) | Manuel Estiarte | 2 | 7 | -71.4% | 9 | 4.500 | 24 | 240 |
| Club - men | Volleyball (CEV CL) | Karch Kiraly | 1 | 5 | ≤ -80.0% | 6 | 6.000 | 13 | 280 |
| Club - men | Lacrosse (NLL/MLL) | Gary Gait | 6 | — | — | — | — | — | — |
| Club - women | WNBA | Diana Taurasi | 3 | 5 | -40.0% | 4 | 1.333 | 20 | — |
| Club - women | Football (UWCL) | Marta | 1 | 8 | -87.5% | 8 | 8.000 | 22 | — |
| Club - women | Handball (EHF CL) | Cristina Neagu | 1 | 7 | -85.7% | 8 | 8.000 | 20 | — |
| Club - women | Cycling (Grand Tours) | Annemiek van Vleuten | 6 | 5 | +20.0% | — | — | 16 | — |
| Soccer league | Premier League | Thierry Henry | 2 | 13 | -84.6% | 6 | 3.000 | 8 | 500 |
| Soccer league | La Liga | Lionel Messi | 10 | 12 | -16.7% | 12 | 1.200 | 17 | 500 |
| Soccer league | Serie A | Paolo Maldini | 7 | 10 | -30.0% | 13 | 1.857 | 25 | 500 |
| Soccer league | Bundesliga | Gerd Mueller | 4 | 13 | -69.2% | 13 | 3.250 | 14 | 450 |
| Soccer league | Ligue 1 | Kylian Mbappe | 7 | 11 | -36.4% | 8 | 1.143 | 9 | 450 |
| National (supplementary) | Rowing (all events) | Steve Redgrave | 5 | — | — | 30 | 6.000 | 5 | — |
| National (supplementary) | Ice hockey | Vladislav Tretiak | 3 | — | — | 4 | 1.333 | 4 | — |
| National (supplementary) | Ice hockey | Hayley Wickenheiser | 4 | — | — | 4 | 1.000 | 5 | — |
| National (supplementary) | Water polo | Dezso Gyarmati | 3 | — | — | 3 | 1.000 | 5 | — |
| National (supplementary) | Water polo | Maggie Steffens | 3 | — | — | 3 | 1.000 | 4 | — |
| National (supplementary) | Volleyball | Regla Torres | 3 | — | — | 3 | 1.000 | 3 | — |
