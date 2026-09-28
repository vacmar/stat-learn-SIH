import uuid
from datetime import UTC, datetime
from typing import Any

from app.models.domain import LearningPath, NodeStatus, PathNode
from app.repository import state_repo


def _get_target_role_requirements(learner_id: str) -> dict[str, float]:
    profile = state_repo.db.get("learner_profiles", {}).get(learner_id)
    if not profile:
        return {}
    role = state_repo.db.get("target_roles", {}).get(profile["target_role"])
    return role.get("required_skills", {}) if role else {}


def _get_available_course_for_skill(skill_id: str) -> dict[str, Any] | None:
    # In MVP, assume 1 course maps to 1 skill primarily for replanning simplicity
    for course_id, course in state_repo.db.get("courses", {}).items():
        if skill_id in course.get("taught_skills", []):
            return course
    return None


def _resolve_prerequisites_recursively(
    learner_id: str,
    required_courses: set,
    resolved_courses: set,
    proficiencies: dict[str, float],
):
    """
    Recursively pulls in prerequisite courses if their skills aren't mastered.
    """
    added_new = True
    while added_new:
        added_new = False
        current_reqs = list(required_courses)
        for course_id in current_reqs:
            prereqs = state_repo.get_prerequisites(course_id)
            for prereq in prereqs:
                req_skill = prereq["skill_id"]
                req_thresh = prereq["required_proficiency"]

                if proficiencies.get(req_skill, 0.0) < req_thresh:
                    prereq_course = _get_available_course_for_skill(req_skill)
                    if (
                        prereq_course
                        and prereq_course["course_id"] not in required_courses
                    ):
                        required_courses.add(prereq_course["course_id"])
                        added_new = True


def _rank_courses(
    courses: list[dict[str, Any]],
    proficiencies: dict[str, float],
    target_reqs: dict[str, float],
) -> list[str]:
    """
    Ranks courses using the Phase 8 ranking logic.
    For dependencies, a simple topological sort or relying on 'prerequisite validity'
    can be used. Since the prompt asks to use Phase 8 weights:
    0.35 gap reduction, 0.25 career relevance, 0.15 prereq validity, 0.15 time eff, 0.10 diff fit
    """
    scored = []
    for course in courses:
        course_id = course["course_id"]

        # 1. Gap reduction (max gap of taught skills)
        max_gap = 0.0
        for skill in course.get("taught_skills", []):
            target = target_reqs.get(skill, 0.0)
            current = proficiencies.get(skill, 0.0)
            gap = max(0.0, target - current)
            max_gap = max(max_gap, gap)

        score = 0.35 * max_gap
        score += 0.25 * course.get("career_relevance", 0.5)

        # Prerequisite validity (are its prereqs met among already mastered skills?)
        # For simplicity, if prereqs are met, validity is 1.0, else 0.0
        prereqs = state_repo.get_prerequisites(course_id)
        prereqs_met = all(
            proficiencies.get(p["skill_id"], 0.0) >= p["required_proficiency"]
            for p in prereqs
        )
        score += 0.15 * (1.0 if prereqs_met else 0.0)

        score += 0.15 * course.get("time_efficiency", 0.5)
        score += 0.10 * course.get("difficulty_fit", 0.5)

        scored.append((course_id, score))

    # Sort descending by score. To ensure prerequisites come first if tied or close,
    # we do a stable dependency-aware sort.
    scored.sort(key=lambda x: x[1], reverse=True)

    # Topological sort enforcement: prereqs must appear before dependents.
    # We iteratively pull courses whose prereqs are either met by proficiencies OR already in the sorted_result.
    final_sequence = []
    remaining = [c[0] for c in scored]

    # Track skills we conceptually 'gain' as we go through the sequence
    simulated_prof = proficiencies.copy()

    while remaining:
        moved_any = False
        for cid in list(remaining):
            prereqs = state_repo.get_prerequisites(cid)
            can_take = all(
                simulated_prof.get(p["skill_id"], 0.0) >= p["required_proficiency"]
                for p in prereqs
            )

            if can_take:
                final_sequence.append(cid)
                remaining.remove(cid)
                course = state_repo.db["courses"][cid]
                for skill in course.get("taught_skills", []):
                    # Simulate mastering the skill to 1.0
                    simulated_prof[skill] = 1.0
                moved_any = True
                break

        if not moved_any:
            # Cycle or unresolved prereq. Just append the first remaining one to break the deadlock.
            final_sequence.append(remaining.pop(0))

    return final_sequence


