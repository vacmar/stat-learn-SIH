# Data Model

The `manthaino` application relies on an Exasol database to act as the authoritative source of truth for learner progression, skills, and course catalogues. The schema is highly normalized and designed to efficiently run analytical queries for dynamic pathway generation.

## Core Entities
- **Learners**: Represents the users of the system.
- **Goals**: The target career roles a learner is striving for (e.g., Data Engineer, AI Engineer).
- **Career Roles**: The predefined roles available in the system.
- **Skills**: Granular concepts or technologies (e.g., Python, Distributed Systems).
- **Courses**: Learning modules or nodes that teach specific skills.
- **Projects**: Larger practical tasks that assess multiple skills at once.

## Relationships
- **Role Skills**: Maps `career_roles` to `skills` with an `importance` weight and a `required_proficiency` target.
- **Course Skills**: Maps `courses` to the `skills` they teach, with a `contribution_weight` indicating how much proficiency they impart.
- **Course Prerequisites**: A directed graph mapping dependencies between courses (`is_mandatory` flags).

## Learner State
- **Learner Skills**: A real-time ledger of a learner's current `proficiency` and `confidence` in a skill.
- **Evidence**: An append-only log of how a learner acquired their proficiency (e.g., Assessment, Practical Task, Self-claim).
- **Path Instances & Path Nodes**: Tracks the active sequence of courses a learner is taking to achieve their goal.
- **Learning Progress**: Tracks the micro-state within a currently active `path_node` (current module, concept, percentage).
- **Conversations & Messages**: Stores the chat history with the AI Tutor for a specific `path_node`.

## Architecture Note
The LLM does not write to the state tables directly. It uses tools to submit evaluations or evidence, and the backend business logic resolves these into proficiency updates and node un-locking.
