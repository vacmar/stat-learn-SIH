"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api, type PathwayJourney } from "@/lib/api";

export default function PathwayPage() {
  const [journeys, setJourneys] = useState<PathwayJourney[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getPathway()
      .then((payload) => {
        setJourneys(payload.journeys);
        setMessage(payload.message);
      })
      .catch(() => setError("Unable to load competency results. Please check the backend and try again."));
  }, []);

  return (
    <div>
      <PageHeader
        kicker="Pathway"
        title="Competency Pathway"
        description="Green is where you are. The course under it is what to do next."
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {message ? (
        <p className="text-sm">
          {message}{" "}
          <Link href="/assessment" className="font-medium text-primary hover:underline">
            Open the diagnostic
          </Link>
        </p>
      ) : null}
      <div className="mt-6 space-y-4">
        {journeys.map((journey) => (
          <Card key={journey.competency_id}>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CardTitle>
                  {journey.name} · {journey.current_level} → {journey.target_level}
                </CardTitle>
                <Badge variant={journey.status === "Priority Gap" ? "destructive" : "outline"}>{journey.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <ol className="space-y-3 border-l border-border pl-4">
                {journey.steps.map((step, index) => (
                  <li key={`${step.state}-${step.label}-${index}`}>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">{step.state}</p>
                    <p className="mt-1 text-sm font-medium">{step.label}</p>
                    {step.detail ? <p className="text-sm text-muted-foreground">{step.detail}</p> : null}
                    {step.source ? <p className="text-xs text-muted-foreground">Synthetic {step.source}</p> : null}
                    {step.prerequisite_status ? (
                      <p className="text-xs text-muted-foreground">Prerequisite {step.prerequisite_status}</p>
                    ) : null}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
