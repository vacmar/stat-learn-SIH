
export interface PathNode {
  node_id: string;
  course_id: string;
  course_title?: string;
  status: "LOCKED" | "UNLOCKED" | "IN_PROGRESS" | "COMPLETED";
  sequence_order: number;
}

export interface LearningPath {
  path_id: string;
  learner_id: string;
  nodes: PathNode[];
  is_active: boolean;
  goal?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  structured?: any;
}

export interface UnlockConditions {
  locked: boolean;
  reasons: Array<{
    prerequisite_skill: string;
    prerequisite_title?: string;
    required_proficiency: number;
    current_proficiency: number;
    status: string;
    message?: string;
  }>;
}

export interface RegeneratePathResult {
  path_id: string;
  version: number;
  previous_path_id: string;
  changed: boolean;
  nodes: PathNode[];
  changes: Array<{ type: string; course_id: string; reason: string }>;
  proficiency_changes: unknown[];
}

export interface VerificationResult {
  learner_id: string;
  discrepancies: Array<{
    skill_id: string;
    claimed_proficiency: number;
    verified_proficiency: number;
    gap: number;
  }>;
  has_discrepancy: boolean;
}

export interface CompletionPayload {
  learner_id: string;
  assessment_score?: number;
  practical_pass?: boolean;
}

export type DiagnosticQuestion = {
  id: string;
  question: string;
  options: string[];
  competency_id: string;
  competency_name: string;
  domain: string;
  proficiency_level: string;
  topic: string;
};

export type DiagnosticAssessment = {
  assessment_id: string;
  title: string;
  purpose: string;
  question_count: number;
  domains: string[];
  questions: DiagnosticQuestion[];
};

export type AttemptState = {
  attempt_id: string;
  status: "in_progress" | "completed";
  answers: { question_id: string; selected_answer: string }[];
};

export type CompetencyEvidence = {
  correct: number;
  evaluated: number;
  incorrect: number;
  incorrect_question_ids: string[];
  correct_question_ids: string[];
  incorrect_topics: string[];
};

export type CompetencyResult = {
  competency_id: string;
  name: string;
  domain: string;
  score_percent: number;
  current_level: string;
  target_level: string;
  gap: number;
  status: string;
  priority: string;
  evidence: CompetencyEvidence;
};

export type CompetencyAttemptResult = {
  attempt_id: string;
  overall_score_percent: number;
  competencies_assessed: number;
  priority_gap_count: number;
  domain_readiness: { domain: string; percent: number; competencies_assessed: number }[];
  competencies: CompetencyResult[];
};

export type CompetencyProfile = CompetencyAttemptResult & {
  assessed: boolean;
  learner_id: string;
  overall_score_percent: number | null;
  attempt_id: string | null;
  completed_at: string | null;
};

export type CompetencyGapList = {
  attempt_id: string | null;
  completed_at?: string | null;
  assessment_title?: string;
  gaps: (CompetencyResult & { assessment_attempt_id?: string })[];
};

export type TrainingRecommendation = {
  rank: number;
  programme_id: string;
  title: string;
  source: string;
  description: string;
  duration: string;
  format: string;
  synthetic: true;
  competency_id: string;
  current_level: string;
  target_level: string;
  programme_level: string;
  gap: number;
  priority: string;
  status: string;
  prerequisite_status: "Met" | "Not met";
  recommendation_reason: string;
  matched_competencies: { competency_id: string; name: string; domain: string }[];
};

export type RecommendationResponse = {
  learner_id: string | null;
  assessment_attempt_id: string | null;
  recommendations: TrainingRecommendation[];
  unmatched_gaps: { competency_id: string; name?: string; gap: number }[];
  message: string | null;
};

export type PathwayJourney = {
  competency_id: string;
  name: string;
  current_level: string;
  target_level: string;
  gap: number;
  priority: string;
  status: string;
  steps: {
    state: string;
    label: string;
    detail?: string;
    source?: string;
    prerequisite_status?: string;
    recommendation_reason?: string;
    programme_id?: string;
    synthetic?: boolean;
  }[];
};

