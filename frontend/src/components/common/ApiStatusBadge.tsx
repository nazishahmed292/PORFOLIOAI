import { Badge } from "@/components/ui/badge";
import { useHealth } from "@/hooks/useHealth";

/** Compact "is the backend reachable" indicator. */
export function ApiStatusBadge() {
  const { data, isPending, isError } = useHealth();

  if (isPending) return <Badge variant="outline">Checking API…</Badge>;
  if (isError) return <Badge variant="destructive">API offline</Badge>;
  if (data.status === "degraded") return <Badge variant="citation">API degraded</Badge>;
  return <Badge variant="success">API online</Badge>;
}
