// Dragging in the project screen (docs/project-screen.md#checks-uxmd-checklist): HTML5 drag events
// caught once on the document. Draggables: file chips [data-file] (with [data-from] = their song),
// a suggested song's handle [data-files] (a JSON list of file ids) and song titles [data-title].
// Drop targets: [data-drop] ("song:<id>", "sugg:<n>", "new", "notsong", "tosort").
// Highlighting stays here; the server gets one "screen_drop" event per drop. Esc cancels a drag
// (the browser does it), and nothing is sent.
(() => {
  let dragged = null; // {kind: "files" | "song", files: [[from, file], ...], song}

  const clear = () => {
    document.body.classList.remove("dt-dragging", "dt-dragging-song");
    document.querySelectorAll(".drop-hi").forEach((e) => e.classList.remove("drop-hi"));
  };

  document.addEventListener("dragstart", (e) => {
    const chip = e.target.closest?.("[data-file]");
    const title = e.target.closest?.("[data-title]");
    const row = e.target.closest?.("[data-files]");
    if (row && !chip) {
      dragged = { kind: "files", files: JSON.parse(row.dataset.files).map((f) => ["", f]) };
      e.dataTransfer.setData("text/plain", row.innerText);
      e.dataTransfer.effectAllowed = "move";
      document.body.classList.add("dt-dragging");
    } else if (chip) {
      // a selected chip drags the whole selection, another chip drags only itself
      const picked = chip.classList.contains("sel")
        ? [...document.querySelectorAll(".fchip.sel[data-file]")]
        : [chip];
      dragged = {
        kind: "files",
        files: picked.map((c) => [c.dataset.from || "", c.dataset.file]),
      };
      e.dataTransfer.setData("text/plain", picked.map((c) => c.innerText).join(", "));
      e.dataTransfer.effectAllowed = "copyMove";
      document.body.classList.add("dt-dragging");
    } else if (title) {
      dragged = { kind: "song", song: title.dataset.title, files: [] };
      e.dataTransfer.setData("text/plain", title.innerText);
      e.dataTransfer.effectAllowed = "move";
      document.body.classList.add("dt-dragging-song");
    }
  });

  const target = (e) => {
    const zone = e.target.closest?.("[data-drop]");
    if (!zone || !dragged) return null;
    // a title only merges into another song
    if (dragged.kind === "song" && !zone.dataset.drop.startsWith("song:")) return null;
    if (dragged.kind === "song" && zone.dataset.drop === "song:" + dragged.song) return null;
    return zone;
  };

  document.addEventListener("dragover", (e) => {
    const zone = target(e);
    if (!zone) return;
    e.preventDefault(); // makes it a drop target
    e.dataTransfer.dropEffect = e.ctrlKey && dragged.kind === "files" ? "copy" : "move";
    if (!zone.classList.contains("drop-hi")) {
      document.querySelectorAll(".drop-hi").forEach((x) => x.classList.remove("drop-hi"));
      zone.classList.add("drop-hi");
    }
  });

  document.addEventListener("dragleave", (e) => {
    const zone = e.target.closest?.("[data-drop]");
    if (zone && !zone.contains(e.relatedTarget)) zone.classList.remove("drop-hi");
  });

  document.addEventListener("drop", (e) => {
    const zone = target(e);
    if (!zone) return;
    e.preventDefault();
    const onto = e.target.closest?.("[data-file]");
    emitEvent("screen_drop", {
      ...dragged,
      to: zone.dataset.drop,
      copy: e.ctrlKey || e.metaKey,
      onto: onto ? onto.dataset.file : "",
    });
    dragged = null;
    clear();
  });

  document.addEventListener("dragend", () => {
    dragged = null;
    clear();
  });
})();
