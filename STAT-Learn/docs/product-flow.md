# Product flow

High-level learner journey (GOAL → learn → verify → replan):

1. **Sign up / log in** — session established via backend auth.
2. **Onboarding** — goal, profile, self-reported skills; backend seeds or regenerates an active path.
3. **Dashboard / path** — view nodes; locked nodes show prerequisite reasons; regenerate path when goals or proficiency change.
4. **Focus lesson** — consume node content; tutor chat via AI service; rich notes; confirm mastery when ready.
5. **Workspace (practice pad)** — draft code for an unlocked/completed path node; `POST /workspace/execute` runs Python and shows stdout/stderr. Teaching/mastery still live in the lesson.
6. **Assessment & verification** — adaptive/practical signals fused into verified proficiency; discrepancies vs self-claim surfaced on profile/assessment.
7. **Projects** — submit artifact URL; structured evaluation updates evidence and may unlock downstream nodes.
8. **Progress** — mastery, weak concepts (mistakes), completed nodes, history timeline.
9. **Replan** — `POST /paths/{path_id}/regenerate` preserves completed work and explains node additions/removals.

Demo video & pitch deck: [Google Drive](https://drive.google.com/drive/folders/1gJi4xPHb1ambAe_zFNwnwIV2xQTDvYt1?usp=sharing).
