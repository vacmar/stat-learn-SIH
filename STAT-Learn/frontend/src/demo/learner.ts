import type { DemoRole } from "@/demo/types";

export const demoLearner = {
  name: "Arun Kumar",
  role: "Statistical Officer",
  organisation: "Official Statistical System",
  language: "English",
  readinessPercent: 72,
  competenciesAssessed: 18,
  priorityGapCount: 3,
  activeProgrammeCount: 2,
} as const;

export const adminSession = {
  label: "Training Admin",
  role: "Training Admin",
} as const;

export function sessionIdentity(role: DemoRole) {
  if (role === "admin") {
    return { name: adminSession.label, role: adminSession.role };
  }
  return { name: demoLearner.name, role: demoLearner.role };
}
