import { programmes } from "@/demo/catalog";
import { priorityGaps } from "@/demo/competencies";

export const pathwayStages = [
  "Current competency state",
  "Competency gap",
  "Recommended training",
  "Assessment",
  "Target proficiency",
] as const;

export type PathwayPlan = {
  competencyId: string;
  competency: string;
  currentLevel: string;
  targetLevel: string;
  gapLabel: string;
  programmeId: string;
  programmeTitle: string;
  source: "iGOT" | "NSSTA" | "TPAC";
  assessment: string;
  targetLabel: string;
};

export const pathwayPlans: PathwayPlan[] = priorityGaps.map((gap) => {
  const programme = programmes.find((item) => item.competencyId === gap.id);
  return {
    competencyId: gap.id,
    competency: gap.name,
    currentLevel: gap.currentLevel,
    targetLevel: gap.targetLevel,
    gapLabel: `${gap.currentLevel} to ${gap.targetLevel}`,
    programmeId: programme?.id ?? "",
    programmeTitle: programme?.title ?? "Programme to be assigned",
    source: programme?.source ?? "iGOT",
    assessment: `Follow-up items at ${gap.targetLevel} for ${gap.name}`,
    targetLabel: `${gap.name} at ${gap.targetLevel}`,
  };
});
