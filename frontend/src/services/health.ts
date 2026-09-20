import type { HealthResponse } from "@/types/api";

import { api } from "./api";

export const getHealth = () => api.get<HealthResponse>("/health");
