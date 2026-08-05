import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Sidebar } from "../components/layout/Sidebar";

const LABELS = [
  "Dashboard",
  "Workflows",
  "AI Agents",
  "Providers",
  "ChatGPT Bridge",
  "Voice Center",
  "MCP Gateway",
  "Execution Planner",
  "Memory",
  "Timeline",
  "Tasks",
  "Queue",
  "Metrics",
];

describe("navigation", () => {
  it("renders Control Center nav items", () => {
    render(
      <MemoryRouter>
        <Sidebar collapsed={false} />
      </MemoryRouter>,
    );
    for (const label of LABELS) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });
});
