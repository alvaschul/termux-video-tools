async function fetchJobs() {
  const res = await fetch("/api/jobs");
  return res.json();
}

function renderJobs(jobs) {
  const container = document.getElementById("jobsList");
  container.innerHTML = "";
  const ids = Object.keys(jobs).sort((a,b)=> (jobs[b].created_at || "") - (jobs[a].created_at || ""));
  ids.forEach(id => {
    const j = jobs[id];
    const div = document.createElement("div");
    div.className = "job";
    div.innerHTML = `<strong>${id}</strong> - ${j.url} <div class="meta">${j.status} - ${j.message || ""}</div>`;
    if (j.status === "error") {
      const btn = document.createElement("button");
      btn.textContent = "Retry";
      btn.onclick = async ()=> {
        await fetch(`/api/retry/${id}`, { method: "POST" });
      };
      div.appendChild(btn);
    }
    container.appendChild(div);
  });
}

async function poll() {
  try {
    const jobs = await fetchJobs();
    renderJobs(jobs);
  } catch (e) {
    console.warn("Failed to fetch jobs", e);
  }
}

document.getElementById("downloadForm").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  await downloadVideo();
});

setInterval(poll, 2000);
poll();
