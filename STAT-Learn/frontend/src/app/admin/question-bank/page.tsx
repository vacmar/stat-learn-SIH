"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/Sidebar";
import { api, type ReviewQuestion } from "@/lib/api";
import { readDemoRole } from "@/demo/role";

export default function QuestionBankPage() {
  const [questions, setQuestions] = useState<ReviewQuestion[]>([]);
  const [domain, setDomain] = useState("All");
  const [level, setLevel] = useState("All");
  const [error, setError] = useState("");

  useEffect(() => {
    if (readDemoRole() !== "admin") {
      setError("Training Admin session required");
      return;
    }
    api
      .getQuestionBank(domain, level)
      .then((payload) => setQuestions(payload.questions))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Training Admin session required"));
  }, [domain, level]);

  return (
    <div>
      <PageHeader
        kicker="Question bank"
        title="Question Bank"
        description="Approved questions only. Drafts and rejected items stay out of this list and out of the diagnostic."
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      <div className="mb-4 flex gap-3">
        <label className="text-xs text-muted-foreground">
          Domain
          <select value={domain} onChange={(event) => setDomain(event.target.value)} className="mt-1 block rounded-md border border-input bg-card px-2 py-1.5 text-sm">
            {["All", "STAT", "TECH", "GOV", "BEH"].map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="text-xs text-muted-foreground">
          Level
          <select value={level} onChange={(event) => setLevel(event.target.value)} className="mt-1 block rounded-md border border-input bg-card px-2 py-1.5 text-sm">
            {["All", "L1", "L2", "L3", "L4", "L5"].map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>
      {questions.length === 0 && !error ? (
        <p className="mb-4 text-sm text-muted-foreground">No approved questions are available yet.</p>
      ) : null}
      <div className="overflow-x-auto rounded-lg border border-border bg-card">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-3 py-2 font-medium">Question</th>
              <th className="px-3 py-2 font-medium">Competency</th>
              <th className="px-3 py-2 font-medium">Level</th>
              <th className="px-3 py-2 font-medium">Source</th>
              <th className="px-3 py-2 font-medium">Approved</th>
              <th className="px-3 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {questions.map((item) => (
              <tr key={item.id} className="border-b border-border last:border-0">
                <td className="max-w-md px-3 py-2.5">{item.question}</td>
                <td className="px-3 py-2.5">{item.competency}</td>
                <td className="px-3 py-2.5">{item.target_level}</td>
                <td className="px-3 py-2.5">{item.source}</td>
                <td className="px-3 py-2.5">{item.approved_at ? new Date(item.approved_at).toLocaleString() : "—"}</td>
                <td className="px-3 py-2.5">
                  <Badge variant="secondary">{item.status}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
