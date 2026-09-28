"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LevelTrack, ReadinessChart } from "@/components/LevelTrack";
import { PageHeader } from "@/components/Sidebar";
import { useEffect, useState } from "react";
import { api, type CompetencyProfile, type RecommendationResponse } from "@/lib/api";

const DOMAIN_LABEL: Record<string, string> = {
  STAT: "Statistical",
  TECH: "Technical",
  GOV: "Digital governance",
  BEH: "Behavioural",
};

export default function DashboardPage() {
  const [profile, setProfile] = useState<CompetencyProfile | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [person, setPerson] = useState("");
  const [finishedCount, setFinishedCount] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getCompetencyProfile()
      .then(setProfile)
      .catch(() => setError("Unable to load competency results. Please check the backend and try again."));
    api
      .getRecommendations()
      .then(setRecommendations)
      .catch(() => setError("Unable to load competency results. Please check the backend and try again."));
    api
      .getMe()
      .then((me) => {
        const role = [me.designation, me.organisation].filter(Boolean).join(", ");
        setPerson(role ? `${me.name}, ${role}` : me.name || "");
      })
      .catch(() => setPerson(""));
    api
      .getCourseProgress()
      .then((payload) => setFinishedCount(payload.courses.filter((item) => item.passed).length))
      .catch(() => setFinishedCount(null));
  }, []);

  const assessed = Boolean(profile?.assessed);
  const metrics = [
    { label: "Your score", value: assessed ? `${profile?.overall_score_percent}%` : "—" },
    { label: "Skills checked", value: assessed ? String(profile?.competencies_assessed ?? 0) : "—" },
    { label: "Big gaps", value: assessed ? String(profile?.priority_gap_count ?? 0) : "—" },
    { label: "Courses finished", value: finishedCount === null ? "—" : String(finishedCount) },
  ];
  const gaps = (profile?.competencies ?? [])
    .filter((item) => item.gap > 0)
    .sort((a, b) => Number(a.status !== "Priority Gap") - Number(b.status !== "Priority Gap") || b.gap - a.gap);
  const firstId = recommendations?.recommendations[0]?.programme_id;

  return (
    <div>
      <PageHeader
        kicker="STAT-Learn"
        title="Competency Intelligence Dashboard"
        description={
          person
            ? assessed
              ? `${person}. This page shows your score, what to improve, and the next course.`
              : `${person}. Take the test to see your score.`
            : "Sign in to see the score saved for your account."
        }
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      {!assessed && !error ? (
        <p className="mb-4 text-sm">
          <Link href="/assessment" className="font-medium text-primary hover:underline">
            Start the diagnostic assessment
          </Link>
        </p>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label} size="sm">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground">{metric.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-heading text-3xl font-semibold tabular-nums text-foreground">{metric.value}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="mt-8">
        <h2 className="font-heading text-lg font-semibold">How strong you are</h2>
        <div className="mt-3 rounded-lg border border-border bg-card p-4">
          <ReadinessChart
            items={(profile?.domain_readiness ?? []).map((domain) => ({
              label: DOMAIN_LABEL[domain.domain] ?? domain.domain,
              percent: domain.percent,
            }))}
          />
          {!assessed ? <p className="mt-3 text-sm text-muted-foreground">Take the test to fill this chart.</p> : null}
        </div>
      </section>

      <section className="mt-8">
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-heading text-lg font-semibold">Competency gaps</h2>
          <Link href="/gaps" className="text-sm font-medium text-primary hover:underline">
            View all gaps
          </Link>
        </div>
        <div className="mt-3 overflow-hidden rounded-lg border border-border bg-card">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-2 font-medium">Competency</th>
                <th className="px-4 py-2 font-medium">Level change</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {gaps.map((gap) => (
                <tr key={gap.competency_id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3 font-medium">{gap.name}</td>
                  <td className="px-4 py-3">
                    <LevelTrack current={gap.current_level} target={gap.target_level} />
                    <p className="mt-1 text-xs text-muted-foreground">
                      {gap.current_level} now, goal {gap.target_level}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={gap.status === "Priority Gap" ? "destructive" : "outline"}>{gap.status}</Badge>
                  </td>
                </tr>
              ))}
              {assessed && gaps.length === 0 ? (
                <tr>
                  <td className="px-4 py-3 text-muted-foreground" colSpan={3}>
                    Your assessed competencies currently meet their target levels.
                  </td>
                </tr>
              ) : null}
              {!assessed ? (
                <tr>
                  <td className="px-4 py-3 text-muted-foreground" colSpan={3}>
                    Complete the diagnostic assessment to generate your competency profile and personalized recommendations.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="font-heading text-lg font-semibold">What to do next</h2>
        <p className="mt-1 text-sm text-muted-foreground">Practice courses for this demo. Not live government sites.</p>
        {recommendations?.message && !recommendations.recommendations.length ? (
          <p className="mt-3 text-sm">
            {recommendations.assessment_attempt_id
              ? "Your assessed competencies currently meet their target levels."
              : "Open a course and answer its questions to finish it."}{" "}
            <Link href="/catalogue" className="font-medium text-primary hover:underline">
              Choose a course
            </Link>
          </p>
        ) : null}
        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          {(recommendations?.recommendations ?? []).slice(0, 4).map((programme) => (
            <Card key={programme.programme_id} size="sm">
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="secondary">{programme.source}</Badge>
                  <span className="text-xs text-muted-foreground">
                    {programme.programme_id === firstId ? "Do this first" : programme.prerequisite_status === "Met" ? "Ready" : "Later"}
                  </span>
                </div>
                <CardTitle className="mt-2">{programme.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>{programme.matched_competencies[0]?.name}</p>
                <LevelTrack current={programme.current_level} target={programme.target_level} />
                <p className="text-muted-foreground">
                  Course is {programme.programme_level}. {programme.prerequisite_status === "Met" ? "You can start it." : "You can still study it."}
                </p>
                <Link href={`/catalogue/${programme.programme_id}`} className="font-medium text-primary hover:underline">
                  Study this course
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <Link href="/pathway" className="text-sm font-medium text-primary hover:underline">
          See the full plan
        </Link>
      </section>
    </div>
  );
}
