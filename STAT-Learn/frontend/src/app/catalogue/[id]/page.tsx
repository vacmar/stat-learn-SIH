"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api } from "@/lib/api";

type Course = Awaited<ReturnType<typeof api.getCourse>>;
type Review = { question_id: string; correct: boolean };

export default function CoursePage() {
  const params = useParams<{ id: string }>();
  const programmeId = params.id;
  const [course, setCourse] = useState<Course | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{
    score_percent: number;
    correct_count: number;
    status: string;
    passed_this_attempt: boolean;
    reviews: Review[];
  } | null>(null);

  useEffect(() => {
    if (!programmeId) return;
    api
      .getCourse(programmeId)
      .then(setCourse)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Course unavailable"));
  }, [programmeId]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!course) return;
    setBusy(true);
    setError("");
    try {
      const saved = await api.submitCourse(
        course.id,
        course.questions.map((question) => ({ question_id: question.id, selected_answer: answers[question.id] })),
      );
      setResult(saved);
      setCourse({
        ...course,
        progress: { ...course.progress, status: saved.status, passed: saved.status === "Completed" },
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not save the course");
    } finally {
      setBusy(false);
    }
  }

  if (error && !course) return <p className="text-sm text-destructive">{error}</p>;
  if (!course) return <p className="text-sm text-muted-foreground">Loading the course…</p>;

  const finished = course.progress.passed || result?.status === "Completed";
  const reviewById = new Map((result?.reviews ?? []).map((item) => [item.question_id, item.correct]));

  return (
    <div>
      <PageHeader
        kicker={course.source}
        title={course.title}
        description={`${course.level} · ${course.duration}. Read the short notes, then answer to finish the course.`}
      />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge variant={finished ? "secondary" : "outline"}>{finished ? "Completed" : course.progress.status}</Badge>
        <span className="text-sm text-muted-foreground">{course.pass_rule}</span>
        {course.external_url ? (
          <a href={course.external_url} target="_blank" rel="noreferrer" className="text-sm font-medium text-primary hover:underline">
            Open on iGOT
          </a>
        ) : null}
      </div>
      <Card className="mb-6">
        <CardContent className="space-y-2 text-sm leading-6">
          {course.lessons.map((lesson) => (
            <p key={lesson}>{lesson}</p>
          ))}
        </CardContent>
      </Card>
      <form onSubmit={submit} className="space-y-3">
        {course.questions.map((question, index) => {
          const marked = reviewById.get(question.id);
          return (
            <Card key={question.id}>
              <CardContent className="space-y-2">
                <p className="text-sm font-medium">
                  {index + 1}. {question.prompt}
                </p>
                {question.options.map((option) => {
                  const active = answers[question.id] === option;
                  return (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setAnswers((current) => ({ ...current, [question.id]: option }))}
                      className={`block w-full rounded-md border px-3 py-2.5 text-left text-sm ${
                        active ? "border-primary bg-accent text-foreground" : "border-border bg-card hover:bg-muted"
                      }`}
                    >
                      {option}
                    </button>
                  );
                })}
                {marked === true ? <p className="text-sm text-secondary">Correct</p> : null}
                {marked === false ? <p className="text-sm text-destructive">Try this one again</p> : null}
              </CardContent>
            </Card>
          );
        })}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {result ? (
          <p className="text-sm">
            {result.correct_count} of {course.questions.length} correct. {result.status}.
          </p>
        ) : null}
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={busy || course.questions.some((question) => !answers[question.id])}>
            {busy ? "Saving…" : finished ? "Answer again" : "Finish course"}
          </Button>
          <Link href="/catalogue" className="text-sm font-medium text-primary hover:underline">
            Back to courses
          </Link>
        </div>
      </form>
    </div>
  );
}