export type CatalogueProgramme = {
  id: string;
  title: string;
  source: string;
  description: string;
  competencies: { competency_id: string; name: string; domain: string }[];
  domains: string[];
  level: string;
  duration_hours: number;
  duration: string;
  format: string;
  prerequisites: { competency_id: string; min_level: string }[];
  synthetic: boolean;
  external_url?: string;
  keywords?: string[];
};

export type AdminDocument = {
  id: string;
  title: string;
  source: string;
  filename: string;
  status: string;
  summary: string;
  synthetic: boolean;
  chunks: number;
  sections?: string[];
  added: string;
};

export type ReviewEvidence = {
  chunk_id: string;
  section: string;
  text: string;
  document_title: string;
  source: string;
};

export type ReviewQuestion = {
  id: string;
  question: string;
  options: string[];
  correct_option: string;
  explanation: string;
  competency: string;
  domain: string;
  target_level: string;
  status: string;
  origin: string;
  badge: string;
  source: string;
  document_title: string;
  created_at: string;
  approved_at: string | null;
  evidence: ReviewEvidence[];
};

export type AdminOverview = {
  learning_materials: number;
  draft_mcqs: number;
  awaiting_review: number;
  approved_questions: number;
  rejected_questions: number;
  generated_today: number;
};

const competencyFetch = (): RequestInit => ({
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-Statlearn-Demo-Learner": "arun-kumar",
  },
});

const adminFetch = (): RequestInit => ({
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-Statlearn-Demo-Actor": "training-admin",
  },
});

export const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const AI_SERVICE_URL = process.env.NEXT_PUBLIC_AI_SERVICE_URL || "http://localhost:8001";

const defaultFetchOpts: RequestInit = {
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
  }
};

/** Turn FastAPI `{"detail":"..."}` bodies into plain Error messages. */
async function errorFromResponse(res: Response, fallback: string): Promise<Error> {
  const text = await res.text();
  if (!text) return new Error(fallback);
  try {
    const parsed = JSON.parse(text) as { detail?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return new Error(parsed.detail);
    }
    if (Array.isArray(parsed.detail)) {
      const parts = parsed.detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: unknown }).msg);
          }
          return "";
        })
        .filter(Boolean);
      if (parts.length) return new Error(parts.join(". "));
    }
  } catch {
    /* plain text body */
  }
  return new Error(text);
}

