"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { LogoutButton } from "@/components/LogoutButton";
import { api } from "@/lib/api";

type Me = {
  name?: string;
  email?: string;
  posting?: string | null;
  ministry?: string | null;
  state_name?: string | null;
  department?: string | null;
  organisation?: string | null;
  designation?: string | null;
};

export default function AccountPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    api
      .getMe()
      .then((payload) => {
        setMe(payload);
        setSignedIn(true);
      })
      .catch(() => setSignedIn(false));
  }, []);

  const place = me?.posting === "state" ? "State" : me?.posting === "center" ? "Center" : "";

  return (
    <div>
      <PageHeader
        kicker="My account"
        title={signedIn ? me?.name || "Account" : "Not signed in"}
        description="These details were saved when the account was registered."
      />
      {!signedIn ? (
        <p className="text-sm">
          <Link href="/auth/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>{" "}
          to see the saved name, email, and designation.
        </p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Saved registration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Field label="Name" value={me?.name} />
              <Field label="Email" value={me?.email} />
              <Field label="Center / State" value={place} />
              {me?.posting === "state" ? (
                <>
                  <Field label="State" value={me.state_name} />
                  <Field label="Department" value={me.department} />
                </>
              ) : (
                <Field label="Ministry / Department" value={me?.ministry} />
              )}
              <Field label="Organisation" value={me?.organisation} />
              <Field label="Designation" value={me?.designation} />
              <div className="pt-2">
                <LogoutButton />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>What this account is for</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>Take the test.</p>
              <p>See your level and your goal.</p>
              <p>Open the next course.</p>
              <p>A certificate appears when your level matches the goal.</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <p>
      <span className="text-muted-foreground">{label}. </span>
      {value || "Not saved"}
    </p>
  );
}
