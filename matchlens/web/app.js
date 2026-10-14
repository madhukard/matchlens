const $ = (id) => document.getElementById(id);
const state = {
  live: true,
  frame: -1,
  polling: null,
  audience: "fan",
  language: "en",
  start: 3300,
  end: 3900,
  data: null,
  selected: null,
  timer: null,
  request: 0,
};
const embedded = window.parent !== window;
const pending = new Map();
let rpcId = 0;
let hostReady = false;
const fmt = (seconds) =>
  `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
const labels = {
  en: {
    pass: "Pass",
    recovery: "Recovery",
    shot: "Shot",
    goal: "Goal",
    pressure: "Pressure",
  },
  es: {
    pass: "Pase",
    recovery: "Recuperación",
    shot: "Disparo",
    goal: "Gol",
    pressure: "Presión",
  },
};
function rpc(method, params) {
  return new Promise((resolve, reject) => {
    const id = ++rpcId;
    const timeout = setTimeout(() => {
      pending.delete(id);
      reject(
        new Error(
          "The host did not respond. Please reconnect the MatchLens app.",
        ),
      );
    }, 12000);
    pending.set(id, { resolve, reject, timeout });
    window.parent.postMessage({ jsonrpc: "2.0", id, method, params }, "*");
  });
}
function notify(method, params) {
  if (hostReady)
    window.parent.postMessage({ jsonrpc: "2.0", method, params }, "*");
}
function hostContext(ctx) {
  if (!ctx) return;
  if (["light", "dark"].includes(ctx.theme)) {
    document.documentElement.dataset.theme = ctx.theme;
    document.documentElement.style.colorScheme = ctx.theme;
  }
  for (const [key, value] of Object.entries(ctx.styles?.variables || {})) {
    if (key.startsWith("--") && typeof value === "string")
      document.documentElement.style.setProperty(key, value);
  }
  if (ctx.safeAreaInsets)
    for (const [side, value] of Object.entries(ctx.safeAreaInsets)) {
      if (
        ["top", "bottom", "left", "right"].includes(side) &&
        Number.isFinite(value)
      )
        document.body.style.setProperty(`padding-${side}`, `${value}px`);
    }
}
window.addEventListener("message", (event) => {
  if (
    !embedded ||
    event.source !== window.parent ||
    event.data?.jsonrpc !== "2.0"
  )
    return;
  const message = event.data;
  if (pending.has(message.id)) {
    const item = pending.get(message.id);
    clearTimeout(item.timeout);
    pending.delete(message.id);
    if (message.error) item.reject(new Error(message.error.message));
    else item.resolve(message.result);
  } else if (
    message.method === "ui/notifications/tool-result" &&
    message.params?.structuredContent?.match
  ) {
    accept(message.params.structuredContent);
  } else if (message.method === "ui/notifications/host-context-changed")
    hostContext(message.params);
});
async function tool(name, args) {
  let result;
  if (embedded) result = await rpc("tools/call", { name, arguments: args });
  else {
    const response = await fetch("/api/tools", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, arguments: args }),
    });
    if (!response.ok)
      throw new Error(
        `Match service returned ${response.status}. Please try again.`,
      );
    result = await response.json();
  }
  if (result.isError)
    throw new Error(result.content?.[0]?.text || "Tool could not complete.");
  return result.structuredContent;
}
function showError(error) {
  $("error").hidden = false;
  $("error").textContent = error.message || String(error);
}
async function load(background = false) {
  const request = ++state.request;
  $("error").hidden = true;
  if (!background) stop();
  try {
    const data = await tool(
      state.live ? "get_live_match" : "explain_moment",
      state.live
        ? {
            frame: state.frame,
            audience: state.audience,
            language: state.language,
          }
        : {
            match_id: "harbor-summit-demo",
            start_second: state.start,
            end_second: state.end,
            audience: state.audience,
            language: state.language,
          },
    );
    if (request === state.request) {
      if (
        background &&
        data.live?.run_id === state.data?.live?.run_id &&
        data.live?.updated_at === state.data?.live?.updated_at
      ) {
        state.polling = setTimeout(
          () => load(true),
          data.live.status === "running" ? 5000 : 15000,
        );
      } else accept(data);
    }
  } catch (error) {
    if (request === state.request) {
      showError(error);
      if (background && state.live && state.frame === -1)
        state.polling = setTimeout(() => load(true), 15000);
    }
  }
}
function accept(data) {
  if (!data?.match || !Array.isArray(data.events)) return;
  stop();
  state.live = Boolean(data.live);
  state.data = data;
  clearTimeout(state.polling);
  state.start = data.window.start_second;
  state.end = data.window.end_second;
  if (data.insight) {
    state.audience = data.insight.audience;
    state.language = data.insight.language;
  }
  $("language").value = state.language;
  document.documentElement.lang = state.language;
  for (const mode of ["fan", "analyst"]) {
    $(mode).classList.toggle("active", mode === state.audience);
    $(mode).setAttribute("aria-pressed", String(mode === state.audience));
  }
  $("score").textContent = `${data.score.harbor} : ${data.score.summit}`;
  $("match-clock").textContent =
    `${Math.floor(state.end / 60)}′ · REPLAY SNAPSHOT`;
  $("window-title").textContent =
    state.start === 0
      ? "The whole match"
      : `${Math.floor(state.start / 60)}–${Math.floor(state.end / 60)}′ · The turning point`;
  const insight = data.insight;
  $("source").textContent =
    insight?.source === "agents_sdk"
      ? "AI narrative · evidence reviewed"
      : "Statistics only · AI not generated";
  $("headline").textContent =
    insight?.narrative.headline || "Explore the match";
  $("summary").textContent =
    insight?.narrative.summary || "Select an event to inspect its evidence.";
  $("uncertainty").textContent = insight?.analysis?.uncertainty || "";
  $("uncertainty").hidden = !$("uncertainty").textContent;
  $("metrics").replaceChildren();
  const metrics =
    state.audience === "fan"
      ? [
          ["shots", "Shots"],
          ["high_recoveries", "High recoveries"],
          ["goals", "Goals in window"],
        ]
      : [
          ["completed_passes", "Completed passes"],
          ["pass_accuracy", "Pass accuracy %"],
          ["progressive_passes", "Progressive passes"],
        ];
  for (const [key, label] of metrics) {
    const block = document.createElement("div");
    block.className = "metric";
    const caption = document.createElement("span");
    caption.textContent =
      state.language === "es"
        ? {
            Shots: "Disparos",
            "High recoveries": "Recuperaciones altas",
            "Goals in window": "Goles del intervalo",
            "Completed passes": "Pases completos",
            "Pass accuracy %": "Precisión de pase %",
            "Progressive passes": "Pases progresivos",
          }[label] || label
        : label;
    const number = document.createElement("strong");
    number.textContent = `${data.stats.harbor[key] ?? "—"} / ${data.stats.summit[key] ?? "—"}`;
    const legend = document.createElement("small");
    legend.textContent = "Harbor / Summit";
    block.append(caption, number, legend);
    $("metrics").append(block);
  }
  const oldPlayer = $("player").value;
  $("player").replaceChildren(
    new Option(state.language === "es" ? "Todos" : "All players", "all"),
  );
  for (const player of [...new Set(data.events.map((e) => e.player))].sort())
    $("player").add(new Option(player, player));
  $("player").value = [...$("player").options].some(
    (o) => o.value === oldPlayer,
  )
    ? oldPlayer
    : "all";
  $("time").min = state.start;
  $("time").max = state.end - 1;
  $("time").value = state.end - 1;
  const ids = new Set(insight?.narrative.evidence_event_ids || []);
  const evidence = data.events.filter((e) => ids.has(e.event_id));
  $("evidence-count").textContent = String(evidence.length);
  $("evidence-list").replaceChildren();
  for (const event of evidence)
    $("evidence-list").append(eventButton(event, true));
  if (!evidence.length) {
    const note = document.createElement("p");
    note.className = "muted";
    note.textContent =
      insight?.source === "agents_sdk"
        ? state.language === "es"
          ? "Esta explicación cita recuentos agregados. Consulta las estadísticas."
          : "This explanation cites aggregate counts. See the match statistics."
        : state.language === "es"
          ? "Aún no hay una explicación revisada. Explora los eventos."
          : "No reviewed narrative for this window. Browse the events below.";
    $("evidence-list").append(note);
  }
  $("show-evidence").disabled = !evidence.length;
  state.selected = evidence[0] || data.events.at(-1) || null;
  if (state.selected) $("time").value = state.selected.second;
  renderLive(data);
  renderEvents();
  updateContext();
}
function eventButton(event, evidence = false) {
  const button = document.createElement("button");
  button.className = evidence ? "evidence-item" : "";
  button.dataset.id = event.event_id;
  const minute = document.createElement("strong");
  minute.textContent = fmt(event.second);
  const caption = document.createElement("span");
  caption.textContent = `${labels[state.language][event.kind]} · ${event.player}${event.void ? (state.language === "es" ? " · anulado" : " · voided") : ""}`;
  const id = document.createElement("small");
  id.textContent = event.event_id;
  caption.append(id);
  button.append(minute, caption);
  button.addEventListener("click", () => {
    state.selected = event;
    $("time").value = event.second;
    draw();
    updateContext();
  });
  return button;
}
function renderEvents() {
  const visible = state.data.events.filter(
    (e) => $("player").value === "all" || e.player === $("player").value,
  );
  $("timeline").replaceChildren(...visible.map((e) => eventButton(e)));
  $("event-count").textContent =
    `${visible.length} ${state.language === "es" ? "eventos registrados" : "recorded events"}`;
  if (state.selected && !visible.includes(state.selected))
    state.selected = visible[0] || null;
  draw();
}
function svgElement(name, attrs) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attrs))
    node.setAttribute(key, String(value));
  return node;
}
function draw() {
  const time = Number($("time").value);
  $("time-label").textContent = fmt(time);
  $("event-trails").replaceChildren();
  $("active-event").replaceChildren();
  const visible = state.data.events.filter(
    (e) =>
      e.second <= time &&
      ($("player").value === "all" || e.player === $("player").value),
  );
  for (const event of visible.slice(-18)) {
    const color = event.team === "harbor" ? "#e3f3b0" : "#f1bc72";
    $("event-trails").append(
      svgElement("circle", {
        cx: event.x,
        cy: event.y,
        r: 0.75,
        fill: color,
        opacity: 0.4,
      }),
    );
  }
  const event =
    state.selected?.second <= time ? state.selected : visible.at(-1);
  if (event) {
    const color = event.team === "harbor" ? "#e3f3b0" : "#f1bc72";
    const group = $("active-event");
    group.append(
      svgElement("line", {
        x1: event.x,
        y1: event.y,
        x2: event.end_x,
        y2: event.end_y,
        stroke: color,
        "stroke-width": 0.75,
        "stroke-dasharray": event.successful ? "none" : "2 1",
      }),
    );
    group.append(
      svgElement("circle", {
        cx: event.x,
        cy: event.y,
        r: 2.3,
        fill: color,
        stroke: "#163d31",
        "stroke-width": 0.5,
      }),
    );
    group.append(
      svgElement("circle", {
        cx: event.end_x,
        cy: event.end_y,
        r: 1,
        fill: color,
      }),
    );
    const text = svgElement("text", {
      x: event.x,
      y: event.y - 4,
      fill: "#fff",
      "font-size": 2.8,
      "text-anchor": "middle",
    });
    text.textContent = event.player;
    group.append(text);
    $("event-caption").textContent =
      `${fmt(event.second)} · ${labels[state.language][event.kind]} · ${event.player}${event.void ? (state.language === "es" ? " · anulado" : " · voided") : event.successful ? "" : state.language === "es" ? " · sin éxito" : " · unsuccessful"}`;
  } else
    $("event-caption").textContent =
      "No events at this point in the selected window";
  for (const button of $("timeline").querySelectorAll("button"))
    button.classList.toggle("selected", button.dataset.id === event?.event_id);
}
function updateContext() {
  if (!hostReady) return;
  rpc("ui/update-model-context", {
    structuredContent: {
      match_id: state.data?.match?.match_id || "harbor-summit-demo",
      run_id: state.data?.live?.run_id,
      frame: state.data?.live?.frame,
      evidence_hash: state.data?.evidence_hash,
      window: { start_second: state.start, end_second: state.end },
      audience: state.audience,
      language: state.language,
      selected_event_id: state.selected?.event_id || null,
    },
  }).catch(() => {});
}
function stop() {
  clearInterval(state.timer);
  state.timer = null;
  $("play").textContent = "▶";
  $("play").setAttribute("aria-label", "Play event replay");
}
const words = {
  en: {
    tagline: "FOOTBALL, EXPLAINED.",
    title: "There’s more to the score.",
    intro: "Follow the moments. Explore the evidence. Understand the game.",
    home: "HOME",
    away: "AWAY",
    language: "Language",
    focus: "Focus",
    support: "Supporting moments",
    timeline: "Match timeline",
    explore: "Explore the sequence",
    dataNote:
      "Synthetic on-ball events and authored pressure tags. Counts are not possession, xG or proof of causality.",
    reviewNote:
      "Evidence IDs connect explanations to versioned events. Model review does not guarantee correctness.",
    moment: "Moment",
    watch: "Watch latest",
    pitch: "Pitch",
    comparison: "Before / after",
    sequence: "Sequence",
    checked: "How this was checked",
    latest: "Latest update",
    fan: "Fan view",
    analyst: "Analyst view",
    why: "Show me why ↗",
    stages: [
      "Opening control",
      "First chance",
      "Late event arrives",
      "Pressure and recovery",
      "Goal reported",
      "Goal corrected",
    ],
  },
  es: {
    tagline: "EL FÚTBOL, EXPLICADO.",
    title: "Hay más que el marcador.",
    intro: "Sigue los momentos. Explora la evidencia. Entiende el partido.",
    home: "LOCAL",
    away: "VISITANTE",
    language: "Idioma",
    focus: "Enfoque",
    support: "Momentos de apoyo",
    timeline: "Cronología del partido",
    explore: "Explora la secuencia",
    dataNote:
      "Eventos sintéticos y etiquetas de presión creadas para la demostración. Los recuentos no son posesión, xG ni prueba de causalidad.",
    reviewNote:
      "Los identificadores enlazan las explicaciones con eventos versionados. La revisión del modelo no garantiza la exactitud.",
    moment: "Momento",
    watch: "Ver lo último",
    pitch: "Campo",
    comparison: "Antes / después",
    sequence: "Secuencia",
    checked: "Cómo se verificó",
    latest: "Última actualización",
    fan: "Afición",
    analyst: "Análisis",
    why: "Muéstrame por qué ↗",
    stages: [
      "Control inicial",
      "Primera ocasión",
      "Llega un evento tardío",
      "Presión y recuperación",
      "Gol registrado",
      "Gol corregido",
    ],
  },
};
function setView(view) {
  if (!["pitch", "comparison", "timeline"].includes(view)) view = "pitch";
  document.querySelector(".pitch-wrap").hidden = view !== "pitch";
  $("comparison-panel").hidden = view !== "comparison";
  $("sequence-panel").hidden = view !== "timeline";
  for (const name of ["pitch", "comparison", "timeline"])
    $("view-" + name).setAttribute("aria-pressed", String(name === view));
}
function renderLive(data) {
  const es = state.language === "es";
  const w = words[state.language];
  for (const node of document.querySelectorAll("[data-i18n]"))
    node.textContent = w[node.dataset.i18n];
  $("fan").textContent = w.fan;
  $("analyst").textContent = w.analyst;
  $("show-evidence").textContent = w.why;
  $("recap").textContent = es
    ? "Resumen de exhibición ↗"
    : "Exhibition recap ↗";
  $("uncertainty").textContent =
    es && data.insight?.analysis?.uncertainty
      ? "Datos sintéticos; los recuentos no demuestran causalidad."
      : data.insight?.analysis?.uncertainty || "";
  $("source").textContent =
    data.insight?.source === "agents_sdk"
      ? es
        ? "Narración de IA · evidencia revisada"
        : "AI narrative · evidence reviewed"
      : es
        ? "Estadísticas · revisión pendiente o no disponible"
        : "Statistics · review pending or unavailable";
  document.querySelector(".live-controls").hidden = !data.live;
  document.querySelector(".view-controls").hidden = !data.live;
  document.querySelector(".workflow-details").hidden = !data.live;
  $("correction").hidden = true;
  $("view-reason").textContent = "";
  if (!data.live) {
    setView("pitch");
    return;
  }
  const live = data.live;
  const age = live.updated_at
    ? (Date.now() - Date.parse(live.updated_at)) / 1000
    : Infinity;
  const running = live.status === "running" && age < 240 && state.frame === -1;
  $("run-status").textContent = running
    ? es
      ? "EN DIRECTO · simulación sintética"
      : "LIVE · synthetic simulation"
    : es
      ? "REPETICIÓN · ejecución registrada"
      : "REPLAY · recorded run";
  if (live.status === "not_started")
    $("run-status").textContent = es
      ? "Esperando al operador"
      : "Waiting for the operator";
  if (live.status === "running" && age >= 240)
    $("run-status").textContent = es
      ? "Actualización retrasada"
      : "Update delayed · last received state";
  $("run-detail").textContent =
    `${w.stages[live.frame] || ""} · ${es ? "revisión" : "revision"} ${data.revision}${live.updated_at ? " · " + new Date(live.updated_at).toLocaleTimeString(state.language) : ""}`;
  $("match-clock").textContent =
    `${fmt(state.end - 1)} · ${running ? "LIVE" : "REPLAY"}`;
  $("window-title").textContent = w.stages[live.frame] || w.latest;
  $("frame").replaceChildren(new Option(w.latest, "-1"));
  for (let i = 0; i < live.frame_count; i++)
    $("frame").add(new Option(`${i + 1}. ${w.stages[i]}`, String(i)));
  $("frame").value = String(state.frame);
  if (data.facts?.["corrections.void_goals"]?.value) {
    $("correction").hidden = false;
    $("correction").textContent = es
      ? "Marcador corregido: el gol anterior fue anulado por una revisión del evento. El feed no indica el motivo."
      : "Score corrected: the earlier goal was voided by an event revision. The feed does not state why.";
  }
  $("comparison-panel").replaceChildren();
  const table = document.createElement("table");
  const caption = document.createElement("caption");
  caption.textContent = es
    ? "Harbor · recuentos por intervalo"
    : "Harbor · counts by window";
  table.append(caption);
  const rows = [
    [
      es ? "Métrica" : "Metric",
      `${es ? "Antes" : "Before"} (${data.comparison.before_seconds}s)`,
      `${es ? "Después" : "After"} (${data.comparison.after_seconds}s)`,
    ],
  ];
  for (const [key, label] of [
    ["completed_passes", es ? "Pases completos" : "Completed passes"],
    ["high_recoveries", es ? "Recuperaciones altas" : "High recoveries"],
    ["shots", es ? "Disparos" : "Shots"],
    ["goals", es ? "Goles" : "Goals"],
  ])
    rows.push([
      label,
      data.comparison.before.harbor[key],
      data.comparison.after.harbor[key],
    ]);
  rows.forEach((row, index) => {
    const tr = document.createElement("tr");
    for (const value of row) {
      const cell = document.createElement(index ? "td" : "th");
      cell.textContent = value;
      tr.append(cell);
    }
    table.append(tr);
  });
  $("comparison-panel").append(table);
  const note = document.createElement("p");
  note.className = "muted";
  note.textContent = es
    ? "Los intervalos pueden tener distinta duración. Los recuentos no prueban causalidad."
    : "Windows may have different durations. Event counts do not establish causality.";
  $("comparison-panel").append(note);
  $("sequence-panel").replaceChildren(
    ...data.events
      .filter((e) => e.kind !== "pass" || e.void)
      .map((e) => eventButton(e, true)),
  );
  const view = data.insight?.analysis?.recommended_view || "pitch";
  setView(
    state.audience === "analyst" && view !== "timeline" ? "comparison" : view,
  );
  $("view-reason").textContent = es
    ? "Vista elegida para esta explicación; puedes cambiarla."
    : "View selected for this explanation; you can change it.";
  $("workflow").replaceChildren();
  for (const step of live.workflow) {
    const row = document.createElement("p");
    row.textContent = `${step.agent} · ${step.status}${step.latency_seconds ? " · " + step.latency_seconds + "s" : ""}${step.reason ? " · " + step.reason : ""}`;
    $("workflow").append(row);
  }
  const summary = document.createElement("p");
  summary.textContent = `${live.model || ""} · ${live.input_tokens} input / ${live.output_tokens} output tokens · ${live.latency_seconds || "—"}s. ${es ? "Revisión de modelos, no certificación humana." : "Model review, not human certification."}`;
  $("workflow").append(summary);
  if (state.frame === -1)
    state.polling = setTimeout(() => load(true), running ? 5000 : 15000);
}
for (const view of ["pitch", "comparison", "timeline"])
  $("view-" + view).addEventListener("click", () => setView(view));
$("frame").addEventListener("change", () => {
  state.frame = Number($("frame").value);
  load();
});
$("watch-live").addEventListener("click", () => {
  state.live = true;
  state.frame = -1;
  load();
});
$("play").addEventListener("click", () => {
  if (state.timer) {
    stop();
    return;
  }
  if (!state.data) return;
  if (Number($("time").value) >= state.end - 1) $("time").value = state.start;
  state.selected = null;
  $("play").textContent = "Ⅱ";
  $("play").setAttribute("aria-label", "Pause event replay");
  state.timer = setInterval(() => {
    $("time").value = Math.min(state.end - 1, Number($("time").value) + 15);
    draw();
    if (Number($("time").value) >= state.end - 1) stop();
  }, 350);
});
$("time").addEventListener("input", () => {
  stop();
  state.selected = null;
  draw();
});
$("player").addEventListener("change", () => {
  renderEvents();
  updateContext();
});
$("show-evidence").addEventListener("click", () => {
  const ids = state.data.insight.narrative.evidence_event_ids;
  const id =
    state.data.events.find((e) => e.void && ids.includes(e.event_id))
      ?.event_id || ids.at(-1);
  state.selected = state.data.events.find((e) => e.event_id === id);
  $("time").value = state.selected.second;
  draw();
  updateContext();
});
for (const mode of ["fan", "analyst"])
  $(mode).addEventListener("click", () => {
    state.audience = mode;
    load();
  });
$("language").addEventListener("change", () => {
  state.language = $("language").value;
  load();
});
$("recap").addEventListener("click", () => {
  state.live = false;
  clearTimeout(state.polling);
  state.start = 0;
  state.end = 5400;
  load();
});
$("reset-window").addEventListener("click", () => {
  state.live = false;
  clearTimeout(state.polling);
  state.start = 3300;
  state.end = 3900;
  load();
});
window.addEventListener("pagehide", () => {
  stop();
  clearTimeout(state.polling);
});
async function start() {
  if (embedded) {
    try {
      const init = await rpc("ui/initialize", {
        appInfo: { name: "matchlens", version: "0.1.0" },
        appCapabilities: {},
        protocolVersion: "2026-01-26",
      });
      hostReady = true;
      hostContext(init.hostContext);
      notify("ui/notifications/initialized", {});
      if (!state.data) await load();
    } catch (error) {
      showError(error);
    }
  } else await load();
}
start();

new ResizeObserver(() =>
  notify("ui/notifications/size-changed", {
    height: document.documentElement.scrollHeight,
  }),
).observe(document.body);
