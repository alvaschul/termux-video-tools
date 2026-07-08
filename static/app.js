async function fetchJobs() {
  const res = await fetch("/api/jobs");
  return res.json();
}

function renderJobs(jobs) {
  const container = document.getElementById("jobs");
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
  const url = document.getElementById("url").value;
  const format = document.getElementById("format").value;
  const use_aria2 = document.getElementById("use_aria2").checked;
  const cookiesFileInput = document.getElementById("cookies");
  const form = new FormData();
  form.append("url", url);
  form.append("format", format);
  form.append("use_aria2", use_aria2 ? "true" : "false");
  if (cookiesFileInput.files.length > 0) {
    form.append("cookies_file", cookiesFileInput.files[0]);
  }
  const res = await fetch("/api/download", { method: "POST", body: form });
  const data = await res.json();
  if (data.job_id) {
    alert("Enqueued job: " + data.job_id);
  } else {
    alert("Failed to enqueue job.");
  }
});

setInterval(poll, 2000);
poll();
