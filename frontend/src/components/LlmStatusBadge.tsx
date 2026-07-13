import { useQuery } from "@tanstack/react-query";
import { getLlmStatus } from "../api/logicFortressApi";

export function LlmStatusBadge() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["llm-status"],
    queryFn: getLlmStatus,
    staleTime: 30_000,
  });

  if (isLoading) {
    return <span className="border border-fortress-line px-3 py-2">LLM: checking</span>;
  }

  if (isError || !data) {
    return <span className="border border-fortress-red px-3 py-2 text-fortress-red">LLM: offline</span>;
  }

  const mode = data.using_rules_fallback ? "rules fallback" : data.provider;

  return (
    <span className="border border-fortress-line px-3 py-2">
      LLM: {mode} / {data.client_configured ? "client ready" : "rules"}
    </span>
  );
}
