import type { DomainCode, Level } from "@/demo/types";

export type DiagnosticQuestion = {
  id: string;
  domain: DomainCode;
  competency: string;
  level: Level;
  prompt: string;
  options: string[];
};

export const diagnosticMeta = {
  title: "Diagnostic Competency Assessment",
  purpose:
    "Assess your current competency levels and identify areas requiring targeted development.",
  durationLabel: "20 minutes",
  questionCount: 8,
  domains: ["STAT", "TECH", "GOV", "BEH"] as DomainCode[],
};

export const diagnosticQuestions: DiagnosticQuestion[] = [
  {
    id: "dq-stat-1",
    domain: "STAT",
    competency: "Statistical Data Analysis",
    level: "L3",
    prompt:
      "A published table shows a sharp change after a classification update. What should the statistical officer do before describing the change as a movement in the underlying series?",
    options: [
      "Confirm whether the classification break has been adjusted or footnoted",
      "Treat every large change as a seasonal effect",
      "Replace the table with an average of the last five years",
      "Suppress the series until the next census",
    ],
  },
  {
    id: "dq-stat-2",
    domain: "STAT",
    competency: "Survey Methodology",
    level: "L3",
    prompt:
      "A household survey frame excludes newly formed dwellings in one district. Which description fits the risk?",
    options: [
      "Coverage error that can bias estimates for that district",
      "A labelling convention that only affects the questionnaire layout",
      "A presentation choice for the press note",
      "A behavioural competency for field supervisors",
    ],
  },
  {
    id: "dq-stat-3",
    domain: "STAT",
    competency: "Data Quality",
    level: "L4",
    prompt:
      "Which check belongs in a data-quality review of a table proposed for release?",
    options: [
      "Compare totals with the agreed source and record any unexplained difference",
      "Choose the chart colour preferred by the communication team",
      "Shorten the title so it fits a social-media graphic",
      "Remove footnotes to reduce the length of the release",
    ],
  },
  {
    id: "dq-tech-1",
    domain: "TECH",
    competency: "Statistical Computing Practice",
    level: "L4",
    prompt:
      "A colleague must reproduce an official table six months later. What should be retained with the release file?",
    options: [
      "The processing steps, source extract, and software version used for the table",
      "Only the final PDF of the press note",
      "A personal spreadsheet that is not stored with the release",
      "The draft slide used in an internal briefing",
    ],
  },
  {
    id: "dq-tech-2",
    domain: "TECH",
    competency: "Open Data Practice",
    level: "L3",
    prompt:
      "An open statistical release is being prepared. Which practice matches open-data publication for an official series?",
    options: [
      "Provide a machine-readable file with a clear licence and field definitions",
      "Share the file only through a private messaging group",
      "Publish the chart image without the underlying figures",
      "Omit the reference period to keep the file short",
    ],
  },
  {
    id: "dq-gov-1",
    domain: "GOV",
    competency: "Data Privacy",
    level: "L4",
    prompt:
      "A microdata file still contains a direct identifier. What is the appropriate step before any wider sharing?",
    options: [
      "Remove or protect the identifier according to the approved privacy rule",
      "Publish the file if the identifier is in a separate column",
      "Ask the communication team to decide after the press briefing",
      "Keep the identifier because it helps readers contact respondents",
    ],
  },
  {
    id: "dq-gov-2",
    domain: "GOV",
    competency: "Information Security Practice",
    level: "L3",
    prompt:
      "An official notices an unexpected download of a pre-release table. What is the right first action?",
    options: [
      "Report the incident through the approved security channel and preserve the record",
      "Forward the file to a personal account for safekeeping",
      "Ignore it if the table looks familiar",
      "Post a correction on a public forum before informing the office",
    ],
  },
  {
    id: "dq-beh-1",
    domain: "BEH",
    competency: "Official Communication",
    level: "L4",
    prompt:
      "A previously published figure must be revised. How should the revision be communicated?",
    options: [
      "State the previous figure, the revised figure, and the reason in the official note",
      "Replace the figure quietly so readers see only the new value",
      "Describe the revision as a change in policy",
      "Delay all future releases until the series is redrawn",
    ],
  },
];

export type ReviewItem = {
  id: string;
  stem: string;
  competency: string;
  domain: DomainCode;
  level: Level;
  state: "pending_review" | "published" | "draft";
  sourceTitle: string;
  sourceExcerpt: string;
};

export const learningMaterial = {
  id: "mat-sampling-note",
  title: "Sampling concepts for official surveys",
  kind: "Synthetic note",
  pages: 2,
  status: "Ready for a later generation phase",
  summary:
    "A short original note on coverage, frames, and stratum allocation. It is demo material, not an official course file.",
};

export const reviewItems: ReviewItem[] = [
  {
    id: "mcq-draft-1",
    stem: "Why does an incomplete dwelling frame matter for a household survey estimate?",
    competency: "Survey Methodology",
    domain: "STAT",
    level: "L3",
    state: "pending_review",
    sourceTitle: learningMaterial.title,
    sourceExcerpt:
      "If newly formed dwellings are missing from the frame, households in those dwellings have no chance of selection.",
  },
  {
    id: "mcq-draft-2",
    stem: "What should be recorded when sample size is allocated across strata?",
    competency: "Sampling Design",
    domain: "STAT",
    level: "L4",
    state: "pending_review",
    sourceTitle: learningMaterial.title,
    sourceExcerpt:
      "Allocation notes should state the stratum, the allocated size, and the rule used to arrive at that size.",
  },
];

export const questionBank: ReviewItem[] = [
  ...diagnosticQuestions.map((question) => ({
    id: question.id,
    stem: question.prompt,
    competency: question.competency,
    domain: question.domain,
    level: question.level,
    state: "published" as const,
    sourceTitle: "Diagnostic item bank",
    sourceExcerpt: "Seeded diagnostic item for the screening profile. Not generated from an upload.",
  })),
  ...reviewItems,
];

export const adminMetrics = {
  totalLearners: 1,
  competenciesAssessed: 18,
  priorityGaps: 3,
  trainingProgrammes: 9,
  mcqsGenerated: diagnosticQuestions.length + reviewItems.length,
  mcqsAwaitingReview: reviewItems.length,
};