def _sync_learner_profile(learner_id: str, target_role_id: str | None):
    if not target_role_id:
        return
    profiles = state_repo.db.setdefault("learner_profiles", {})
    existing = profiles.get(learner_id) or {}
    existing["target_role"] = target_role_id
    profiles[learner_id] = existing


def _slugify(text: str) -> str:
    raw = "".join(c.lower() if c.isalnum() else "_" for c in text.strip())
    while "__" in raw:
        raw = raw.replace("__", "_")
    return raw.strip("_")[:48] or "stage"


def _materialize_ai_courses(stages: list[dict[str, Any]]) -> list[str]:
    """Register AI-authored courses in mock_db and return ordered course_ids."""
    courses = state_repo.db.setdefault("courses", {})
    skills = state_repo.db.setdefault("skills", {})
    course_skills = state_repo.db.setdefault("course_skills", {})
    sequence: list[str] = []

    for i, stage in enumerate(stages):
        title = str(stage.get("course_name") or f"Stage {i + 1}").strip()
        course_id = f"ai_{_slugify(title)}"
        # Avoid collisions across regenerations
        if course_id in courses and courses[course_id].get("title") != title:
            course_id = f"{course_id}_{i + 1}"

        target_skills = [str(s) for s in (stage.get("target_skills") or []) if s]
        skill_ids: list[str] = []
        for skill_name in target_skills:
            sid = f"skill_{_slugify(skill_name)}"
            skills[sid] = {"name": skill_name}
            skill_ids.append(sid)
        if not skill_ids:
            sid = f"skill_{_slugify(title)}"
            skills[sid] = {"name": title}
            skill_ids = [sid]

        courses[course_id] = {
            "course_id": course_id,
            "title": title,
            "taught_skills": skill_ids,
            "rationale": stage.get("rationale") or "",
            "career_relevance": 0.95,
            "time_efficiency": 0.8,
            "difficulty_fit": 0.8,
            "ai_authored": True,
        }
        course_skills[course_id] = skill_ids
        sequence.append(course_id)

    return sequence


def _store_ai_capstone(learner_id: str, capstone: dict[str, Any] | None) -> str | None:
    if not capstone or not capstone.get("title"):
        return None
    project_id = f"proj_ai_{learner_id[:12]}"
    requirements = []
    for i, req in enumerate(capstone.get("requirements") or []):
        if isinstance(req, dict):
            requirements.append(
                {
                    "requirement_id": req.get("requirement_id") or f"req_{i + 1}",
                    "description": req.get("description") or "Requirement",
                    "mandatory": bool(req.get("mandatory", True)),
                }
            )
        else:
            requirements.append(
                {
                    "requirement_id": f"req_{i + 1}",
                    "description": str(req),
                    "mandatory": True,
                }
            )
    project = {
        "title": capstone["title"],
        "description": capstone.get("description") or "",
        "roles": [],
        "requirements": requirements,
        "taught_skills": [],
        "ai_authored": True,
        "learner_id": learner_id,
    }
    state_repo.db.setdefault("projects", {})[project_id] = project
    profiles = state_repo.db.setdefault("learner_profiles", {})
    profile = profiles.setdefault(learner_id, {})
    profile["recommended_project_id"] = project_id
    profile["pathway_summary"] = profile.get("pathway_summary")
    return project_id


