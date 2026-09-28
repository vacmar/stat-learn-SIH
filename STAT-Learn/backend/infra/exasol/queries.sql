-- queries.sql
-- Core analytical queries for pathway generation in Exasol

-- 1. Skill Gap Analysis
-- Compares a learner's current skills against the required skills for their goal role.
-- Variables: :learner_id, :role_id
SELECT 
    rs.skill_id,
    s.name AS skill_name,
    rs.importance,
    rs.required_proficiency,
    COALESCE(ls.proficiency, 0.0) AS current_proficiency,
    GREATEST(0.0, rs.required_proficiency - COALESCE(ls.proficiency, 0.0)) AS gap
FROM 
    role_skills rs
JOIN 
    skills s ON rs.skill_id = s.skill_id
LEFT JOIN 
    learner_skills ls ON rs.skill_id = ls.skill_id AND ls.learner_id = :learner_id
WHERE 
    rs.role_id = :role_id
    AND GREATEST(0.0, rs.required_proficiency - COALESCE(ls.proficiency, 0.0)) > 0
ORDER BY 
    gap DESC, rs.importance DESC;


-- 2. Prerequisite Coverage Analysis
-- Checks which courses are eligible to be taken by verifying that all mandatory prerequisites
-- are satisfied (i.e., the prerequisite courses have been completed by the learner).
-- Note: Assuming completion means proficiency > 0.6 for the skills taught, or we can check path_nodes.
-- Here we check based on course completions in path_nodes for simplicity.
SELECT 
    c.course_id,
    c.title,
    COUNT(cp.prerequisite_course_id) AS total_mandatory_prereqs,
    SUM(CASE WHEN pn.status = 'COMPLETED' THEN 1 ELSE 0 END) AS satisfied_prereqs
FROM 
    courses c
LEFT JOIN 
    course_prerequisites cp ON c.course_id = cp.course_id AND cp.is_mandatory = TRUE
LEFT JOIN 
    path_nodes pn ON cp.prerequisite_course_id = pn.course_id 
                  AND pn.path_id IN (SELECT path_id FROM path_instances WHERE learner_id = :learner_id)
GROUP BY 
    c.course_id, c.title
HAVING 
    COUNT(cp.prerequisite_course_id) = SUM(CASE WHEN pn.status = 'COMPLETED' THEN 1 ELSE 0 END)
    OR COUNT(cp.prerequisite_course_id) = 0;


-- 3. Candidate Path Ranking
-- Scores eligible courses based on how much they reduce the skill gap, factoring in importance.
-- This uses a CTE to first compute gaps, then joins with eligible courses to rank them.
WITH SkillGaps AS (
    SELECT 
        rs.skill_id,
        GREATEST(0.0, rs.required_proficiency - COALESCE(ls.proficiency, 0.0)) AS gap,
        rs.importance
    FROM 
        role_skills rs
    LEFT JOIN 
        learner_skills ls ON rs.skill_id = ls.skill_id AND ls.learner_id = :learner_id
    WHERE 
        rs.role_id = :role_id
),
EligibleCourses AS (
    SELECT 
        c.course_id
    FROM 
        courses c
    LEFT JOIN 
        course_prerequisites cp ON c.course_id = cp.course_id AND cp.is_mandatory = TRUE
    LEFT JOIN 
        path_nodes pn ON cp.prerequisite_course_id = pn.course_id 
                      AND pn.path_id IN (SELECT path_id FROM path_instances WHERE learner_id = :learner_id)
    GROUP BY 
        c.course_id
    HAVING 
        COUNT(cp.prerequisite_course_id) = SUM(CASE WHEN pn.status = 'COMPLETED' THEN 1 ELSE 0 END)
        OR COUNT(cp.prerequisite_course_id) = 0
)
SELECT 
    c.course_id,
    c.title,
    -- Ranking score logic: SUM(gap * importance * contribution_weight)
    SUM(sg.gap * sg.importance * cs.contribution_weight) AS gap_reduction_score,
    c.estimated_hours,
    (SUM(sg.gap * sg.importance * cs.contribution_weight) / NULLIF(c.estimated_hours, 0)) AS efficiency_score
FROM 
    EligibleCourses ec
JOIN 
    courses c ON ec.course_id = c.course_id
JOIN 
    course_skills cs ON c.course_id = cs.course_id
JOIN 
    SkillGaps sg ON cs.skill_id = sg.skill_id
WHERE 
    sg.gap > 0
GROUP BY 
    c.course_id, c.title, c.estimated_hours
ORDER BY 
    efficiency_score DESC, gap_reduction_score DESC;


-- 4. Course Coverage Analysis
-- For a target role, shows how well each required skill is covered by catalogue courses.
-- Variables: :role_id
SELECT
    rs.skill_id,
    s.name AS skill_name,
    rs.required_proficiency,
    COUNT(DISTINCT cs.course_id) AS covering_courses,
    COALESCE(SUM(cs.contribution_weight), 0.0) AS total_contribution_weight,
    CASE
        WHEN COALESCE(SUM(cs.contribution_weight), 0.0) >= rs.required_proficiency THEN 'COVERED'
        WHEN COALESCE(SUM(cs.contribution_weight), 0.0) > 0 THEN 'PARTIAL'
        ELSE 'UNCOVERED'
    END AS coverage_status
FROM
    role_skills rs
JOIN
    skills s ON rs.skill_id = s.skill_id
LEFT JOIN
    course_skills cs ON cs.skill_id = rs.skill_id
WHERE
    rs.role_id = :role_id
GROUP BY
    rs.skill_id, s.name, rs.required_proficiency
ORDER BY
    coverage_status DESC, rs.required_proficiency DESC;
