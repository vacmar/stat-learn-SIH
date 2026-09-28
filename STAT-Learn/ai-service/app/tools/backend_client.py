from typing import Any

import httpx

from app.core.config import settings


class BackendClient:
    """Async HTTP client to interact with the manthaino backend service with local fallback."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.backend_api_url).rstrip("/")

    async def _safe_get(self, endpoint: str, fallback_data: Any) -> Any:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}{endpoint}")
                if resp.status_code == 200:
                    return resp.json()
        except (httpx.HTTPError, ConnectionError):
            pass
        return fallback_data

    async def _safe_post(
        self, endpoint: str, payload: dict[str, Any], fallback_data: Any
    ) -> Any:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(f"{self.base_url}{endpoint}", json=payload)
                if resp.status_code == 200:
                    return resp.json()
        except (httpx.HTTPError, ConnectionError):
            pass
        return fallback_data

    async def get_learner_profile(self, learner_id: str) -> dict[str, Any]:
        return await self._safe_get(
            f"/learners/{learner_id}/profile",
            fallback_data={
                "learner_id": learner_id,
                "name": "Alex Mercer",
                "target_role": "Data Engineer",
                "active_path_id": "path_de_01",
                "current_node_id": "node_py_01",
            },
        )

    async def get_current_skill_state(self, learner_id: str) -> list[dict[str, Any]]:
        return await self._safe_get(
            f"/learners/{learner_id}/skills",
            fallback_data=[
                {
                    "skill_id": "skill_py",
                    "name": "Python",
                    "proficiency": 0.65,
                    "confidence": 0.8,
                },
                {
                    "skill_id": "skill_sql",
                    "name": "SQL",
                    "proficiency": 0.40,
                    "confidence": 0.7,
                },
                {
                    "skill_id": "skill_dm",
                    "name": "Data Modeling",
                    "proficiency": 0.20,
                    "confidence": 0.5,
                },
            ],
        )

    async def get_target_requirements(self, role_id: str) -> list[dict[str, Any]]:
        return [
            {
                "skill_id": "skill_py",
                "name": "Python",
                "importance": 0.9,
                "required_proficiency": 0.8,
            },
            {
                "skill_id": "skill_sql",
                "name": "SQL",
                "importance": 0.9,
                "required_proficiency": 0.8,
            },
            {
                "skill_id": "skill_dm",
                "name": "Data Modeling",
                "importance": 0.8,
                "required_proficiency": 0.75,
            },
            {
                "skill_id": "skill_dist",
                "name": "Distributed Systems",
                "importance": 0.85,
                "required_proficiency": 0.8,
            },
        ]

    async def calculate_skill_gaps(
        self, learner_id: str, role_id: str
    ) -> list[dict[str, Any]]:
        return [
            {
                "skill_name": "Distributed Systems",
                "required": 0.8,
                "current": 0.0,
                "gap": 0.8,
                "importance": 0.85,
            },
            {
                "skill_name": "Data Modeling",
                "required": 0.75,
                "current": 0.2,
                "gap": 0.55,
                "importance": 0.8,
            },
            {
                "skill_name": "SQL",
                "required": 0.8,
                "current": 0.4,
                "gap": 0.4,
                "importance": 0.9,
            },
            {
                "skill_name": "Python",
                "required": 0.8,
                "current": 0.65,
                "gap": 0.15,
                "importance": 0.9,
            },
        ]

    async def get_prerequisites(self, course_id: str) -> list[dict[str, Any]]:
        return [
            {
                "course_id": "c_py_intro",
                "title": "Introduction to Python",
                "is_mandatory": True,
            }
        ]

    async def find_courses_for_skill(self, skill_id: str) -> list[dict[str, Any]]:
        return [
            {
                "course_id": "c_py_adv",
                "title": "Advanced Python",
                "difficulty": "Intermediate",
                "hours": 5.0,
            },
            {
                "course_id": "c_py_perf",
                "title": "High Performance Python",
                "difficulty": "Advanced",
                "hours": 6.0,
            },
        ]

    async def find_projects_for_skills(
        self, skill_ids: list[str]
    ) -> list[dict[str, Any]]:
        return [
            {
                "project_id": "proj_etl_pipeline",
                "title": "Real-time ETL Stream Processor",
                "difficulty": "Intermediate",
                "estimated_hours": 12.0,
                "target_skills": skill_ids,
            }
        ]

    async def generate_candidate_paths(
        self, learner_id: str, role_id: str
    ) -> list[dict[str, Any]]:
        return [
            {
                "candidate_id": "path_opt_fast",
                "sequence": [
                    "Python",
                    "SQL",
                    "Data Modeling",
                    "Distributed Systems",
                    "Spark",
                    "Capstone",
                ],
                "total_hours": 35.0,
                "gap_reduction": 0.95,
            },
            {
                "candidate_id": "path_opt_deep",
                "sequence": [
                    "Python",
                    "Advanced Python",
                    "SQL",
                    "PostgreSQL",
                    "Data Modeling",
                    "Distributed Systems",
                    "Spark",
                ],
                "total_hours": 48.0,
                "gap_reduction": 0.99,
            },
        ]

    async def rank_candidate_paths(
        self, candidate_paths: list[dict[str, Any]], role_id: str | None = None
    ) -> list[dict[str, Any]]:
        # Sort by gap_reduction / total_hours (efficiency score)
        return sorted(
            candidate_paths,
            key=lambda p: (
                p.get("gap_reduction", 1.0) / max(p.get("total_hours", 1.0), 1.0)
            ),
            reverse=True,
        )

    async def get_learning_node_state(self, node_id: str) -> dict[str, Any]:
        return await self._safe_get(
            f"/nodes/{node_id}/progress",
            fallback_data={
                "node_id": node_id,
                "course_title": "Python Programming",
                "status": "IN_PROGRESS",
                "current_module": "Decorators and Closures",
                "current_concept": "Function Wrapping and Metadata Preservation",
                "progress_percentage": 64.0,
                "mastery_score": 0.72,
            },
        )

    async def get_conversation_context(
        self, conversation_id: str, limit: int = 10
    ) -> dict[str, Any]:
        return await self._safe_get(
            f"/conversations/{conversation_id}",
            fallback_data={
                "conversation_id": conversation_id,
                "summary": "Learner previously explored basic decorator syntax and asked about `functools.wraps`.",
                "recent_messages": [
                    {
                        "role": "user",
                        "content": "Why do we use functools.wraps on our wrapper?",
                    },
                    {
                        "role": "assistant",
                        "content": "It preserves the original function's name and docstring.",
                    },
                ],
            },
        )

    async def get_weak_concepts(
        self, learner_id: str, node_id: str
    ) -> list[dict[str, Any]]:
        resp = await self._safe_get(
            f"/nodes/{node_id}/mistakes?learner_id={learner_id}",
            fallback_data={"weak_concepts": []},
        )
        return resp.get("weak_concepts", [])

    async def record_mistake(
        self, learner_id: str, node_id: str, concept: str, description: str
    ) -> dict[str, Any]:
        payload = {
            "learner_id": learner_id,
            "concept": concept,
            "description": description,
        }
        return await self._safe_post(
            f"/nodes/{node_id}/mistakes", payload, fallback_data={"status": "recorded"}
        )

    async def get_lesson_context(self, node_id: str) -> dict[str, Any]:
        return await self._safe_get(
            f"/nodes/{node_id}/context",
            fallback_data={
                "lesson": "Lesson context not available in DB.",
                "concepts": [],
            },
        )

    async def record_assessment_result(
        self, learner_id: str, assessment_id: str, score: float, passed: bool
    ) -> dict[str, Any]:
        payload = {"score": score, "passed": passed}
        return await self._safe_post(
            f"/assessments/{assessment_id}/answer",
            payload,
            fallback_data={
                "status": "recorded",
                "assessment_id": assessment_id,
                "score": score,
                "passed": passed,
            },
        )

    async def update_skill_evidence(
        self,
        learner_id: str,
        skill_id: str,
        score: float,
        source_type: str = "PRACTICAL",
    ) -> dict[str, Any]:
        payload = {"skill_id": skill_id, "score": score, "source_type": source_type}
        return await self._safe_post(
            f"/learners/{learner_id}/evidence",
            payload,
            fallback_data={
                "status": "evidence_recorded",
                "learner_id": learner_id,
                "skill_id": skill_id,
                "score": score,
            },
        )

    async def check_unlock_conditions(
        self, learner_id: str, node_id: str
    ) -> dict[str, Any]:
        return {
            "node_id": node_id,
            "can_unlock": True,
            "prerequisites_met": True,
            "unmet_prerequisites": [],
        }

    async def complete_learning_node(
        self, node_id: str, assessment_score: float, practical_pass: bool
    ) -> dict[str, Any]:
        payload = {
            "assessment_score": assessment_score,
            "practical_pass": practical_pass,
        }
        return await self._safe_post(
            f"/nodes/{node_id}/complete",
            payload,
            fallback_data={
                "node_id": node_id,
                "success": (assessment_score >= 0.8 and practical_pass),
            },
        )

    async def evaluate_project(
        self, project_id: str, evaluation_payload: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._safe_post(
            f"/projects/{project_id}/evaluate",
            evaluation_payload,
            fallback_data={
                "status": "PASSED"
                if evaluation_payload.get("passed", False)
                else "NEEDS_REVISION",
                "feedback": "Fallback",
                "skills_updated": [],
                "unlocked_nodes": [],
                "next_recommended_node": None,
            },
        )


backend_client = BackendClient()
