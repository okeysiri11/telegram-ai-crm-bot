import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { Providers } from "@/shell/Providers";
import { ErrorBoundary } from "@/shell/ErrorBoundary";
import "./index.css";
import "./vertical-workspace/verticalWorkspace.css";
import "./owner-experience/ownerExperience.css";

if (typeof navigator !== "undefined" && "serviceWorker" in navigator) {
  void navigator.serviceWorker.getRegistrations().then((regs) => {
    for (const reg of regs) void reg.unregister();
  });
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <Providers>
        <App />
      </Providers>
    </ErrorBoundary>
  </StrictMode>,
);
