import type { DemoRole } from "@/demo/types";

export const DEMO_ROLE_KEY = "statlearn:demo-role";

export function readDemoRole(): DemoRole {
  if (typeof window === "undefined") return "learner";
  return window.sessionStorage.getItem(DEMO_ROLE_KEY) === "admin"
    ? "admin"
    : "learner";
}

export function writeDemoRole(role: DemoRole) {
  window.sessionStorage.setItem(DEMO_ROLE_KEY, role);
}
