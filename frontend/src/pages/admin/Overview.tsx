import { Database, KeyRound, Layers, Server, Tag } from "lucide-react";
import type { ReactNode } from "react";

import { PageHeader } from "@/components/common/PageHeader";
import { PhaseNotice } from "@/components/common/PhaseNotice";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useHealth } from "@/hooks/useHealth";
import { ApiError } from "@/services/api";

function StatusCard({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription className="flex items-center gap-2">
          {icon}
          {title}
        </CardDescription>
        <CardTitle className="text-xl">{children}</CardTitle>
      </CardHeader>
    </Card>
  );
}

export default function Overview() {
  const { data, error, isPending, isError, refetch, isFetching } = useHealth();

  return (
    <div className="space-y-10">
      <PageHeader
        title="Overview"
        description="System status. Portfolio and chatbot statistics appear here as those modules are built."
      />

      {isPending && <p className="text-sm text-muted-foreground">Checking the backend…</p>}

      {isError && (
        <Card className="border-destructive/40">
          <CardHeader>
            <CardTitle className="text-destructive">Backend unavailable</CardTitle>
            <CardDescription>
              {error instanceof ApiError ? error.message : "The status check failed."}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm">
            <p className="mb-3">
              Start it with <code className="rounded bg-muted px-1.5 py-0.5">uvicorn app.main:app --reload</code>{" "}
              from the <code className="rounded bg-muted px-1.5 py-0.5">backend</code> folder.
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
              {isFetching ? "Checking…" : "Check again"}
            </Button>
          </CardContent>
        </Card>
      )}

      {data && (
        <section aria-label="System status" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatusCard icon={<Server className="size-4" />} title="API">
            <span className="flex items-center gap-2">
              {data.app}
              <Badge variant={data.status === "ok" ? "success" : "citation"}>
                {data.status === "ok" ? "Healthy" : "Degraded"}
              </Badge>
            </span>
          </StatusCard>

          <StatusCard icon={<Database className="size-4" />} title="Database">
            <span className="flex items-center gap-2">
              {data.database.status === "up" ? `${data.database.latency_ms} ms` : "Unreachable"}
              <Badge variant={data.database.status === "up" ? "success" : "destructive"}>
                {data.database.status === "up" ? "Connected" : "Down"}
              </Badge>
            </span>
          </StatusCard>

          <StatusCard icon={<KeyRound className="size-4" />} title={`LLM provider: ${data.llm_provider}`}>
            <span className="flex items-center gap-2">
              {data.llm_configured ? "API key set" : "No API key"}
              <Badge variant={data.llm_configured ? "success" : "outline"}>
                {data.llm_configured ? "Ready" : "Needed from phase 7"}
              </Badge>
            </span>
          </StatusCard>

          <StatusCard icon={<Layers className="size-4" />} title="Vector store">
            {data.vector_store}
          </StatusCard>

          <StatusCard icon={<Tag className="size-4" />} title="Version">
            v{data.version}
          </StatusCard>

          <StatusCard icon={<Server className="size-4" />} title="Environment">
            {data.environment}
          </StatusCard>
        </section>
      )}

      <section aria-labelledby="stats-heading" className="space-y-3">
        <h2 id="stats-heading" className="text-xl font-semibold">
          Portfolio and chatbot statistics
        </h2>
        <PhaseNotice
          phase={11}
          className="max-w-2xl"
          features={[
            "Totals for projects, skills, certificates and documents",
            "Chatbot query count and latest RAG evaluation score",
            "Charts for skills, projects, retrieval performance and query statistics",
            "Recent activity",
          ]}
        />
      </section>
    </div>
  );
}
