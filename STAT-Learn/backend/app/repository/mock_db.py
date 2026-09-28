from typing import Any

# In-memory store for MVP testing
db: dict[str, Any] = {
    "paths": {},
    "nodes": {},
    "prerequisites": {
        "c_dist": [{"skill_id": "skill_py", "required_proficiency": 0.75}],
        "c_cloud": [{"skill_id": "skill_dist", "required_proficiency": 0.8}],
        "c_react": [{"skill_id": "skill_js", "required_proficiency": 0.6}],
        "c_rn": [{"skill_id": "skill_react", "required_proficiency": 0.6}],
        "c_android": [{"skill_id": "skill_rn", "required_proficiency": 0.5}],
        "c_uiux": [{"skill_id": "skill_rn", "required_proficiency": 0.4}],
        "c_sql": [{"skill_id": "skill_py", "required_proficiency": 0.5}],
    },  # course_id -> list of required skills and thresholds
    "courses": {
        "c_py": {
            "course_id": "c_py",
            "title": "Python Basics",
            "taught_skills": ["skill_py"],
            "career_relevance": 0.9,
            "time_efficiency": 0.8,
            "difficulty_fit": 0.8,
        },
        "c_sql": {
            "course_id": "c_sql",
            "title": "SQL Basics",
            "taught_skills": ["skill_sql"],
            "career_relevance": 0.8,
            "time_efficiency": 0.7,
            "difficulty_fit": 0.9,
        },
        "c_dist": {
            "course_id": "c_dist",
            "title": "Distributed Systems",
            "taught_skills": ["skill_dist"],
            "career_relevance": 0.9,
            "time_efficiency": 0.6,
            "difficulty_fit": 0.7,
        },
        "c_cloud": {
            "course_id": "c_cloud",
            "title": "Cloud Data Eng",
            "taught_skills": ["skill_cloud"],
            "career_relevance": 1.0,
            "time_efficiency": 0.5,
            "difficulty_fit": 0.6,
        },
        "c_stats": {
            "course_id": "c_stats",
            "title": "Statistics",
            "taught_skills": ["skill_stats"],
            "career_relevance": 0.7,
            "time_efficiency": 0.9,
            "difficulty_fit": 0.8,
        },
        "c_js": {
            "course_id": "c_js",
            "title": "JavaScript Fundamentals",
            "taught_skills": ["skill_js"],
            "career_relevance": 0.95,
            "time_efficiency": 0.85,
            "difficulty_fit": 0.9,
        },
        "c_react": {
            "course_id": "c_react",
            "title": "React Essentials",
            "taught_skills": ["skill_react"],
            "career_relevance": 0.95,
            "time_efficiency": 0.75,
            "difficulty_fit": 0.8,
        },
        "c_rn": {
            "course_id": "c_rn",
            "title": "React Native Basics",
            "taught_skills": ["skill_rn"],
            "career_relevance": 1.0,
            "time_efficiency": 0.7,
            "difficulty_fit": 0.75,
        },
        "c_android": {
            "course_id": "c_android",
            "title": "Android App Foundations",
            "taught_skills": ["skill_android"],
            "career_relevance": 1.0,
            "time_efficiency": 0.65,
            "difficulty_fit": 0.7,
        },
        "c_uiux": {
            "course_id": "c_uiux",
            "title": "Mobile UI/UX Patterns",
            "taught_skills": ["skill_uiux"],
            "career_relevance": 0.9,
            "time_efficiency": 0.8,
            "difficulty_fit": 0.85,
        },
    },
    "target_roles": {
        "role_de": {
            "role_id": "role_de",
            "required_skills": {
                "skill_py": 0.8,
                "skill_sql": 0.8,
                "skill_dist": 0.8,
                "skill_cloud": 0.8,
                "skill_stats": 0.7,
            },
        },
        "role_be": {
            "role_id": "role_be",
            "required_skills": {
                "skill_py": 0.8,
                "skill_sql": 0.7,
            },
        },
        "role_ai": {
            "role_id": "role_ai",
            "required_skills": {
                "skill_py": 0.8,
                "skill_stats": 0.7,
            },
        },
        "role_fe": {
            "role_id": "role_fe",
            "required_skills": {
                "skill_js": 0.8,
                "skill_react": 0.8,
                "skill_uiux": 0.6,
            },
        },
        "role_mlops": {
            "role_id": "role_mlops",
            "required_skills": {
                "skill_py": 0.8,
                "skill_cloud": 0.7,
                "skill_dist": 0.6,
            },
        },
        "role_other": {
            "role_id": "role_other",
            "required_skills": {
                "skill_js": 0.7,
                "skill_react": 0.7,
                "skill_rn": 0.7,
                "skill_android": 0.7,
                "skill_uiux": 0.6,
            },
        },
    },
    "accounts": {},
    "learners_by_id": {},
    "learners_by_account": {},
    "goals": {},
    "learning_progress": {},
    "verification_sessions": {},
    "assessments": {},
    "conversations": {},
    "lesson_notes": {},  # f"{learner_id}:{node_id}" -> notes text
    "lesson_meta": {},  # f"{learner_id}:{node_id}" -> {ai_ready: bool, ...}
    "summaries": {},
    "learner_profiles": {"L1": {"target_role": "role_de"}},
    "lessons": {
        "n1": {
            "lesson": "# Introduction to Decorators\nA decorator is a function that takes another function...",
            "concepts": ["High-order functions", "functools.wraps"],
            "exercises": ["Write a @timer decorator"],
            "hints": ["Remember to return the wrapper function."],
        }
    },
    "mistakes": {},  # (learner_id, node_id) -> list of mistake dicts
    "course_skills": {
        "c1": ["skill_py"],
        "c2": ["skill_sql"],
        "c_py": ["skill_py"],
        "c_sql": ["skill_sql"],
        "c_dist": ["skill_dist"],
        "c_cloud": ["skill_cloud"],
        "c_stats": ["skill_stats"],
        "c_js": ["skill_js"],
        "c_react": ["skill_react"],
        "c_rn": ["skill_rn"],
        "c_android": ["skill_android"],
        "c_uiux": ["skill_uiux"],
    },
    "skills": {
        "skill_py": {"name": "Python"},
        "skill_sql": {"name": "SQL"},
        "skill_dist": {"name": "Distributed Systems"},
        "skill_cloud": {"name": "Cloud Data Eng"},
        "skill_stats": {"name": "Statistics"},
        "skill_js": {"name": "JavaScript"},
        "skill_react": {"name": "React"},
        "skill_rn": {"name": "React Native"},
        "skill_android": {"name": "Android"},
        "skill_uiux": {"name": "UI/UX"},
    },
    "projects": {
        "proj_1": {
            "title": "Build a Simple API",
            "description": "Create a FastAPI application with two endpoints.",
            "roles": ["role_be", "role_de", "role_mlops"],
            "requirements": [
                {
                    "requirement_id": "req_fastapi",
                    "description": "Must use FastAPI",
                    "mandatory": True,
                },
                {
                    "requirement_id": "req_health",
                    "description": "Must have /health endpoint",
                    "mandatory": True,
                },
                {
                    "requirement_id": "req_json",
                    "description": "Must return JSON",
                    "mandatory": True,
                },
                {
                    "requirement_id": "req_auth",
                    "description": "Optional: Add basic auth",
                    "mandatory": False,
                },
            ],
            "taught_skills": ["skill_py"],
        },
        "proj_mobile": {
            "title": "Build a Mobile Screen Flow",
            "description": "Create a React Native app with navigation and two polished screens.",
            "roles": ["role_fe", "role_other"],
            "requirements": [
                {
                    "requirement_id": "req_rn",
                    "description": "Must use React Native",
                    "mandatory": True,
                },
                {
                    "requirement_id": "req_nav",
                    "description": "Must include screen navigation",
                    "mandatory": True,
                },
                {
                    "requirement_id": "req_responsive",
                    "description": "Must handle basic responsive layout",
                    "mandatory": True,
                },
                {
                    "requirement_id": "req_a11y",
                    "description": "Optional: Add accessibility labels",
                    "mandatory": False,
                },
            ],
            "taught_skills": ["skill_rn", "skill_uiux"],
        },
    },
    "project_submissions": {},  # submission_id -> submission dict
    "evidence": {},  # (learner_id, skill_id, source_type, source_id) -> evidence dict
    "proficiency": {},  # (learner_id, skill_id) -> proficiency dict
}
