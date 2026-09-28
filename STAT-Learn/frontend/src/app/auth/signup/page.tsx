"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { AuthShell, authFieldClass, authLabelClass } from "@/components/AuthShell";

type Option = { kind: string; posting: string; parent_label: string | null; label: string };
type Posting = "center" | "state";

function labels(options: Option[], kind: string, posting: Posting, parent?: string) {
  const needsParent = kind === "department" || kind === "organisation";
  if (needsParent && !parent) return [];
  const seen = new Set<string>();
  const result: string[] = [];
  for (const item of options) {
    if (item.kind !== kind || (item.posting !== posting && item.posting !== "both")) continue;
    if (needsParent && item.parent_label !== parent) continue;
    if (seen.has(item.label)) continue;
    seen.add(item.label);
    result.push(item.label);
  }
  return result;
}

export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [options, setOptions] = useState<Option[]>([]);
  const [posting, setPosting] = useState<Posting>("center");
  const [ministry, setMinistry] = useState("");
  const [stateName, setStateName] = useState("");
  const [department, setDepartment] = useState("");
  const [organisation, setOrganisation] = useState("");
  const [designation, setDesignation] = useState("");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    api
      .getRegistrationForm()
      .then((form) => {
        setOptions(form.options);
        const saved = form.profile;
        if (!saved) return;
        setPosting(saved.posting === "state" ? "state" : "center");
        setMinistry(saved.ministry || "");
        setStateName(saved.state_name || "");
        setDepartment(saved.department || "");
        setOrganisation(saved.organisation || "");
        setDesignation(saved.designation || "");
        setEmail(saved.email || "");
        setName(saved.name || "");
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Unable to load saved registration"))
      .finally(() => setReady(true));
  }, []);

  const ministries = labels(options, "ministry", "center");
  const states = labels(options, "state", "state");
  const departments = labels(options, "department", "state", stateName);
  const organisations =
    posting === "center" ? labels(options, "organisation", "center", ministry) : labels(options, "organisation", "state", stateName);
  const designations = labels(options, "designation", posting);

  function clearPrepared() {
    setMinistry("");
    setStateName("");
    setDepartment("");
    setOrganisation("");
    setDesignation("");
    setEmail("");
    setName("");
    setPassword("");
    setConfirmPassword("");
    setError("");
    setStep(1);
  }

  function goNext(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    if (posting === "center" && (!ministry || !organisation || !designation)) {
      setError("Choose a ministry, organisation, and designation.");
      return;
    }
    if (posting === "state" && (!stateName || !department || !organisation || !designation)) {
      setError("Choose a state, department, organisation, and designation.");
      return;
    }
    setStep(2);
  }

  async function handleSignup(event: React.FormEvent) {
    event.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.signup({
        name,
        email,
        password,
        posting,
        ministry: posting === "center" ? ministry : null,
        state_name: posting === "state" ? stateName : null,
        department: posting === "state" ? department : null,
        organisation,
        designation,
      });
      router.push("/dashboard");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to sign up";
      if (message === "Email already registered") {
        try {
          await api.login({ email, password });
          router.push("/dashboard");
          return;
        } catch {
          setError("This email is already saved. The password did not match, so log in with the password used before.");
          return;
        }
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell mode="signup">
      <h2 className="font-heading text-2xl font-semibold text-foreground">Register</h2>
      <p className="mt-1.5 mb-4 text-sm text-muted-foreground">
        {ready ? "Saved details are filled from your account. They appear again after you sign in." : "Loading saved registration…"}
      </p>
      <ol className="mb-6 flex items-center gap-3 text-xs font-medium text-muted-foreground">
        <li className={step === 1 ? "text-primary" : ""}>1 · Organisation</li>
        <li className="h-px w-10 bg-border" />
        <li className={step === 2 ? "text-primary" : ""}>2 · Name and password</li>
      </ol>
      {error && (
        <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
          {error}
        </div>
      )}
      {step === 1 ? (
        <form onSubmit={goNext} className="space-y-4">
          <fieldset>
            <legend className={authLabelClass}>Center / State</legend>
            <div className="flex gap-4 text-sm">
              <label className="flex items-center gap-2">
                <input type="radio" name="posting" checked={posting === "center"} onChange={() => setPosting("center")} />
                Center
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="posting" checked={posting === "state"} onChange={() => setPosting("state")} />
                State
              </label>
            </div>
          </fieldset>
          {posting === "center" ? (
            <SelectField label="Ministry / Department" value={ministry} options={ministries} onChange={setMinistry} />
          ) : (
            <>
              <SelectField label="State" value={stateName} options={states} onChange={setStateName} />
              <SelectField label="Department" value={department} options={departments} onChange={setDepartment} />
            </>
          )}
          <SelectField label="Organisation" value={organisation} options={organisations} onChange={setOrganisation} />
          <SelectField label="Designation" value={designation} options={designations} onChange={setDesignation} />
          <div>
            <label className={authLabelClass}>Email</label>
            <input type="email" required autoComplete="email" className={authFieldClass} value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <div className="flex items-center justify-between gap-3">
            <button type="button" className="text-sm text-primary hover:underline" onClick={clearPrepared}>
              Register someone else
            </button>
            <Button type="submit">Next</Button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleSignup} className="space-y-4">
          <div>
            <label className={authLabelClass}>Name</label>
            <input type="text" required autoComplete="name" className={authFieldClass} value={name} onChange={(event) => setName(event.target.value)} />
          </div>
          <div>
            <label className={authLabelClass}>Password</label>
            <input type="password" required autoComplete="new-password" className={authFieldClass} value={password} onChange={(event) => setPassword(event.target.value)} />
          </div>
          <div>
            <label className={authLabelClass}>Confirm password</label>
            <input type="password" required autoComplete="new-password" className={authFieldClass} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} />
          </div>
          <div className="flex items-center justify-between gap-3">
            <button type="button" className="text-sm text-primary hover:underline" onClick={() => setStep(1)}>
              Back
            </button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving…" : "Register"}
            </Button>
          </div>
        </form>
      )}
    </AuthShell>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  const choices = value && !options.includes(value) ? [value, ...options] : options;
  return (
    <div>
      <label className={authLabelClass}>{label}</label>
      <select required className={authFieldClass} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select</option>
        {choices.map((item, index) => (
          <option key={`${item}-${index}`} value={item}>
            {item}
          </option>
        ))}
      </select>
    </div>
  );
}
