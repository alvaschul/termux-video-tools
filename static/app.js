// Minimal poller for index.html's inline job queue UI.
// All rendering is handled by loadJobs() in index.html.
(async function () {
  if (typeof loadJobs !== "function") {
    console.warn("loadJobs() not found — app.js expects index.html inline script.");
  }
  setInterval(() => {
    if (typeof loadJobs === "function") {
      loadJobs().catch((e) => console.warn("loadJobs failed:", e));
    }
  }, 2000);
})();
