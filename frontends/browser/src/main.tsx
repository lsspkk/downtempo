// Mounts the app in its language.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { getLocale } from "./paraglide/runtime.js";
import App from "./ui/App";
import "./index.css";

document.documentElement.lang = getLocale();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
