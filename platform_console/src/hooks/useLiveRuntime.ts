import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { runtimeApi } from "../services/runtimeApi";
import { useRuntimeSocket } from "./useRuntimeSocket";

const REFETCH_MS = 2000;

export function useLiveRuntime() {
  const socket = useRuntimeSocket(true);
  const qc = useQueryClient();

  useEffect(() => {
    if (!socket.lastMessage) return;
    const t = socket.lastMessage.type;
    if (
      t === "status" ||
      t === "event" ||
      t === "agent.status" ||
      t === "agent.task" ||
      t === "provider.connected" ||
      t === "provider.disconnected" ||
      t === "provider.health" ||
      t === "provider.execution" ||
      t === "provider.error" ||
      String(t).startsWith("workflow.")
    ) {
      void qc.invalidateQueries({ queryKey: ["runtime"] });
    }
  }, [socket.lastMessage, qc]);

  const health = useQuery({
    queryKey: ["runtime", "health"],
    queryFn: runtimeApi.health,
    refetchInterval: REFETCH_MS,
  });
  const status = useQuery({
    queryKey: ["runtime", "status"],
    queryFn: runtimeApi.status,
    refetchInterval: REFETCH_MS,
  });
  const metrics = useQuery({
    queryKey: ["runtime", "metrics"],
    queryFn: runtimeApi.metrics,
    refetchInterval: REFETCH_MS,
  });
  const kernel = useQuery({
    queryKey: ["runtime", "kernel"],
    queryFn: runtimeApi.kernel,
    refetchInterval: REFETCH_MS,
  });
  const services = useQuery({
    queryKey: ["runtime", "services"],
    queryFn: async () => (await runtimeApi.services()).services,
    refetchInterval: REFETCH_MS,
  });
  const workflows = useQuery({
    queryKey: ["runtime", "workflows"],
    queryFn: runtimeApi.workflows,
    refetchInterval: REFETCH_MS,
  });
  const events = useQuery({
    queryKey: ["runtime", "events"],
    queryFn: async () => (await runtimeApi.events()).events,
    refetchInterval: REFETCH_MS,
  });
  const logs = useQuery({
    queryKey: ["runtime", "logs"],
    queryFn: async () => (await runtimeApi.logs()).logs,
    refetchInterval: REFETCH_MS,
  });
  const agents = useQuery({
    queryKey: ["runtime", "agents"],
    queryFn: async () => (await runtimeApi.agents()).agents,
    refetchInterval: REFETCH_MS,
  });

  return {
    socket,
    health,
    status,
    metrics,
    kernel,
    services,
    workflows,
    events,
    logs,
    agents,
    connected: health.isSuccess && status.isSuccess,
  };
}
