"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api, type CompetencyGapList, type CompetencyResult, type TrainingRecommendation } from "@/lib/api";

function GapList({
  items,
  expandedId,
  onToggle,
  attemptLabel,
  recommendations,
}: {
  items: CompetencyResult[];
  expandedId: string | null;
  onToggle: (id: string) => void;
  attemptLabel: string;
  recommendations: TrainingRecommendation[];
}) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">None in this section.</p>;
  }
  return (
    <div className="grid gap-3">
      {items.map((item) => {
        const open = expandedId === item.competency_id;
        return (
          <Card key={item.competency_id} size="sm">
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <CardTitle>{item.name}</CardTitle>
                <Badge variant={item.priority === "High" ? "destructive" : "outline"}>{item.priority} priority</Badge>
              </div>
            </CardHeader>
            <CardContent className="text-sm">
              <p className="text-muted-foreground">
                Current {item.current_level} · Target {item.target_level} · {item.domain}
              </p>
              <button
                type="button"
                className="mt-3 text-sm font-medium text-primary hover:underline"
                onClick={() => onToggle(item.competency_id)}
              >
                {open ? "Hide explanation" : "Why is this a gap?"}
              </button>
              {open ? (
                <div className="mt-3 space-y-1.5 leading-6">
                  <p>Current level: {item.current_level}</p>
                  <p>Target level: {item.target_level}</p>
                  <p>Gap: {item.gap}</p>
                  <p>Assessment score: {item.score_percent}%</p>
                  <p>
                    Evidence: {item.evidence.correct} of {item.evidence.evaluated} relevant questions answered correctly.
                  </p>
                  <p>Incorrect answers: {item.evidence.incorrect_question_ids.join(", ") || "None"}</p>
                  <p>Incorrect areas: {item.evidence.incorrect_topics.join(", ") || "None"}</p>
                  <p>Assessment: Diagnostic Assessment. {attemptLabel}</p>
                  <RecommendedStep items={recommendations.filter((row) => row.competency_id === item.competency_id)} />
                </div>
              ) : null}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function RecommendedStep({ items }: { items: TrainingRecommendation[] }) {
  if (items.length === 0) return null;
  const next = items[0];
  return (
    <div className="mt-2 rounded-md border border-border bg-muted/40 p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Recommended next step</p>
      <p className="font-medium text-foreground">
        {next.title}
      </p>
      <p>{next.prerequisite_status === "Met" ? "You can start this course." : "Finish the earlier course first."}</p>
    </div>
  );
}

export default function GapsPage() {
  const [data, setData] = useState<CompetencyGapList | null>(null);
  const [recommendations, setRecommendations] = useState<TrainingRecommendation[]>([]);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    api
      .getCompetencyGaps()
      .then((payload) => {
        setData(payload);
        const first = payload.gaps.find((item) => item.gap > 0);
        setExpandedId(first?.competency_id ?? null);
      })
      .catch(() => setError("Unable to load competency results. Please check the backend and try again."));
    api
      .getRecommendations()
      .then((payload) => setRecommendations(payload.recommendations))
      .catch(() => setRecommendations([]));
  }, []);

  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!data) {
    return (
      <div className="space-y-3">
        <div className="h-8 w-56 animate-pulse rounded-md bg-muted" />
        <div className="h-28 animate-pulse rounded-lg border border-border bg-card" />
      </div>
    );
  }

  if (!data.attempt_id) {
    return (
      <div>
        <PageHeader
          kicker="Gaps"
          title="My Competency Gaps"
          description="Gaps appear after the diagnostic is submitted. Levels are calculated on the server."
        />
        <Link href="/assessment" className="text-sm font-medium text-primary hover:underline">
          Start the diagnostic assessment
        </Link>
      </div>
    );
  }

  const priority = data.gaps.filter((item) => item.status === "Priority Gap");
  const moderate = data.gaps.filter((item) => item.status === "Moderate Gap");
  const meeting = data.gaps.filter((item) => item.status === "Meets Target");
  const attemptLabel = `Attempt ${data.attempt_id.slice(0, 8)}`;

  return (
    <div>
      <PageHeader
        kicker="Gaps"
        title="My Competency Gaps"
        description="Explanations use the stored answers from the latest completed diagnostic. No language model is involved."
      />
      <section>
        <h2 className="mb-3 font-heading text-lg font-semibold">Priority gaps</h2>
        <GapList items={priority} expandedId={expandedId} onToggle={(id) => setExpandedId((current) => (current === id ? null : id))} attemptLabel={attemptLabel} recommendations={recommendations} />
      </section>
      <section className="mt-8">
        <h2 className="mb-3 font-heading text-lg font-semibold">Moderate gaps</h2>
        <GapList items={moderate} expandedId={expandedId} onToggle={(id) => setExpandedId((current) => (current === id ? null : id))} attemptLabel={attemptLabel} recommendations={recommendations} />
      </section>
      <section className="mt-8">
        <h2 className="mb-3 font-heading text-lg font-semibold">Meeting target</h2>
        <GapList items={meeting} expandedId={expandedId} onToggle={(id) => setExpandedId((current) => (current === id ? null : id))} attemptLabel={attemptLabel} recommendations={recommendations} />
      </section>
    </div>
  );
}
