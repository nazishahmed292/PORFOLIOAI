import { useQuery } from "@tanstack/react-query";

import { getHealth } from "@/services/health";

/** Polls the backend health endpoint every 30 seconds. */
export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
    retry: false,
  });
}
