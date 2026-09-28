import type { CatalogueSource, DomainCode, Level, ProgrammeFormat } from "@/demo/types";

export type TrainingProgramme = {
  id: string;
  title: string;
  source: CatalogueSource;
  competencyId: string;
  competency: string;
  domain: DomainCode;
  currentLevel: Level;
  targetLevel: Level;
  durationHours: number;
  durationLabel: string;
  format: ProgrammeFormat;
  reason: string;
  active: boolean;
  synthetic: true;
};

export const programmes: TrainingProgramme[] = [
  {
    id: "igot-official-analysis",
    title: "Analysis of official statistical datasets",
    source: "iGOT",
    competencyId: "stat-data-analysis",
    competency: "Statistical Data Analysis",
    domain: "STAT",
    currentLevel: "L2",
    targetLevel: "L4",
    durationHours: 12,
    durationLabel: "12 hours",
    format: "Self-paced module",
    reason: "Closes the high-priority gap from L2 to L4 on interpreting official tables.",
    active: true,
    synthetic: true,
  },
  {
    id: "nssta-survey-practicum",
    title: "Survey methodology practicum",
    source: "NSSTA",
    competencyId: "stat-survey-methodology",
    competency: "Survey Methodology",
    domain: "STAT",
    currentLevel: "L2",
    targetLevel: "L3",
    durationHours: 8,
    durationLabel: "8 hours",
    format: "Instructor-led programme",
    reason: "Addresses the unmet L3 coverage item for household surveys.",
    active: true,
    synthetic: true,
  },
  {
    id: "tpac-data-quality",
    title: "Data quality frameworks for published tables",
    source: "TPAC",
    competencyId: "stat-data-quality",
    competency: "Data Quality",
    domain: "STAT",
    currentLevel: "L3",
    targetLevel: "L4",
    durationHours: 6,
    durationLabel: "6 hours",
    format: "Blended workshop",
    reason: "Targets the single unmet L4 data-quality item.",
    active: false,
    synthetic: true,
  },
  {
    id: "nssta-sampling-note",
    title: "Sample allocation across strata",
    source: "NSSTA",
    competencyId: "stat-sampling",
    competency: "Sampling Design",
    domain: "STAT",
    currentLevel: "L3",
    targetLevel: "L4",
    durationHours: 5,
    durationLabel: "5 hours",
    format: "Self-paced module",
    reason: "Supports the moderate gap on stratum allocation.",
    active: false,
    synthetic: true,
  },
  {
    id: "igot-sdg",
    title: "SDG indicator disaggregation",
    source: "iGOT",
    competencyId: "stat-sdg",
    competency: "SDG Indicators",
    domain: "STAT",
    currentLevel: "L2",
    targetLevel: "L3",
    durationHours: 10,
    durationLabel: "10 hours",
    format: "Blended workshop",
    reason: "Continues developing practice on disaggregation.",
    active: false,
    synthetic: true,
  },
  {
    id: "nssta-reproducible-tables",
    title: "Reproducible official tables",
    source: "NSSTA",
    competencyId: "tech-statistical-computing",
    competency: "Statistical Computing Practice",
    domain: "TECH",
    currentLevel: "L3",
    targetLevel: "L4",
    durationHours: 9,
    durationLabel: "9 hours",
    format: "Instructor-led programme",
    reason: "Covers documented table releases using approved statistical software.",
    active: false,
    synthetic: true,
  },
  {
    id: "tpac-geospatial",
    title: "Geospatial briefing for statistical offices",
    source: "TPAC",
    competencyId: "tech-gis",
    competency: "Geospatial Statistics",
    domain: "TECH",
    currentLevel: "L2",
    targetLevel: "L3",
    durationHours: 4,
    durationLabel: "4 hours",
    format: "Instructor-led programme",
    reason: "Scheduled after the priority statistical gaps.",
    active: false,
    synthetic: true,
  },
  {
    id: "igot-revisions",
    title: "Communicating statistical revisions",
    source: "iGOT",
    competencyId: "beh-communication",
    competency: "Official Communication",
    domain: "BEH",
    currentLevel: "L3",
    targetLevel: "L4",
    durationHours: 3,
    durationLabel: "3 hours",
    format: "Self-paced module",
    reason: "Addresses the open L4 practice on revision notices.",
    active: false,
    synthetic: true,
  },
  {
    id: "tpac-coordination",
    title: "Coordination with training counterparts",
    source: "TPAC",
    competencyId: "beh-coordination",
    competency: "Stakeholder Coordination",
    domain: "BEH",
    currentLevel: "L3",
    targetLevel: "L4",
    durationHours: 6,
    durationLabel: "6 hours",
    format: "Blended workshop",
    reason: "Pairs with the communication programme for the developing L4 practice.",
    active: false,
    synthetic: true,
  },
];

export const dashboardRecommendations = [
  programmes[0],
  programmes[1],
  programmes[2],
];

export const catalogueSources = ["iGOT", "NSSTA", "TPAC"] as const;
export const catalogueDomains = ["STAT", "TECH", "GOV", "BEH"] as const;
