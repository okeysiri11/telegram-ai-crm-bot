import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { Providers } from "@/shell/Providers";
import { ErrorBoundary } from "@/shell/ErrorBoundary";
import "./index.css";
import "./vertical-workspace/verticalWorkspace.css";
import "./owner-experience/ownerExperience.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <Providers>
        <App />
      </Providers>
    </ErrorBoundary>
  </StrictMode>,
);
