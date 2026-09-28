"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api } from "@/lib/api";
import { readDemoRole } from "@/demo/role";

export default function McqGeneratorPage() {
  const [level, setLevel] = useState("L2");
  const [count, setCount] = useState(1);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run(kind: "model" | "demo") {
    if (readDemoRole() !== "admin") {
      setError("Training Admin session required");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    const body = {
      document_id: "mat-sampling-note",
      competency_id: "stat-survey-methodology",
      target_level: level,
      count,
    };
    try {
      const result = kind === "model" ? await api.generateModelDraft(body) : await api.generateDemoDraft(body);
      const label = result.drafts[0]?.badge ?? "Draft";
      setMessage(`${result.drafts.length} ${label} created. AI-generated drafts require human review before publication.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI generation unavailable. No draft was created.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        kicker="Generator"
        title="MCQ Generator"
        description="AI-generated drafts require human review before publication. A demo draft is labeled separately and is not described as model output."
      />
      <Card>
        <CardHeader>
          <CardTitle>Draft request</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <label className="text-sm md:col-span-2">
            Source
            <input readOnly value="Synthetic sampling note · Demo source" className="mt-1 w-full rounded-md border border-input bg-muted px-3 py-2" />
          </label>
          <label className="text-sm">
            Competency
            <input readOnly value="Survey Methodology" className="mt-1 w-full rounded-md border border-input bg-muted px-3 py-2" />
          </label>
          <label className="text-sm">
            Target level
            <select value={level} onChange={(event) => setLevel(event.target.value)} className="mt-1 w-full rounded-md border border-input bg-card px-3 py-2">
              {["L1", "L2", "L3", "L4", "L5"].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Questions
            <input
              type="number"
              min={1}
              max={3}
              value={count}
              onChange={(event) => setCount(Number(event.target.value))}
              className="mt-1 w-full rounded-md border border-input bg-card px-3 py-2"
            />
          </label>
          <div className="flex flex-wrap gap-2 md:col-span-2">
            <Button disabled={busy} onClick={() => run("model")}>
              Generate MCQs
            </Button>
            <Button variant="outline" disabled={busy} onClick={() => run("demo")}>
              Load demo draft
            </Button>
          </div>
          {message ? <p className="text-sm md:col-span-2">{message}</p> : null}
          {error ? <p className="text-sm text-destructive md:col-span-2">{error}</p> : null}
          <Link href="/admin/mcq-review" className="text-sm font-medium text-primary hover:underline md:col-span-2">
            Review generated questions
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
