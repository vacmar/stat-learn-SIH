"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api, type CatalogueProgramme, type TrainingRecommendation } from "@/lib/api";

export default function CataloguePage() {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [domain, setDomain] = useState("all");
  const [duration, setDuration] = useState("all");
  const [programmes, setProgrammes] = useState<CatalogueProgramme[]>([]);
  const [note, setNote] = useState("");
  const [recommendations, setRecommendations] = useState<TrainingRecommendation[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [learnerName, setLearnerName] = useState("");
  const [finished, setFinished] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getCatalogue()
      .then((payload) => {
        setProgrammes(payload.programmes);
        setNote(payload.note);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Backend unavailable"));
    api.getMe().then((me) => setLearnerName(me.name || "")).catch(() => setLearnerName(""));
    api
      .getCourseProgress()
      .then((payload) => {
        const done: Record<string, boolean> = {};
        payload.courses.forEach((item) => {
          if (item.passed) done[item.programme_id] = true;
        });
        setFinished(done);
      })
      .catch(() => setFinished({}));
    api
      .getRecommendations()
      .then((payload) => {
        setRecommendations(payload.recommendations);
        setMessage(payload.message);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Backend unavailable"));
  }, []);

  const results = useMemo(() => {
    return programmes.filter((programme) => {
      const names = programme.competencies.map((item) => item.name).join(" ");
      const haystack = `${programme.title} ${names}`.toLowerCase();
      if (query && !haystack.includes(query.trim().toLowerCase())) return false;
      if (source !== "all" && programme.source !== source) return false;
      if (domain !== "all" && !programme.level.toLowerCase().includes(domain.toLowerCase())) return false;
      if (duration === "short" && programme.duration_hours > 6) return false;
      if (duration === "medium" && (programme.duration_hours < 7 || programme.duration_hours > 10)) return false;
      if (duration === "long" && programme.duration_hours < 11) return false;
      return true;
    });
  }, [programmes, query, source, domain, duration]);

  return (
    <div>
      <PageHeader
        kicker="Catalogue"
        title="Training Catalogue"
        description={note || "Courses from the public iGOT Karmayogi catalogue."}
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}

      <section>
        <h2 className="font-heading text-lg font-semibold">Recommended for {learnerName || "you"}</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Personalized from the latest diagnostic gaps. The list below is the public iGOT course list.
        </p>
        {message ? (
          <p className="mt-3 text-sm">
            {message}{" "}
            <Link href="/assessment" className="font-medium text-primary hover:underline">
              Open the diagnostic
            </Link>
          </p>
        ) : null}
        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          {recommendations.map((programme) => (
            <Card key={programme.programme_id} size="sm">
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="secondary">{programme.source}</Badge>
                  <span className="text-xs text-muted-foreground">Synthetic · rank {programme.rank}</span>
                </div>
                <CardTitle className="mt-2">{programme.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm leading-6">
                <p>{programme.recommendation_reason}</p>
                <p className="text-muted-foreground">
                  {programme.current_level} → {programme.target_level}. Prerequisite {programme.prerequisite_status}.
                </p>
                <Link href={`/catalogue/${programme.programme_id}`} className="font-medium text-primary hover:underline">
                  {finished[programme.programme_id] ? "Completed · open course" : "Study this course"}
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="font-heading text-lg font-semibold">All training programmes</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <label className="text-xs text-muted-foreground">
            Search
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="mt-1 w-full rounded-md border border-input bg-card px-2 py-1.5 text-sm text-foreground"
              placeholder="Programme or competency"
            />
          </label>
          <label className="text-xs text-muted-foreground">
            Source
            <select value={source} onChange={(event) => setSource(event.target.value)} className="mt-1 w-full rounded-md border border-input bg-card px-2 py-1.5 text-sm">
              <option value="all">All sources</option>
              <option>iGOT</option>
            </select>
          </label>
          <label className="text-xs text-muted-foreground">
            Language
            <select value={domain} onChange={(event) => setDomain(event.target.value)} className="mt-1 w-full rounded-md border border-input bg-card px-2 py-1.5 text-sm">
              <option value="all">All languages</option>
              <option>English</option>
              <option>Hindi</option>
            </select>
          </label>
          <label className="text-xs text-muted-foreground">
            Duration
            <select value={duration} onChange={(event) => setDuration(event.target.value)} className="mt-1 w-full rounded-md border border-input bg-card px-2 py-1.5 text-sm">
              <option value="all">Any duration</option>
              <option value="short">Up to 6 hours</option>
              <option value="medium">7–10 hours</option>
              <option value="long">11 hours or more</option>
            </select>
          </label>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">{results.length} programmes</p>
        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          {results.map((programme) => (
            <Card key={programme.id} size="sm">
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="outline">{programme.source}</Badge>
                  <span className="text-xs text-muted-foreground">{programme.duration}</span>
                </div>
                <CardTitle className="mt-2">{programme.title}</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-1 text-sm text-muted-foreground">
                <p>{programme.format}</p>
                <p>{(programme.keywords || []).slice(0, 3).join(" · ")}</p>
                <Link href={`/catalogue/${programme.id}`} className="mt-1 font-medium text-primary hover:underline">
                  {finished[programme.id] ? "Completed · open course" : "Study this course"}
                </Link>
                {programme.external_url ? (
                  <a href={programme.external_url} target="_blank" rel="noreferrer" className="font-medium text-primary hover:underline">
                    Open on iGOT
                  </a>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
