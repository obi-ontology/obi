-- Create a view with search labels as LABEL - SYNONYM [TERM ID]
DROP VIEW IF EXISTS obi_search_view;
CREATE VIEW obi_search_view AS
WITH term_ids AS (
    SELECT * FROM (
        SELECT DISTINCT subject AS subject FROM obi
        UNION
        SELECT DISTINCT predicate FROM obi
    )
),
labels AS (
    SELECT DISTINCT subject, object
    FROM obi WHERE predicate = 'rdfs:label'
),
synonyms AS (
    SELECT * FROM (
        SELECT DISTINCT subject, object FROM obi
        WHERE predicate = 'IAO:0000118'
        UNION
        -- IEDB alternative term
        SELECT DISTINCT subject, object FROM obi
        WHERE predicate = 'OBI:9991118'
        UNION
        -- ISA alternative term
        SELECT DISTINCT subject, object FROM obi
        WHERE predicate = 'OBI:0001847'
        UNION
        -- NIAID GSCID-BRC alternative term
        SELECT DISTINCT subject, object FROM obi
        WHERE predicate = 'OBI:0001886'
    )
)
SELECT
    t.subject AS subject,
    COALESCE(l.object, "") || COALESCE(" - " || s.object, "") || " [" || t.subject || "]" AS label
FROM term_ids t
LEFT JOIN labels l ON t.subject = l.subject
LEFT JOIN synonyms s ON t.subject = s.subject;
