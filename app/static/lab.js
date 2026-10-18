"use strict";

const byId = (id) => document.getElementById(id);
let selected = null;
let current = null;
let executions = 0;

function status(message, error = false) {
  byId("status").textContent = message;
  byId("status").classList.toggle("error", error);
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error("Não foi possível concluir a operação. Tente novamente.");
  return response.json();
}

function renderScenarios(scenarios) {
  byId("scenario-list").replaceChildren();
  scenarios.forEach((scenario) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "scenario-card";
    button.setAttribute("aria-pressed", "false");
    const top = document.createElement("span");
    top.className = "scenario-top";
    const title = document.createElement("strong");
    title.textContent = scenario.id.toUpperCase();
    const reference = document.createElement("span");
    reference.className = "reference";
    reference.textContent = scenario.owasp;
    top.append(title, reference);
    const description = document.createElement("p");
    description.textContent = scenario.title;
    button.append(top, description);
    button.addEventListener("click", () => {
      selected = scenario;
      document.querySelectorAll(".scenario-card").forEach((card) => card.setAttribute("aria-pressed", String(card === button)));
      byId("scenario-description").textContent = scenario.description;
      byId("run").disabled = false;
    });
    byId("scenario-list").append(button);
  });
}

function showResult(payload) {
  current = payload;
  const result = payload.result;
  byId("results").hidden = false;
  byId("result-title").textContent = result.title;
  byId("result-operation").textContent = result.operation;
  byId("result-user").textContent = `Identidade: ${result.user}`;
  byId("result-verdict").textContent = result.passed ? "Proteção confirmada" : "Resultado divergente";
  byId("result-verdict").classList.toggle("failed", !result.passed);
  for (const version of ["vulnerable", "protected"]) {
    byId(`${version}-code`).textContent = `HTTP ${result[version].status_code}`;
    byId(`${version}-body`).textContent = result[version].body === null ? "Sem conteúdo" : JSON.stringify(result[version].body, null, 2);
  }
  byId("result-impact").textContent = result.impact;
  byId("result-mitigation").textContent = result.mitigation;
  byId("run-count").textContent = String(++executions).padStart(2, "0");
  byId("run-summary").textContent = `Última: ${result.scenario.toUpperCase()}`;
  byId("download-md").disabled = false;
  byId("download-json").disabled = false;
  byId("report-preview").hidden = false;
  byId("markdown-preview").textContent = payload.markdown;
}

byId("run").addEventListener("click", async () => {
  if (!selected) return;
  const scenario = selected;
  byId("run").disabled = true;
  document.querySelectorAll(".scenario-card").forEach((card) => { card.disabled = true; });
  byId("run").setAttribute("aria-busy", "true");
  status(`Executando ${scenario.id.toUpperCase()}…`);
  try {
    showResult(await request(`/api/simulations/${encodeURIComponent(scenario.id)}`, {method: "POST"}));
    status("Simulação concluída. Respostas e relatório disponíveis abaixo.");
  } catch (error) {
    status(error.message, true);
  } finally {
    byId("run").disabled = false;
    byId("run").removeAttribute("aria-busy");
    document.querySelectorAll(".scenario-card").forEach((card) => { card.disabled = false; });
  }
});

function download(format) {
  if (!current) return;
  const content = format === "json" ? JSON.stringify(current.result, null, 2) : current.markdown;
  const blob = new Blob([content], {type: format === "json" ? "application/json" : "text/markdown;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `apisec-${current.result.scenario}-${current.result.id}.${format}`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
byId("download-md").addEventListener("click", () => download("md"));
byId("download-json").addEventListener("click", () => download("json"));

request("/api/scenarios").then((scenarios) => {
  renderScenarios(scenarios);
}).catch((error) => {
  byId("scenario-list").textContent = "Cenários indisponíveis. Atualize a página para tentar novamente.";
  status(error.message, true);
});
request("/api/test-status").then((result) => {
  if (!result.available) {
    byId("test-count").textContent = "Sem registro";
    byId("test-summary").textContent = "Gere reports/junit.xml com Pytest";
    return;
  }
  byId("test-count").textContent = `${result.tests} testes`;
  byId("test-summary").textContent = `${result.failures} falhas · ${result.errors} erros · ${result.skipped} ignorados (último JUnit)`;
}).catch(() => {
  byId("test-count").textContent = "Indisponível";
  byId("test-summary").textContent = "Não foi possível consultar o JUnit";
});
