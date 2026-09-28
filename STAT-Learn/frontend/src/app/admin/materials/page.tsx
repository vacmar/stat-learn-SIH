"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api, type AdminDocument } from "@/lib/api";
import { readDemoRole } from "@/demo/role";

export default function MaterialsPage() {
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (readDemoRole() !== "admin") {
      setError("Training Admin session required");
      return;
    }
    api
      .getAdminMaterials()
      .then((payload) => setDocuments(payload.documents))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Training Admin session required"));
  }, []);

  return (
    <div>
      <PageHeader
        kicker="Materials"
        title="Learning Materials"
        description="Demo sources only. These notes are not official government publications."
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <div className="space-y-3">
        {documents.map((document) => (
          <Card key={document.id}>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CardTitle>{document.title}</CardTitle>
                <Badge variant="outline">{document.status}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-1 text-sm text-muted-foreground">
              <p>Source: {document.source}</p>
              <p>{document.summary}</p>
              <p>Sections: {(document.sections ?? []).join(", ") || "Not listed"}</p>
              <p>Chunks: {document.chunks}</p>
              <p>Added: {document.added}</p>
              <Link href="/admin/mcq-generator" className="inline-block pt-2 font-medium text-primary hover:underline">
                Generate MCQs
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
