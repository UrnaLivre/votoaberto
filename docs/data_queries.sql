-- Open election.sqlite. Codes are textual identifiers from TSE, not IBGE.
-- National totals include only coverage actually present (see manifest).
SELECT e.year,e.round,c.number,c.name,c.kind,SUM(a.votes) AS votes
FROM aggregates a JOIN elections e ON e.id=a.election
JOIN candidates c ON c.id=a.candidate_id
GROUP BY e.id,c.id ORDER BY e.round,c.number;

-- UF and two-round comparison; absent candidacies are not zero.
SELECT e.round,s.uf,c.number,SUM(r.votes) AS votes
FROM results r JOIN sections s ON s.id=r.section_id
JOIN elections e ON e.id=s.election JOIN candidates c ON c.id=r.candidate_id
WHERE s.uf='SC' GROUP BY e.id,s.uf,c.id ORDER BY c.number,e.round;

-- Municipality / zone / section; adjust the codes to the desired location.
SELECT e.round,s.uf,s.municipality,s.zone,s.section,c.number,r.votes,
       r.source_id,r.source_line,t.comparison
FROM results r JOIN sections s ON s.id=r.section_id
JOIN elections e ON e.id=s.election JOIN candidates c ON c.id=r.candidate_id
JOIN section_totals t ON t.section_id=s.id
WHERE s.uf='SC' AND s.municipality='80020' AND s.zone='65' AND s.section='110'
ORDER BY e.round,c.number;

-- Municipality or zone aggregation: drop the unwanted filter.
SELECT e.round,s.municipality,s.zone,c.number,SUM(r.votes) AS votes
FROM results r JOIN sections s ON s.id=r.section_id
JOIN elections e ON e.id=s.election JOIN candidates c ON c.id=r.candidate_id
WHERE s.uf='SC' AND s.municipality='80020' AND s.zone='65'
GROUP BY e.id,s.municipality,s.zone,c.id;

-- SUM skips NULL; availability must accompany totals.
SELECT e.round,SUM(t.eligible) AS eligible_available,SUM(t.turnout) AS turnout_available,
       SUM(t.eligible IS NULL) AS missing_eligible_sections,COUNT(*) AS sections
FROM section_totals t JOIN sections s ON s.id=t.section_id
JOIN elections e ON e.id=s.election GROUP BY e.id;
