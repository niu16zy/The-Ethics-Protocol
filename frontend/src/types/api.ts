export interface UserCreate {
  username: string;
  display_name: string;
  email?: string | null;
  external_id?: string | null;
}

export interface UserRead {
  id: number;
  username: string;
  display_name: string;
  email?: string | null;
  external_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SessionCreate {
  user_id: number;
  current_level?: number;
}

export interface SessionRead {
  id: number;
  user_id: number;
  current_level: number;
  fortress_meter: number;
  session_status: string;
  started_at: string;
  ended_at?: string | null;
  updated_at: string;
}

export interface DebateTurnCreate {
  player_input: string;
}

export type Verdict = "strong" | "partial" | "weak" | "unsupported" | "off_topic";

export interface EvidenceRef {
  document_id: number;
  course?: string | null;
  lesson?: string | null;
  topic?: string | null;
  seq_order?: number | null;
  excerpt: string;
  score?: number | null;
}

export interface EvaluatorResult {
  match_score: number;
  score_delta: number;
  verdict: Verdict;
  identified_principles: string[];
  misconceptions_addressed: string[];
  missing_points: string[];
  evidence_refs: EvidenceRef[];
  reasoning_summary: string;
  persona_instruction: string;
  confidence: number;
}

export type RuntimeSource = "llm" | "rules" | "fallback" | string;

export interface DebateTurnResponse {
  session_id: number;
  turn_index: number;
  player_input: string;
  retrieved_refs: EvidenceRef[];
  evaluator: EvaluatorResult;
  npc_response: string;
  meter_before: number;
  meter_after: number;
  score_delta: number;
  evaluator_source?: RuntimeSource | null;
  persona_source?: RuntimeSource | null;
}

export type DebateTurnStreamEvent =
  | {
      event: "phase";
      phase: "retrieving" | "evaluating" | "persona";
    }
  | {
      event: "evaluator_complete";
      verdict: Verdict;
      confidence: number;
      meter_before: number;
      meter_after: number;
      score_delta: number;
      evaluator_source?: RuntimeSource | null;
    }
  | {
      event: "persona_delta";
      text: string;
    }
  | {
      event: "complete";
      turn: DebateTurnResponse;
    }
  | {
      event: "error";
      message: string;
    };

export interface LlmStatus {
  provider: string;
  model: string;
  timeout_seconds: number;
  max_attempts: number;
  max_output_tokens: number;
  api_key_configured: boolean;
  client_configured: boolean;
  using_rules_fallback: boolean;
}

export interface ApiErrorBody {
  detail?: string;
}
