"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api, type CompetencyProfile, type TrainingRecommendation } from "@/lib/api";

export default function AssistantPage() {
  const [profile, setProfile] = useState<CompetencyProfile | null>(null);
  const [recommendations, setRecommendations] = useState<TrainingRecommendation[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [activeId, setActiveId] = useState("gaps");

  useEffect(() => {
    Promise.all([api.getCompetencyProfile(), api.getRecommendations()])
      .then(([nextProfile, nextRecommendations]) => {
        setProfile(nextProfile);
        setRecommendations(nextRecommendations.recommendations);
      })
      .catch(() => setError("Unable to load competency results. Please check the backend and try again."))
      .finally(() => setReady(true));
  }, []);

  const gaps = (profile?.competencies ?? []).filter((item) => item.gap > 0);
  const prompts = [
    {
      id: "gaps",
      label: "What are my priority gaps?",
      answer: !profile?.assessed
        ? "Complete the diagnostic assessment to generate your competency profile and personalized recommendations."
        : gaps.length === 0
          ? "Your assessed competencies currently meet their target levels."
          : gaps
              .map((item) => `${item.name}: you are ${item.current_level}, goal ${item.target_level}.`)
              .join("\n"),
    },
    {
      id: "why",
      label: "Why was this training recommended?",
      answer: recommendations[0]
        ? `${recommendations[0].title} is the first course. You are ${recommendations[0].current_level}. The goal is ${recommendations[0].target_level}. ${recommendations[0].prerequisite_status === "Met" ? "You can start it now." : "Finish the earlier course first."}`
        : "No personalized training recommendations are available yet.",
    },
  ];
  const active = prompts.find((item) => item.id === activeId) ?? prompts[0];

  return (
    <div>
      <PageHeader
        kicker="Assistant"
        title="STAT-Learn Assistant"
        description="Short answers from your test. This page does not decide your level."
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      {!ready ? <div className="h-28 animate-pulse rounded-lg border border-border bg-card" /> : null}
      {ready ? (
        <div className="grid gap-4 lg:grid-cols-[16rem_minmax(0,1fr)]">
          <div className="flex flex-col gap-2">
            {prompts.map((prompt) => (
              <button
                key={prompt.id}
                type="button"
                onClick={() => setActiveId(prompt.id)}
                className={`rounded-md border px-3 py-2 text-left text-sm ${
                  prompt.id === active.id ? "border-primary bg-accent" : "border-border bg-card hover:bg-muted"
                }`}
              >
                {prompt.label}
              </button>
            ))}
          </div>
          <Card>
            <CardHeader>
              <CardTitle>{active.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-line text-sm leading-6">{active.answer}</p>
              {!profile?.assessed ? (
                <Link href="/assessment" className="mt-3 inline-block text-sm font-medium text-primary hover:underline">
                  Open the diagnostic
                </Link>
              ) : null}
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
