"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api, type ReviewQuestion } from "@/lib/api";
import { readDemoRole } from "@/demo/role";

export default function McqReviewPage() {
  const [drafts, setDrafts] = useState<ReviewQuestion[]>([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");

  async function load() {
    if (readDemoRole() !== "admin") {
      setError("Training Admin session required");
      return;
    }
    const payload = await api.getReviewQueue();
    setDrafts(payload.drafts);
  }

  useEffect(() => {
    load().catch((err: unknown) => setError(err instanceof Error ? err.message : "Training Admin session required"));
  }, []);

  async function act(id: string, kind: "approve" | "reject") {
    setBusyId(id);
    setError("");
    try {
      if (kind === "approve") await api.approveQuestion(id);
      else await api.rejectQuestion(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review action failed");
    } finally {
      setBusyId("");
    }
  }

  return (
    <div>
      <PageHeader
        kicker="Review"
        title="MCQ Review"
        description="Drafts stay unpublished until a Training Admin approves them. The model cannot approve or score."
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      {drafts.length === 0 && !error ? <p className="text-sm text-muted-foreground">No MCQ drafts are waiting for review.</p> : null}
      <div className="space-y-4">
        {drafts.map((item) => (
          <Card key={item.id}>
            <CardHeader>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={item.origin === "model" ? "secondary" : "outline"}>{item.badge}</Badge>
                <Badge variant="outline">{item.status}</Badge>
                <Badge variant="outline">{item.target_level}</Badge>
              </div>
              <CardTitle className="mt-2">{item.question}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <ul className="list-disc space-y-1 pl-5">
                {item.options.map((option) => (
                  <li key={option} className={option === item.correct_option ? "font-medium text-foreground" : ""}>
                    {option}
                    {option === item.correct_option ? " (correct option)" : ""}
                  </li>
                ))}
              </ul>
              <p>Competency: {item.competency}</p>
              <p>Target level: {item.target_level}</p>
              <p>Why this answer? {item.explanation}</p>
              <p>Source: {item.document_title} · {item.source}</p>
              {item.evidence.map((evidence) => (
                <div key={evidence.chunk_id} className="rounded-md border border-border bg-muted/50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Source evidence · {evidence.chunk_id} · {evidence.section}
                  </p>
                  <p className="mt-1">{evidence.text}</p>
                </div>
              ))}
              <div className="flex gap-2">
                <Button disabled={busyId === item.id} onClick={() => act(item.id, "approve")}>Approve</Button>
                <Button variant="outline" disabled={busyId === item.id} onClick={() => act(item.id, "reject")}>Reject</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
