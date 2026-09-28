"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api, type CompetencyProfile, type CompetencyResult, type TrainingRecommendation } from "@/lib/api";
import { LevelTrack } from "@/components/LevelTrack";

const DOMAIN_LABEL: Record<string, string> = {
  STAT: "Statistical",
  TECH: "Technical",
  GOV: "Digital governance",
  BEH: "Behavioural",
};

function statusVariant(status: string): "secondary" | "outline" | "destructive" {
  if (status === "Meets Target") return "secondary";
  if (status === "Priority Gap") return "destructive";
  return "outline";
}

export default function CompetenciesPage() {
  const [profile, setProfile] = useState<CompetencyProfile | null>(null);
  const [recommendations, setRecommendations] = useState<TrainingRecommendation[]>([]);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState("");

  useEffect(() => {
    api
      .getCompetencyProfile()
      .then((payload) => {
        setProfile(payload);
        setSelectedId(payload.competencies[0]?.competency_id ?? "");
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Backend unavailable"));
    api
      .getRecommendations()
      .then((payload) => setRecommendations(payload.recommendations))
      .catch(() => setRecommendations([]));
  }, []);

  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!profile) return <p className="text-sm text-muted-foreground">Loading the competency profile…</p>;

  const selected: CompetencyResult | undefined = profile.competencies.find((item) => item.competency_id === selectedId);

  return (
    <div>
      <PageHeader
        kicker="Competency profile"
        title="Competency Profile"
        description={
          profile.assessed
            ? "Green bars are the level you have now. Pale bars are still to reach."
            : "Take the test. Then this page shows your level and any certificate."
        }
      />
      {!profile.assessed ? (
        <Link href="/assessment" className="text-sm font-medium text-primary hover:underline">
          Complete the diagnostic to record levels
        </Link>
      ) : (
        <>
          <p className="mb-4 text-sm text-muted-foreground">Your score is {profile.overall_score_percent}%.</p>
          <h2 className="mb-3 font-heading text-lg font-semibold">Certificates</h2>
          <div className="mb-6 grid gap-3 sm:grid-cols-3">
            {profile.competencies.map((item) => {
              const earned = item.status === "Meets Target";
              return (
                <Card key={item.competency_id} size="sm" className={earned ? "border-secondary" : ""}>
                  <CardHeader>
                    <CardTitle>{earned ? "Certificate" : "Not yet"}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <p className="font-medium">{item.name}</p>
                    <LevelTrack current={item.current_level} target={item.target_level} />
                    <p className="text-muted-foreground">
                      {earned
                        ? `You reached ${item.target_level}.`
                        : `You are ${item.current_level}. Certificate needs ${item.target_level}.`}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {profile.domain_readiness.map((domain) => (
              <Card key={domain.domain} size="sm">
                <CardContent>
                  <p className="text-sm font-medium">{domain.domain}</p>
                  <p className="mt-1 font-heading text-2xl font-semibold tabular-nums">{domain.percent}%</p>
                  <p className="text-xs text-muted-foreground">{DOMAIN_LABEL[domain.domain] ?? domain.domain}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(16rem,0.8fr)]">
            <div className="overflow-x-auto rounded-lg border border-border bg-card">
              <table className="w-full min-w-[40rem] text-left text-sm">
                <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-wide text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Competency</th>
                    <th className="px-3 py-2 font-medium">Domain</th>
                    <th className="px-3 py-2 font-medium">Current</th>
                    <th className="px-3 py-2 font-medium">Target</th>
                    <th className="px-3 py-2 font-medium">Gap</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.competencies.map((item) => (
                    <tr
                      key={item.competency_id}
                      className={`cursor-pointer border-b border-border last:border-0 ${
                        item.competency_id === selected?.competency_id ? "bg-accent/60" : "hover:bg-muted/40"
                      }`}
                      onClick={() => setSelectedId(item.competency_id)}
                    >
                      <td className="px-3 py-2.5 font-medium">{item.name}</td>
                      <td className="px-3 py-2.5">{item.domain}</td>
                      <td className="px-3 py-2.5">{item.current_level}</td>
                      <td className="px-3 py-2.5">{item.target_level}</td>
                      <td className="px-3 py-2.5 tabular-nums">{item.gap}</td>
                      <td className="px-3 py-2.5">
                        <Badge variant={statusVariant(item.status)}>{item.status}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {selected ? (
              <Card>
                <CardHeader>
                  <CardTitle>{selected.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <LevelTrack current={selected.current_level} target={selected.target_level} />
                  <p>You are {selected.current_level}. Goal {selected.target_level}.</p>
                  <p>Score {selected.score_percent}%.</p>
                  <p>Wrong questions: {selected.evidence.incorrect_question_ids.join(", ") || "none"}.</p>
                  {recommendations
                    .filter((item) => item.competency_id === selected.competency_id)
                    .slice(0, 1)
                    .map((item) => (
                      <p key={item.programme_id}>
                        Next course: {item.title}.
                      </p>
                    ))}
                </CardContent>
              </Card>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
