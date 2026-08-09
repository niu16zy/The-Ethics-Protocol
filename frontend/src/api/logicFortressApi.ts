import { API_BASE_URL, ApiError, apiRequest } from "./client";
import type {
  DebateTurnCreate,
  DebateTurnResponse,
  DebateTurnStreamEvent,
  EvidenceRef,
  LlmStatus,
  SessionCreate,
  SessionRead,
  UserCreate,
  UserRead,
} from "../types/api";

interface DebateTurnStreamHandlers {
  onEvent: (event: DebateTurnStreamEvent) => void;
  signal?: AbortSignal;
}

export function createUser(payload: UserCreate): Promise<UserRead> {
  return apiRequest<UserRead>("/api/users", {
    method: "POST",
    body: payload,
  });
}

export function getUser(userId: number): Promise<UserRead> {
  return apiRequest<UserRead>(`/api/users/${userId}`);
}

export function createSession(payload: SessionCreate): Promise<SessionRead> {
  return apiRequest<SessionRead>("/api/sessions", {
    method: "POST",
    body: payload,
  });
}

export function getSession(sessionId: number): Promise<SessionRead> {
  return apiRequest<SessionRead>(`/api/sessions/${sessionId}`);
}

export function submitDebateTurn(
  sessionId: number,
  payload: DebateTurnCreate,
): Promise<DebateTurnResponse> {
  return apiRequest<DebateTurnResponse>(`/api/sessions/${sessionId}/turns`, {
    method: "POST",
    body: payload,
    timeoutMs: 60_000,
  });
}

export async function submitDebateTurnStream(
  sessionId: number,
  payload: DebateTurnCreate,
  handlers: DebateTurnStreamHandlers,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/turns/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal: handlers.signal,
  });

  if (!response.ok) {
    throw new ApiError(response.status, `The Ethics Protocol API returned ${response.status}`);
  }

  if (!response.body) {
    throw new ApiError(0, "Streaming response did not include a readable body.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) {
        continue;
      }

      const event = JSON.parse(trimmed) as DebateTurnStreamEvent;
      handlers.onEvent(event);
      if (event.event === "error") {
        throw new ApiError(0, event.message);
      }
    }
  }

  const remaining = buffer.trim();
  if (remaining) {
    const event = JSON.parse(remaining) as DebateTurnStreamEvent;
    handlers.onEvent(event);
    if (event.event === "error") {
      throw new ApiError(0, event.message);
    }
  }
}

export function searchEvidence(q: string, topK = 5): Promise<EvidenceRef[]> {
  return apiRequest<EvidenceRef[]>("/api/search", {
    query: {
      q,
      top_k: topK,
    },
  });
}

export function getLlmStatus(): Promise<LlmStatus> {
  return apiRequest<LlmStatus>("/api/llm/status");
}
