-- schema.sql
-- Exasol Data Foundation Schema for manthaino

-- Base Entities

CREATE TABLE learners (
    learner_id VARCHAR(36) PRIMARY KEY,
    account_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    target_role_id VARCHAR(50),
    target_domain VARCHAR(100),
    experience_level VARCHAR(50),
    prior_experience VARCHAR(50),
    education VARCHAR(100),
    learning_style VARCHAR(50),
    weekly_time INT,
    onboarding_completed BOOLEAN,
    onboarding_version INT,
    onboarding_completed_at VARCHAR(50),
    goals VARCHAR(2000),
    known_skills VARCHAR(2000),
    interests VARCHAR(2000),
    self_reported_proficiency VARCHAR(4000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    created_at VARCHAR(50),
    updated_at VARCHAR(50),
    is_active BOOLEAN
);

CREATE TABLE goals (
    goal_id VARCHAR(36) PRIMARY KEY,
    learner_id VARCHAR(36) NOT NULL REFERENCES learners(learner_id),
    target_role_id VARCHAR(36) NOT NULL,
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, COMPLETED, ABANDONED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE career_roles (
    role_id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(2000),
    role_level VARCHAR(50) -- e.g., Junior, Mid, Senior (LEVEL is reserved in Exasol)
);

CREATE TABLE skills (
    skill_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description VARCHAR(2000)
);

CREATE TABLE courses (
    course_id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(2000),
    difficulty VARCHAR(50),
    estimated_hours DECIMAL(5,2)
);

CREATE TABLE projects (
    project_id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(2000),
    difficulty VARCHAR(50),
    estimated_hours DECIMAL(5,2)
);

-- Mappings

CREATE TABLE role_skills (
    role_id VARCHAR(36) NOT NULL REFERENCES career_roles(role_id),
    skill_id VARCHAR(36) NOT NULL REFERENCES skills(skill_id),
    importance DECIMAL(3,2), -- e.g., 0.0 to 1.0
    required_proficiency DECIMAL(3,2), -- e.g., 0.0 to 1.0 (0.75 for Advanced)
    PRIMARY KEY (role_id, skill_id)
);

CREATE TABLE course_skills (
    course_id VARCHAR(36) NOT NULL REFERENCES courses(course_id),
    skill_id VARCHAR(36) NOT NULL REFERENCES skills(skill_id),
    contribution_weight DECIMAL(3,2), -- e.g., 0.0 to 1.0
    PRIMARY KEY (course_id, skill_id)
);

CREATE TABLE course_prerequisites (
    course_id VARCHAR(36) NOT NULL REFERENCES courses(course_id),
    prerequisite_course_id VARCHAR(36) NOT NULL REFERENCES courses(course_id),
    is_mandatory BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (course_id, prerequisite_course_id)
);

CREATE TABLE project_skills (
    project_id VARCHAR(36) NOT NULL REFERENCES projects(project_id),
    skill_id VARCHAR(36) NOT NULL REFERENCES skills(skill_id),
    PRIMARY KEY (project_id, skill_id)
);

-- Learner State and Progress

CREATE TABLE learner_skills (
    learner_id VARCHAR(36) NOT NULL REFERENCES learners(learner_id),
    skill_id VARCHAR(36) NOT NULL REFERENCES skills(skill_id),
    proficiency DECIMAL(3,2) DEFAULT 0.0,
    confidence DECIMAL(3,2) DEFAULT 0.0,
    last_assessed_at TIMESTAMP,
    PRIMARY KEY (learner_id, skill_id)
);

CREATE TABLE evidence (
    evidence_id VARCHAR(36) PRIMARY KEY,
    learner_id VARCHAR(36) NOT NULL REFERENCES learners(learner_id),
    skill_id VARCHAR(36) NOT NULL REFERENCES skills(skill_id),
    source_type VARCHAR(50) NOT NULL, -- e.g., 'ASSESSMENT', 'PRACTICAL', 'SELF_CLAIM'
    score DECIMAL(3,2),
    weight DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE path_instances (
    path_id VARCHAR(36) PRIMARY KEY,
    learner_id VARCHAR(36) NOT NULL REFERENCES learners(learner_id),
    goal_id VARCHAR(36) NOT NULL REFERENCES goals(goal_id),
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, OBSOLETE, COMPLETED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE path_nodes (
    node_id VARCHAR(36) PRIMARY KEY,
    path_id VARCHAR(36) NOT NULL REFERENCES path_instances(path_id),
    course_id VARCHAR(36) NOT NULL REFERENCES courses(course_id),
    sequence_order INT NOT NULL,
    status VARCHAR(50) DEFAULT 'LOCKED', -- LOCKED, UNLOCKED, IN_PROGRESS, COMPLETED
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE learning_progress (
    progress_id VARCHAR(36) PRIMARY KEY,
    node_id VARCHAR(36) NOT NULL REFERENCES path_nodes(node_id),
    current_module VARCHAR(255),
    current_concept VARCHAR(255),
    progress_percentage DECIMAL(5,2) DEFAULT 0.0,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assessments and Projects

CREATE TABLE assessments (
    assessment_id VARCHAR(36) PRIMARY KEY,
    course_id VARCHAR(36) REFERENCES courses(course_id),
    title VARCHAR(255),
    type VARCHAR(50) -- e.g., 'QUIZ', 'PRACTICAL', 'FINAL'
);

CREATE TABLE assessment_results (
    result_id VARCHAR(36) PRIMARY KEY,
    assessment_id VARCHAR(36) NOT NULL REFERENCES assessments(assessment_id),
    learner_id VARCHAR(36) NOT NULL REFERENCES learners(learner_id),
    score DECIMAL(5,2),
    passed BOOLEAN,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exercise_results (
    exercise_id VARCHAR(36) PRIMARY KEY,
    node_id VARCHAR(36) NOT NULL REFERENCES path_nodes(node_id),
    learner_id VARCHAR(36) NOT NULL REFERENCES learners(learner_id),
    passed BOOLEAN,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE project_evaluations (
    evaluation_id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL REFERENCES projects(project_id),
    learner_id VARCHAR(36) NOT NULL REFERENCES learners(learner_id),
    score DECIMAL(5,2),
    passed BOOLEAN,
    feedback VARCHAR(2000),
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations

CREATE TABLE conversations (
    conversation_id VARCHAR(36) PRIMARY KEY,
    learner_id VARCHAR(36) NOT NULL REFERENCES learners(learner_id),
    node_id VARCHAR(36) NOT NULL REFERENCES path_nodes(node_id),
    title VARCHAR(255),
    summary VARCHAR(2000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    message_id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(conversation_id),
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system', 'tool'
    content VARCHAR(10000),
    metadata VARCHAR(4000), -- JSON payload for tools or context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Focus lesson workspace (rich HTML notes + chat JSON). No FK to path_nodes
-- because AI-generated node IDs may not exist in Exasol path_nodes yet.
CREATE TABLE lesson_sessions (
    session_key VARCHAR(200) PRIMARY KEY,
    learner_id VARCHAR(50),
    node_id VARCHAR(100),
    practice_notes VARCHAR(2000000),
    messages_json VARCHAR(2000000),
    ai_ready BOOLEAN,
    ready_reason VARCHAR(1000),
    updated_at VARCHAR(50)
);
