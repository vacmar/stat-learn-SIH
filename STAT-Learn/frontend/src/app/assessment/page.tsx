"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import {
  api,
  type CompetencyAttemptResult,
  type DiagnosticQuestion,
} from "@/lib/api";

const ATTEMPT_KEY = "statlearn:diagnostic-attempt";

export default function AssessmentPage() {
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [purpose, setPurpose] = useState("");
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([]);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [started, setStarted] = useState(false);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState<Record<string, string>>({});
  const [result, setResult] = useState<CompetencyAttemptResult | null>(null);
  const [testTitle, setTestTitle] = useState("Diagnostic");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        api.getMe().then((me) => {
          if (me.designation) setTestTitle(`${me.designation} diagnostic`);
        }).catch(() => undefined);
        const diagnostic = await api.getDiagnostic();
        if (cancelled) return;
        setPurpose(diagnostic.purpose);
        setQuestions(diagnostic.questions);
        const stored = window.sessionStorage.getItem(ATTEMPT_KEY);
        if (!stored) return;
        const attempt = await api.getAttempt(stored);
        if (cancelled) return;
        const known = Object.fromEntries(attempt.answers.map((item) => [item.question_id, item.selected_answer]));
        setAttemptId(attempt.attempt_id);
        setAnswers(known);
        setSaved(known);
        if (attempt.status === "completed") {
          setResult(await api.getAttemptResult(attempt.attempt_id));
        } else {
          setStarted(true);
          const firstOpen = diagnostic.questions.findIndex((item) => !known[item.id]);
          setIndex(firstOpen === -1 ? diagnostic.questions.length - 1 : firstOpen);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Assessment unavailable");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function start() {
    setBusy(true);
    setError("");
    try {
      const attempt = await api.createAttempt();
      window.sessionStorage.setItem(ATTEMPT_KEY, attempt.attempt_id);
      setAttemptId(attempt.attempt_id);
      setStarted(true);
      setIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Attempt creation failed");
    } finally {
      setBusy(false);
    }
  }

  async function persistCurrent() {
    const question = questions[index];
    if (!question || !attemptId) return;
    const selected = answers[question.id];
    if (!selected || saved[question.id] === selected) return;
    try {
      await api.submitAnswer(attemptId, question.id, selected);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Answer submission failed";
      if (!message.toLowerCase().includes("already")) throw err;
    }
    setSaved((current) => ({ ...current, [question.id]: selected }));
  }

  async function goNext() {
    setBusy(true);
    setError("");
    try {
      await persistCurrent();
      setIndex((value) => value + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Answer submission failed");
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    if (!attemptId || busy) return;
    setBusy(true);
    setError("");
    try {
      await persistCurrent();
      const completed = await api.completeAttempt(attemptId);
      setResult(completed);
      setStarted(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Result unavailable");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-8 w-64 animate-pulse rounded-md bg-muted" />
        <div className="h-24 animate-pulse rounded-lg border border-border bg-card" />
      </div>
    );
  }

  if (result) {
    return (
      <div>
        <PageHeader
          kicker={testTitle}
          title="Assessment complete"
          description="Scores, levels, and gaps were calculated by the backend from this attempt. They are not estimated in the browser."
        />
        <Card size="sm" className="mb-6">
          <CardContent>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Overall score</p>
            <p className="mt-1 font-heading text-3xl font-semibold tabular-nums">{result.overall_score_percent}%</p>
          </CardContent>
        </Card>
        <h2 className="mb-3 font-heading text-lg font-semibold">Competency results</h2>
        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Competency</th>
                <th className="px-3 py-2 font-medium">Score</th>
                <th className="px-3 py-2 font-medium">Current</th>
                <th className="px-3 py-2 font-medium">Target</th>
                <th className="px-3 py-2 font-medium">Gap</th>
                <th className="px-3 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.competencies.map((row) => (
                <tr key={row.competency_id} className="border-b border-border last:border-0">
                  <td className="px-3 py-2.5 font-medium">{row.name}</td>
                  <td className="px-3 py-2.5 tabular-nums">{row.score_percent}%</td>
                  <td className="px-3 py-2.5">{row.current_level}</td>
                  <td className="px-3 py-2.5">{row.target_level}</td>
                  <td className="px-3 py-2.5 tabular-nums">{row.gap}</td>
                  <td className="px-3 py-2.5">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Link href="/gaps" className="mt-4 inline-block text-sm font-medium text-primary hover:underline">
          View competency gaps
        </Link>
      </div>
    );
  }

  if (!started) {
    return (
      <div>
        <PageHeader kicker={testTitle} title={testTitle} description={purpose} />
        {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
        <div className="grid gap-3 sm:grid-cols-3">
          <Card size="sm">
            <CardContent>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Domains</p>
              <p className="mt-2 font-medium">STAT</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardContent>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Questions</p>
              <p className="mt-2 font-medium">{questions.length}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardContent>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Scoring</p>
              <p className="mt-2 font-medium">Server answer key</p>
            </CardContent>
          </Card>
        </div>
        <Button className="mt-6 h-10 px-4" disabled={busy || questions.length === 0} onClick={start}>
          {busy ? "Starting…" : "Start Assessment"}
        </Button>
      </div>
    );
  }

  const question = questions[index];
  if (!question) return null;

  return (
    <div>
      <PageHeader
        kicker={testTitle}
        title={`Question ${index + 1} of ${questions.length}`}
        description={purpose}
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge variant="outline">{question.domain}</Badge>
        <Badge variant="outline">{question.competency_name}</Badge>
        <Badge variant="secondary">{question.proficiency_level}</Badge>
      </div>
      <Card>
        <CardContent className="space-y-3">
          <p className="text-base font-medium leading-7">{question.question}</p>
          <div className="space-y-2">
            {question.options.map((option) => {
              const active = answers[question.id] === option;
              return (
                <button
                  key={option}
                  type="button"
                  disabled={busy}
                  onClick={() => setAnswers((current) => ({ ...current, [question.id]: option }))}
                  className={`block w-full rounded-md border px-3 py-2.5 text-left text-sm transition-colors ${
                    active ? "border-primary bg-accent text-foreground" : "border-border bg-card hover:bg-muted"
                  }`}
                >
                  {option}
                </button>
              );
            })}
          </div>
          <div className="flex justify-between pt-2">
            <Button variant="outline" disabled={busy || index === 0} onClick={() => setIndex((value) => value - 1)}>
              Previous
            </Button>
            {index < questions.length - 1 ? (
              <Button disabled={busy || !answers[question.id]} onClick={goNext}>
                {busy ? "Saving…" : "Next"}
              </Button>
            ) : (
              <Button disabled={busy || !answers[question.id]} onClick={finish}>
                {busy ? "Submitting…" : "Submit assessment"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
