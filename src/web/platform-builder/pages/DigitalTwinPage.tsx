import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { EnterpriseTwinPage } from "@/enterprise-twin";
import { DigitalTwinStudio } from "../digital-twin/DigitalTwinStudio";

/** Digital Twin hub — living Enterprise Twin by default; classic studio via ?studio=1. */
export function DigitalTwinPage() {
  const [params] = useSearchParams();
  const studio = useMemo(() => params.get("studio") === "1", [params]);
  if (studio) return <DigitalTwinStudio />;
  return <EnterpriseTwinPage showStudioLink />;
}
