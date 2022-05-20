-- Create a view with search labels as LABEL - SYNONYM [TERM ID]
DROP VIEW IF EXISTS TABLE_NAME_search_view;
CREATE VIEW TABLE_NAME_search_view AS
WITH term_ids AS (
    SELECT * FROM (
        SELECT DISTINCT subject AS subject FROM TABLE_NAME
        UNION
        SELECT DISTINCT predicate FROM TABLE_NAME
    )
),
labels AS (
    SELECT DISTINCT subject, object
    FROM TABLE_NAME WHERE predicate = 'rdfs:label'
),
synonyms AS (
    SELECT * FROM (
        SELECT DISTINCT subject, object FROM TABLE_NAME
        WHERE predicate = 'IAO:0000118'
        UNION
        -- IEDB alternative term
        SELECT DISTINCT subject, object FROM TABLE_NAME
        WHERE predicate = 'OBI:9991118'
        UNION
        -- ISA alternative term
        SELECT DISTINCT subject, object FROM TABLE_NAME
        WHERE predicate = 'OBI:0001847'
        UNION
        -- NIAID GSCID-BRC alternative term
        SELECT DISTINCT subject, object FROM TABLE_NAME
        WHERE predicate = 'OBI:0001886'
    )
)
SELECT
    t.subject AS subject,
    COALESCE(l.object, "") || COALESCE(" - " || s.object, "") || " [" || t.subject || "]" AS label
FROM term_ids t
LEFT JOIN labels l ON t.subject = l.subject
LEFT JOIN synonyms s ON t.subject = s.subject
UNION
SELECT
    t.subject AS subject,
    l.object || " [" || t.subject || "]" AS label
FROM term_ids t
JOIN labels l ON t.subject = l.subject
WHERE t.subject IN (SELECT subject FROM synonyms);