def _generate_path_from_ai_stages(
    learner_id: str,
    stages: list[dict[str, Any]],
    *,
    capstone: dict[str, Any] | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    course_sequence = _materialize_ai_courses(stages)
    if not course_sequence:
        raise ValueError("AI pathway returned no stages")

    path_id = uuid.uuid4().hex
    new_path = LearningPath(
        path_id=path_id,
        learner_id=learner_id,
        version=1,
        previous_path_id=None,
        created_at=datetime.now(UTC).isoformat(),
        is_active=True,
    )
    state_repo.save_path(new_path)

    new_nodes: list[PathNode] = []
    for seq, cid in enumerate(course_sequence, start=1):
        status = NodeStatus.UNLOCKED if seq == 1 else NodeStatus.LOCKED
        node = PathNode(
            node_id=uuid.uuid4().hex,
            path_id=path_id,
            course_id=cid,
            sequence_order=seq,
            status=status,
        )
        new_nodes.append(node)
        state_repo.update_node(node)

    _store_ai_capstone(learner_id, capstone)
    if summary:
        profiles = state_repo.db.setdefault("learner_profiles", {})
        profiles.setdefault(learner_id, {})["pathway_summary"] = summary

    from app.services import unlock_service

    unlock_service.check_unlocks(learner_id, path_id)
    state_repo.persist_active_path(learner_id)

    return {
        "path_id": path_id,
        "version": 1,
        "nodes": [n.model_dump() for n in new_nodes],
        "created": True,
        "source": "ai",
    }


def _generate_path_rules_fallback(learner_id: str, role_id: str) -> dict[str, Any]:
    """Legacy catalog ranking — only used if AI service is unreachable."""
    _sync_learner_profile(learner_id, role_id)

    proficiencies: dict[str, float] = {}
    for skill_id in state_repo.db.get("skills", {}).keys():
        prof = state_repo.get_learner_proficiency(learner_id, skill_id)
        proficiencies[skill_id] = prof["proficiency"]

    target_reqs = _get_target_role_requirements(learner_id)
    required_courses: set[str] = set()
    for skill, target in target_reqs.items():
        if proficiencies.get(skill, 0.0) < target:
            course = _get_available_course_for_skill(skill)
            if course:
                required_courses.add(course["course_id"])

    _resolve_prerequisites_recursively(
        learner_id, required_courses, set(), proficiencies
    )

    course_objects = [
        state_repo.db["courses"][cid]
        for cid in required_courses
        if cid in state_repo.db["courses"]
    ]
    course_sequence = _rank_courses(course_objects, proficiencies, target_reqs)

    for first in ("c_js", "c_py"):
        if first in course_sequence:
            course_sequence = [first] + [c for c in course_sequence if c != first]
            break

    path_id = uuid.uuid4().hex
    new_path = LearningPath(
        path_id=path_id,
        learner_id=learner_id,
        version=1,
        previous_path_id=None,
        created_at=datetime.now(UTC).isoformat(),
        is_active=True,
    )
    state_repo.save_path(new_path)

    new_nodes: list[PathNode] = []
    for seq, cid in enumerate(course_sequence, start=1):
        status = NodeStatus.UNLOCKED if seq == 1 else NodeStatus.LOCKED
        node = PathNode(
            node_id=uuid.uuid4().hex,
            path_id=path_id,
            course_id=cid,
            sequence_order=seq,
            status=status,
        )
        new_nodes.append(node)
        state_repo.update_node(node)

    from app.services import unlock_service

    unlock_service.check_unlocks(learner_id, path_id)

    return {
        "path_id": path_id,
        "version": 1,
        "nodes": [n.model_dump() for n in new_nodes],
        "created": True,
        "source": "rules_fallback",
    }


def generate_path_for_learner(
    learner_id: str, target_role_id: str | None = None
) -> dict[str, Any]:
    """Create the first active learning path for a learner via the AI service."""
    existing = state_repo.get_active_path(learner_id)
    if existing:
        nodes = state_repo.get_nodes_for_path(existing.path_id)
        return {
            "path_id": existing.path_id,
            "version": existing.version,
            "nodes": [n.model_dump() for n in nodes],
            "created": False,
        }

    role_id = target_role_id
    learner = state_repo.get_learner(learner_id)
    if not role_id:
        role_id = learner.target_role_id if learner else None
    if not role_id:
        role_id = "role_de"

    _sync_learner_profile(learner_id, role_id)
    profile = state_repo.db.get("learner_profiles", {}).get(learner_id, {})

    if learner:
        from app.services import ai_client

        try:
            payload = ai_client.build_path_generate_payload(
                learner,
                role_title=profile.get("role_title"),
                path_role_id=role_id,
                profile=profile,
            )
            ai_path = ai_client.request_ai_pathway(payload)
            stages = ai_path.get("stages") or []
            if stages:
                return _generate_path_from_ai_stages(
                    learner_id,
                    stages,
                    capstone=ai_path.get("capstone"),
                    summary=ai_path.get("summary"),
                )
        except Exception as e:
            print(f"AI path generation failed, using rules fallback: {e}")

    return _generate_path_rules_fallback(learner_id, role_id)


def regenerate_path(learner_id: str, current_path_id: str) -> dict[str, Any]:
    active_path = state_repo.get_active_path(learner_id)
    if not active_path:
        raise ValueError("No active path found for learner")

    if active_path.path_id != current_path_id:
        raise ValueError("Supplied path_id is not the active path")

    nodes = state_repo.get_nodes_for_path(current_path_id)
    nodes.sort(key=lambda n: n.sequence_order)

    # 1. Preserve History (COMPLETED and IN_PROGRESS)
    preserved_nodes = []
    preserved_course_ids = set()
    for n in nodes:
        if n.status in [NodeStatus.COMPLETED, NodeStatus.IN_PROGRESS]:
            preserved_nodes.append(n)
            preserved_course_ids.add(n.course_id)

    # 2. Get Proficiencies & Gaps
    proficiencies = {}
    for skill_id in state_repo.db.get("skills", {}).keys():
        prof = state_repo.get_learner_proficiency(learner_id, skill_id)
        proficiencies[skill_id] = prof["proficiency"]

    target_reqs = _get_target_role_requirements(learner_id)

    # 3. Identify required courses
    required_courses = set()
    for skill, target in target_reqs.items():
        if proficiencies.get(skill, 0.0) < target:
            course = _get_available_course_for_skill(skill)
            if course and course["course_id"] not in preserved_course_ids:
                required_courses.add(course["course_id"])

    # 4. Resolve Prerequisites Recursively
    _resolve_prerequisites_recursively(
        learner_id, required_courses, preserved_course_ids, proficiencies
    )

    # Remove any required_courses that are already in preserved_course_ids
    required_courses = required_courses - preserved_course_ids

    # 5. Rank & Sequence remaining
    course_objects = [state_repo.db["courses"][cid] for cid in required_courses]
    new_course_sequence = _rank_courses(course_objects, proficiencies, target_reqs)

    # 6. Check if effective plan changed
    old_future_courses = [
        n.course_id
        for n in nodes
        if n.status not in [NodeStatus.COMPLETED, NodeStatus.IN_PROGRESS]
    ]

    if new_course_sequence == old_future_courses:
        return {
            "path_id": current_path_id,
            "version": active_path.version,
            "previous_path_id": active_path.previous_path_id,
            "changed": False,
            "nodes": [n.model_dump() for n in nodes],
            "changes": [],
            "change_facts": [],
            "proficiency_changes": [],
        }

    # 7. Create New Path Version
    new_path_id = uuid.uuid4().hex
    new_version = active_path.version + 1

    new_path = LearningPath(
        path_id=new_path_id,
        learner_id=learner_id,
        version=new_version,
        previous_path_id=current_path_id,
        created_at=datetime.now(UTC).isoformat(),
        is_active=True,
    )

    # Deactivate old
    active_path.is_active = False

    # Create new nodes
    new_nodes = []
    seq = 1
    for p_node in preserved_nodes:
        # Clone it with new path_id
        cloned = PathNode(
            node_id=p_node.node_id,  # Keep node_id or generate new? Keep same node_id means it's the exact same node instance history
            path_id=new_path_id,
            course_id=p_node.course_id,
            sequence_order=seq,
            status=p_node.status,
        )
        new_nodes.append(cloned)
        seq += 1

    for cid in new_course_sequence:
        new_node_id = uuid.uuid4().hex
        new_node = PathNode(
            node_id=new_node_id,
            path_id=new_path_id,
            course_id=cid,
            sequence_order=seq,
            status=NodeStatus.LOCKED,
        )
        new_nodes.append(new_node)
        seq += 1

    # Persist
    state_repo.save_path(new_path)
    for n in new_nodes:
        state_repo.update_node(n)

    # Generate structured facts
    changes = []
    old_set = set(old_future_courses)
    new_set = set(new_course_sequence)

    for c in old_set - new_set:
        changes.append(
            {
                "type": "NODE_REMOVED",
                "course_id": c,
                "reason": "PREREQUISITE_MASTERY",  # Or no longer required
            }
        )

    for c in new_set - old_set:
        changes.append(
            {
                "type": "NODE_ADDED",
                "course_id": c,
                "reason": "NEWLY_ELIGIBLE",  # Or newly required
            }
        )

    # We could also add PROFICIENCY_CHANGE facts if we track the delta since last replan,
    # but for MVP we can just list current proficiencies.
    prof_changes: list[dict[str, Any]] = []

    return {
        "path_id": new_path_id,
        "version": new_version,
        "previous_path_id": current_path_id,
        "changed": True,
        "nodes": [n.model_dump() for n in new_nodes],
        "changes": changes,
        "change_facts": changes,
        "proficiency_changes": prof_changes,
    }
