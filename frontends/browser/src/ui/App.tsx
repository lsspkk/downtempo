// The whole app: the first start (or a new project) or the practice page; sign-in coming back.

import { useEffect, useState } from "react";
import { useProjects } from "../core/projects";
import { m } from "../paraglide/messages.js";
import { Practice } from "./practice/Practice";
import { finishSignIn } from "./signin";
import { useTheme } from "./theme";
import { Welcome } from "./start/Welcome";

export default function App() {
  useTheme();
  const { all, current } = useProjects();
  const [creating, setCreating] = useState(false);
  const [problem, setProblem] = useState("");

  useEffect(() => {
    finishSignIn().catch((error) => setProblem(error.message));
  }, []);

  return (
    <>
      {problem && (
        <div role="alert" className="fixed inset-x-0 top-0 z-50 flex justify-center p-2">
          <p className="flex items-center gap-3 rounded-lg bg-red-100 px-4 py-2 text-sm text-red-900 shadow dark:bg-red-950 dark:text-red-100">
            {problem}
            <button className="font-semibold" onClick={() => setProblem("")}>
              {m.ok()}
            </button>
          </p>
        </div>
      )}
      {!current || creating ? (
        <Welcome
          first={!all.length}
          onClose={all.length ? () => setCreating(false) : undefined}
          onDone={() => setCreating(false)}
        />
      ) : (
        <Practice key={current.id} project={current} onNewProject={() => setCreating(true)} />
      )}
    </>
  );
}