export const api = {
  // Auth
  async getRegistrationForm(): Promise<{
    profile: {
      name: string;
      email: string;
      posting: string | null;
      ministry: string | null;
      state_name: string | null;
      department: string | null;
      organisation: string | null;
      designation: string | null;
    } | null;
    options: Array<{ kind: string; posting: string; parent_label: string | null; label: string }>;
  }> {
    const res = await fetch(`${BACKEND_URL}/auth/registration-form`, { ...defaultFetchOpts, cache: "no-store" });
    if (!res.ok) throw await errorFromResponse(res, "Registration details unavailable");
    return res.json();
  },
  async signup(data: any): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/auth/signup`, { ...defaultFetchOpts, method: "POST", body: JSON.stringify(data) });
    if (!res.ok) throw await errorFromResponse(res, "Signup failed");
    return res.json();
  },
  async login(data: any): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/auth/login`, { ...defaultFetchOpts, method: "POST", body: JSON.stringify(data) });
    if (!res.ok) throw await errorFromResponse(res, "Login failed");
    return res.json();
  },
  async logout(): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/auth/logout`, { ...defaultFetchOpts, method: "POST" });
    return res.json();
  },
  async getMe(): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/auth/me`, { ...defaultFetchOpts });
    if (!res.ok) throw new Error("Not authenticated");
    return res.json();
  },

  // Paths & Lessons
  async getActivePath(): Promise<LearningPath> {
    const res = await fetch(`${BACKEND_URL}/paths/me/active`, { ...defaultFetchOpts, cache: "no-store" });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  async ensureActivePath(): Promise<LearningPath & { regenerated?: boolean }> {
    const res = await fetch(`${BACKEND_URL}/paths/me/ensure`, {
      ...defaultFetchOpts,
      method: "POST",
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  async getLessonSession(nodeId: string): Promise<{
    node_id: string;
    conversation_id: string;
    messages: Array<{ role: string; content: string }>;
    practice_notes: string;
    ai_ready?: boolean;
    ready_reason?: string;
  }> {
    const res = await fetch(`${BACKEND_URL}/lessons/me/${nodeId}/session`, {
      ...defaultFetchOpts,
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  async saveLessonReady(nodeId: string, aiReady: boolean, readyReason?: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/lessons/me/${nodeId}/ready`, {
      ...defaultFetchOpts,
      method: "PUT",
      body: JSON.stringify({ ai_ready: aiReady, ready_reason: readyReason }),
    });
    if (!res.ok) throw new Error(`Failed to save ready state: ${res.status}`);
    return res.json();
  },

  async saveLessonMessages(
    nodeId: string,
    messages: Array<{ role: string; content: string }>,
    replace = true
  ): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/lessons/me/${nodeId}/messages`, {
      ...defaultFetchOpts,
      method: "POST",
      body: JSON.stringify({ messages, replace }),
    });
    if (!res.ok) throw new Error(`Failed to save lesson messages: ${res.status}`);
    return res.json();
  },

  async saveLessonNotes(nodeId: string, practiceNotes: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/lessons/me/${nodeId}/notes`, {
      ...defaultFetchOpts,
      method: "PUT",
      body: JSON.stringify({ practice_notes: practiceNotes }),
    });
    if (!res.ok) throw new Error(`Failed to save notes: ${res.status}`);
    return res.json();
  },

  async completeLesson(learnerId: string, nodeId: string, opts?: { assessment_score?: number; practical_pass?: boolean }): Promise<any> {
    const body: CompletionPayload = {
      learner_id: learnerId,
      assessment_score: opts?.assessment_score ?? 85,
      practical_pass: opts?.practical_pass ?? true,
    };
    const res = await fetch(`${BACKEND_URL}/nodes/${nodeId}/complete`, {
      ...defaultFetchOpts,
      method: "POST",
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Failed to complete lesson: ${res.status}`);
    return res.json();
  },

  async startNode(nodeId: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/nodes/${nodeId}/start`, { ...defaultFetchOpts, method: "POST" });
    if (!res.ok) throw new Error(`Failed to start node: ${res.status}`);
    return res.json();
  },

  async getNodeProgress(nodeId: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/nodes/${nodeId}/progress`, { ...defaultFetchOpts, cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to get node progress: ${res.status}`);
    return res.json();
  },

  async getWeakConcepts(nodeId: string, learnerId: string): Promise<{ weak_concepts: Array<{ concept: string; error_count: number; latest_description: string }> }> {
    const res = await fetch(
      `${BACKEND_URL}/nodes/${nodeId}/mistakes?learner_id=${encodeURIComponent(learnerId)}`,
      { ...defaultFetchOpts, cache: "no-store" }
    );
    if (!res.ok) throw new Error(`Failed to get weak concepts: ${res.status}`);
    return res.json();
  },

  async getUnlockConditions(nodeId: string, learnerId: string): Promise<UnlockConditions> {
    const res = await fetch(
      `${BACKEND_URL}/nodes/${nodeId}/unlock-conditions?learner_id=${encodeURIComponent(learnerId)}`,
      { ...defaultFetchOpts, cache: "no-store" }
    );
    if (!res.ok) throw new Error(`Failed to get unlock conditions: ${res.status}`);
    return res.json();
  },

  async regeneratePath(pathId: string, learnerId: string): Promise<RegeneratePathResult> {
    const res = await fetch(`${BACKEND_URL}/paths/${pathId}/regenerate`, {
      ...defaultFetchOpts,
      method: "POST",
      body: JSON.stringify({ learner_id: learnerId }),
    });
    if (!res.ok) throw new Error(`Failed to regenerate path: ${res.status}`);
    return res.json();
  },

  async getVerification(): Promise<VerificationResult | null> {
    try {
      const me = await this.getMe();
      const skillIds = new Set<string>([
        ...(me.known_skills ?? []),
        ...Object.keys(me.self_reported_proficiency ?? {}),
      ]);
      if (skillIds.size === 0) return null;

      const discrepancies: VerificationResult["discrepancies"] = [];
      for (const skill_id of skillIds) {
        const res = await fetch(`${BACKEND_URL}/verification/skills/${encodeURIComponent(skill_id)}/result`, {
          ...defaultFetchOpts,
          cache: "no-store",
        });
        if (!res.ok) continue;
        const body = await res.json();
        const result = body.result ?? body;
        if (result.discrepancy) {
          discrepancies.push({
            skill_id,
            claimed_proficiency: result.claimed_proficiency,
            verified_proficiency: result.verified_proficiency,
            gap: result.discrepancy_delta ?? result.claimed_proficiency - result.verified_proficiency,
          });
        }
      }

      if (discrepancies.length === 0) return null;
      return {
        learner_id: me.learner_id,
        discrepancies,
        has_discrepancy: true,
      };
    } catch {
      return null;
    }
  },

  async startAssessment(assessmentId: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/assessments/start?assessment_id=${assessmentId}`, { ...defaultFetchOpts, method: "POST" });
    if (!res.ok) throw new Error(`Failed to start assessment: ${res.status}`);
    return res.json();
  },

  async submitAssessmentAnswer(assessmentId: string, questionId: string, answer: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/assessments/${assessmentId}/answer`, {
      ...defaultFetchOpts,
      method: "POST",
      body: JSON.stringify({ question_id: questionId, answer }),
    });
    if (!res.ok) throw new Error(`Failed to submit answer: ${res.status}`);
    return res.json();
  },

  async finalizeAssessment(assessmentId: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/assessments/${assessmentId}/finalize`, { ...defaultFetchOpts, method: "POST" });
    if (!res.ok) throw new Error(`Failed to finalize assessment: ${res.status}`);
    return res.json();
  },

  async executeWorkspaceCode(code: string, language = "python"): Promise<{
    ok: boolean;
    stdout: string;
    stderr: string;
    exit_code: number | null;
    timed_out: boolean;
    language: string;
  }> {
    const res = await fetch(`${BACKEND_URL}/workspace/execute`, {
      ...defaultFetchOpts,
      method: "POST",
      body: JSON.stringify({ code, language }),
    });
    if (!res.ok) throw await errorFromResponse(res, "Failed to run code");
    return res.json();
  },

  // Projects
  async getProject(projectId: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/projects/${projectId}`, { ...defaultFetchOpts });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  async getRecommendedProject(): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/projects/me/recommended`, { ...defaultFetchOpts });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  async submitProject(projectId: string, learnerId: string, artifact: string): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/projects/${projectId}/submit`, {
      ...defaultFetchOpts,
      method: "POST",
      body: JSON.stringify({ learner_id: learnerId, artifact }),
    });
    if (!res.ok) throw new Error(`Failed to submit project: ${res.status}`);
    return res.json();
  },

  async evaluateProject(projectId: string, evaluation: Record<string, unknown>): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/projects/${projectId}/evaluate`, {
      ...defaultFetchOpts,
      method: "POST",
      body: JSON.stringify(evaluation),
    });
    if (!res.ok) throw new Error(`Failed to evaluate project: ${res.status}`);
    return res.json();
  },

  // Profile & Goals
  async getProfile(): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/learners/me`, { ...defaultFetchOpts });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  async getGoals(): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/goals/`, { ...defaultFetchOpts });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  // Onboarding
  async getOnboarding(): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/onboarding/`, { ...defaultFetchOpts });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  async saveOnboarding(data: any): Promise<any> {
    const res = await fetch(`${BACKEND_URL}/onboarding/`, { ...defaultFetchOpts, method: "POST", body: JSON.stringify(data) });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  },

  // AI Service Calls
  async getDiagnostic(): Promise<DiagnosticAssessment> {
    const res = await fetch(`${BACKEND_URL}/assessments/diagnostic`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Assessment unavailable");
    return res.json();
  },
  async createAttempt(): Promise<AttemptState> {
    const res = await fetch(`${BACKEND_URL}/assessments/attempts`, { ...competencyFetch(), method: "POST" });
    if (!res.ok) throw await errorFromResponse(res, "Attempt creation failed");
    return res.json();
  },
  async getAttempt(attemptId: string): Promise<AttemptState> {
    const res = await fetch(`${BACKEND_URL}/assessments/attempts/${attemptId}`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Attempt unavailable");
    return res.json();
  },
  async submitAnswer(attemptId: string, questionId: string, selectedAnswer: string): Promise<void> {
    const res = await fetch(`${BACKEND_URL}/assessments/attempts/${attemptId}/answers`, {
      ...competencyFetch(),
      method: "POST",
      body: JSON.stringify({ question_id: questionId, selected_answer: selectedAnswer }),
    });
    if (!res.ok) throw await errorFromResponse(res, "Answer submission failed");
  },
  async completeAttempt(attemptId: string): Promise<CompetencyAttemptResult> {
    const res = await fetch(`${BACKEND_URL}/assessments/attempts/${attemptId}/complete`, {
      ...competencyFetch(),
      method: "POST",
    });
    if (!res.ok) throw await errorFromResponse(res, "Result unavailable");
    return res.json();
  },
  async getAttemptResult(attemptId: string): Promise<CompetencyAttemptResult> {
    const res = await fetch(`${BACKEND_URL}/assessments/attempts/${attemptId}/result`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Result unavailable");
    return res.json();
  },
  async getCompetencyProfile(): Promise<CompetencyProfile> {
    const res = await fetch(`${BACKEND_URL}/competencies/profile`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Backend unavailable");
    return res.json();
  },
  async getCompetencyGaps(): Promise<CompetencyGapList> {
    const res = await fetch(`${BACKEND_URL}/competencies/gaps`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Backend unavailable");
    return res.json();
  },
  async getRecommendations(): Promise<RecommendationResponse> {
    const res = await fetch(`${BACKEND_URL}/competencies/recommendations`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Backend unavailable");
    return res.json();
  },
  async getPathway(): Promise<{ message: string | null; journeys: PathwayJourney[]; assessment_attempt_id: string | null }> {
    const res = await fetch(`${BACKEND_URL}/competencies/pathway`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Backend unavailable");
    return res.json();
  },
  async getCatalogue(): Promise<{ synthetic: boolean; note: string; programmes: CatalogueProgramme[] }> {
    const res = await fetch(`${BACKEND_URL}/competencies/catalogue`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Backend unavailable");
    return res.json();
  },
  async getCourseProgress(): Promise<{ courses: Array<{ programme_id: string; passed: boolean; status: string; correct_count: number; question_count: number }> }> {
    const res = await fetch(`${BACKEND_URL}/competencies/course-progress`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Backend unavailable");
    return res.json();
  },
  async getCourse(programmeId: string): Promise<{
    id: string;
    title: string;
    source: string;
    description: string;
    level: string;
    duration: string;
    external_url?: string;
    lessons: string[];
    pass_rule: string;
    questions: Array<{ id: string; prompt: string; options: string[] }>;
    progress: { status: string; passed: boolean; correct_count: number; question_count: number };
  }> {
    const res = await fetch(`${BACKEND_URL}/competencies/catalogue/${programmeId}`, competencyFetch());
    if (!res.ok) throw await errorFromResponse(res, "Course unavailable");
    return res.json();
  },
  async submitCourse(programmeId: string, answers: Array<{ question_id: string; selected_answer: string }>): Promise<{
    score_percent: number;
    correct_count: number;
    question_count: number;
    passed_this_attempt: boolean;
    status: string;
    reviews: Array<{ question_id: string; correct: boolean }>;
  }> {
    const res = await fetch(`${BACKEND_URL}/competencies/catalogue/${programmeId}/submit`, {
      ...competencyFetch(),
      method: "POST",
      body: JSON.stringify({ answers }),
    });
    if (!res.ok) throw await errorFromResponse(res, "Could not save the course");
    return res.json();
  },
  async getAdminOverview(): Promise<AdminOverview> {
    const res = await fetch(`${BACKEND_URL}/admin/overview`, adminFetch());
    if (!res.ok) throw await errorFromResponse(res, "Training Admin session required");
    return res.json();
  },
  async getAdminMaterials(): Promise<{ documents: AdminDocument[] }> {
    const res = await fetch(`${BACKEND_URL}/admin/materials`, adminFetch());
    if (!res.ok) throw await errorFromResponse(res, "Training Admin session required");
    return res.json();
  },
  async generateDemoDraft(body: { document_id: string; competency_id: string; target_level: string; count: number }): Promise<{ drafts: ReviewQuestion[] }> {
    const res = await fetch(`${BACKEND_URL}/admin/mcq/demo-draft`, { ...adminFetch(), method: "POST", body: JSON.stringify(body) });
    if (!res.ok) throw await errorFromResponse(res, "Draft was not created");
    return res.json();
  },
  async generateModelDraft(body: { document_id: string; competency_id: string; target_level: string; count: number }): Promise<{ drafts: ReviewQuestion[] }> {
    const res = await fetch(`${BACKEND_URL}/admin/mcq/generate`, { ...adminFetch(), method: "POST", body: JSON.stringify(body) });
    if (!res.ok) throw await errorFromResponse(res, "AI generation unavailable. No draft was created.");
    return res.json();
  },
  async getReviewQueue(): Promise<{ drafts: ReviewQuestion[] }> {
    const res = await fetch(`${BACKEND_URL}/admin/mcq-review`, adminFetch());
    if (!res.ok) throw await errorFromResponse(res, "Training Admin session required");
    return res.json();
  },
  async approveQuestion(id: string): Promise<void> {
    const res = await fetch(`${BACKEND_URL}/admin/mcq/${id}/approve`, { ...adminFetch(), method: "POST" });
    if (!res.ok) throw await errorFromResponse(res, "Approval failed");
  },
  async rejectQuestion(id: string): Promise<void> {
    const res = await fetch(`${BACKEND_URL}/admin/mcq/${id}/reject`, { ...adminFetch(), method: "POST" });
    if (!res.ok) throw await errorFromResponse(res, "Rejection failed");
  },
  async getQuestionBank(domain: string, level: string): Promise<{ questions: ReviewQuestion[] }> {
    const params = new URLSearchParams();
    if (domain !== "All") params.set("domain", domain);
    if (level !== "All") params.set("level", level);
    const res = await fetch(`${BACKEND_URL}/admin/question-bank?${params.toString()}`, adminFetch());
    if (!res.ok) throw await errorFromResponse(res, "Training Admin session required");
    return res.json();
  },

  async chatTutor(message: string, learnerId: string, nodeId: string): Promise<ChatMessage> {
    const res = await fetch(`${AI_SERVICE_URL}/chat`, {
      ...defaultFetchOpts,
      method: "POST",
      body: JSON.stringify({ message, learner_id: learnerId, node_id: nodeId }),
    });
    if (!res.ok) throw new Error(`Failed to chat: ${res.status}`);
    return res.json();
  }
};
