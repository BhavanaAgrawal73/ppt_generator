const apiBase = (location.origin.includes("localhost") ? "http://127.0.0.1:8000" : window.location.origin).replace(/\/$/, "");

const $ = (id) => document.getElementById(id);

const errBox = $("error");
function showError(msg) {
  errBox.textContent = msg;
  errBox.hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}
function clearError() { errBox.hidden = true; errBox.textContent = ""; }

// ---------------- Model presets + wiring ----------------
const MODEL_PRESETS = {
  openai: [
    "gpt-4o-mini",      // ⭐ best quality/price for slide outlines + notes
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-3.5-turbo"
  ],
  anthropic: [
    "claude-3-5-sonnet-latest",  // ⭐ strong default
    "claude-3-opus-latest",
    "claude-3-haiku-latest"
  ],
  gemini: [
    "gemini-1.5-pro",   // ⭐ for long input
    "gemini-1.5-flash"  // faster/cheaper
  ],
};

function populateModels(provider) {
  const list = $("modelList");
  const help = $("modelHelp");
  list.innerHTML = "";
  const prov = (provider || "").toLowerCase();
  
  const options = MODEL_PRESETS[prov] || [];
  options.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m;
    list.appendChild(opt);
  });

  // Helpful hints per provider
  if (prov === "openai") {
    help.textContent = "Tip: If using an OpenAI-compatible gateway (AI-Pipe), set OPENAI_BASE and choose a model it supports (e.g., gpt-4o-mini).";
  } else if (prov === "gemini") {
    help.textContent = "Use gemini-1.5-pro for long inputs; gemini-1.5-flash for quick/cheap runs.";
  } else if (prov === "anthropic") {
    help.textContent = "claude-3-5-sonnet-latest is a strong default for structured outlines.";
  } else {
    help.textContent = "";
  }
}

  const modelInput = $("model");
  if (modelInput && (!modelInput.value || !options.includes(modelInput.value))) {
    if (options.length) modelInput.value = options[0];
  }


// Prefill guidance via chips
Array.from(document.querySelectorAll('.chip')).forEach(ch => {
  ch.addEventListener('click', () => { $("guidance").value = ch.dataset.guidance; });
});

$("analyzeBtn").addEventListener("click", async () => {
  clearError();
  const text = $("inputText").value.trim();
  const guidance = $("guidance").value.trim();
  const provider = $("provider").value;
  const model = $("model").value.trim();
  const apiKey = $("apiKey").value.trim();
  const tpl = $("templateFile").files[0];

  if (!text || text.length < 10) return showError("Please paste at least 10 characters.");
  if (!apiKey) return showError("Please enter your API key.");
  if (!tpl) return showError("Please upload a .pptx or .potx template.");

  const fd = new FormData();
  fd.append("text", text);
  fd.append("guidance", guidance);
  fd.append("provider", provider);
  fd.append("model", model);
  fd.append("api_key", apiKey);
  fd.append("template", tpl);

  $("analyzeBtn").disabled = true;
  $("analyzeBtn").textContent = "Analyzing…";

  try {
    const res = await fetch(`${apiBase}/analyze`, { method: "POST", body: fd });
    if (!res.ok) {
      let detail = "Analyze failed.";
      try { detail = (await res.json()).detail || res.statusText; } catch {}
      if (detail && /401|unauthorized/i.test(detail) && provider.toLowerCase() === "openai") {
        detail += " • If you're using an OpenAI-compatible gateway (like AI-Pipe), set OPENAI_BASE to your gateway URL.";
      }
      throw new Error(detail);
    }
    const data = await res.json();
    window.__deck = data.deck; // keep in memory for editing
    renderPreview(data.deck);
    $("preview").hidden = false;
  } catch (e) {
    showError("Analyze failed: " + e.message);
  } finally {
    $("analyzeBtn").disabled = false;
    $("analyzeBtn").textContent = "Analyze & Preview";
  }
});

function renderPreview(deck) {
  const slidesDiv = $("slides");
  slidesDiv.innerHTML = "";
  deck.slides.forEach((s) => {
    const card = document.createElement('div');
    card.className = 'slide-card';
    card.innerHTML = `
      <div class="row">
        <input class="title" value="${escapeHtml(s.title)}" />
        <select class="layout">
          ${["Title and Content","Two Content","Title Only","Section Header","Content with Caption"]
            .map(l => `<option ${s.layout_hint===l ? "selected" : ""}>${l}</option>`).join("")}
        </select>
      </div>
      <textarea class="bullets" rows="6" placeholder="One bullet per line">${escapeHtml((s.bullets || []).join("\n"))}</textarea>
      <textarea class="notes" rows="4" placeholder="Speaker notes (optional)">${escapeHtml(s.notes || "")}</textarea>
    `;
    slidesDiv.appendChild(card);
  });
}

function escapeHtml(str){
  return (str || "").replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

$("downloadBtn").addEventListener("click", async () => {
  clearError();
  const tpl = $("templateFile").files[0];
  if (!tpl) return showError("Template missing. Upload again.");

  // Read edits back into deck JSON
  const deck = window.__deck;
  const cards = Array.from(document.querySelectorAll('.slide-card'));
  deck.slides = cards.map(c => ({
    title: c.querySelector('.title').value.trim(),
    layout_hint: c.querySelector('.layout').value,
    bullets: c.querySelector('.bullets').value.split(/\n+/).map(x => x.trim()).filter(Boolean).slice(0,8),
    notes: c.querySelector('.notes').value.trim()
  }));

  const fd = new FormData();
  fd.append("deck_json", JSON.stringify(deck));
  fd.append("template", tpl);

  const provider = $("provider").value;
  const apiKey = $("apiKey").value.trim();
  const model = $("model").value.trim();
  if (apiKey && provider) {
    fd.append("provider", provider);
    fd.append("api_key", apiKey);
    fd.append("model", model);
  }

  const btn = $("downloadBtn");
  btn.disabled = true; btn.textContent = "Generating…";

  try {
    const res = await fetch(`${apiBase}/generate`, { method: "POST", body: fd });
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'generated_presentation.pptx';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    showError("Generate failed: " + e.message);
  } finally {
    btn.disabled = false; btn.textContent = "Generate & Download .pptx";
  }
});

// Hook up presets on load & when provider changes
populateModels($("provider").value);
$("provider").addEventListener("change", () => {
  populateModels($("provider").value);
});

