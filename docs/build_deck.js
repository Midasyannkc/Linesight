const pptxgen = require("pptxgenjs");
const NAVY = "1A2B3C", TEAL = "2B7A6B", MAROON = "8B3A3A", AMBER = "C97A2B", GRAY = "5B6472", WHITE = "FFFFFF";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";

function titleSlide() {
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("LineSight", { x: 0.8, y: 1.85, w: 11.7, h: 1.3, fontSize: 48, bold: true, color: WHITE, fontFace: "Arial" });
  s.addText("Real-Time OEE, Statistical Process Control & Predictive Maintenance", { x: 0.8, y: 2.9, w: 11.7, h: 0.7, fontSize: 20, color: "9FCBB0", fontFace: "Arial" });
  s.addText("Hybrid Databricks + Snowflake architecture, orchestrated end to end by Dagster", { x: 0.8, y: 3.65, w: 11.7, h: 0.5, fontSize: 14, color: "7FA396", fontFace: "Arial" });
  s.addText("A real 5-step Dagster asset graph ran this entire pipeline across both platforms and returned RUN_SUCCESS. See docs/dagster_run_log.txt.", { x: 0.8, y: 4.35, w: 11.0, h: 0.8, fontSize: 12, color: "D4E4D8", fontFace: "Arial", italic: true });
  s.addText("Christian Kouadio Kouassi", { x: 0.8, y: 6.6, w: 6, h: 0.4, fontSize: 12, color: "6F9686", fontFace: "Arial" });
}
function sectionHeader(title, kicker) {
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText(kicker.toUpperCase(), { x: 0.8, y: 0.55, w: 8, h: 0.4, fontSize: 13, color: TEAL, bold: true, fontFace: "Arial", charSpacing: 1 });
  s.addText(title, { x: 0.8, y: 0.95, w: 11.5, h: 0.85, fontSize: 28, bold: true, color: NAVY, fontFace: "Arial" });
  return s;
}
function bulletBlock(s, items, opts) {
  const o = Object.assign({ x: 0.8, y: 2.0, w: 11.5, h: 4.6, fontSize: 16 }, opts);
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "2022" }, breakLine: i !== items.length - 1, paraSpaceAfter: 14 } })),
    { x: o.x, y: o.y, w: o.w, h: o.h, fontSize: o.fontSize, color: NAVY, fontFace: "Arial", valign: "top", margin: 0 });
}

titleSlide();

{ const s = sectionHeader("The Problem", "Context");
  bulletBlock(s, [
    "A shop floor needs to know, in near real time, whether a line is within statistical control, how efficiently it runs, and whether a machine is about to fail.",
    "That spans classical statistics and modern ML, and in practice runs on two different platforms talking to each other.",
    "Databricks for streaming ML and transformation, Snowflake for governed BI, the real hybrid pattern many enterprises run today.",
  ]); }

{ const s = sectionHeader("Where the Data Comes From", "Data Source");
  bulletBlock(s, [
    "4 production lines, 12 machines: 77,760 sensor readings, 19,440 quality measurements, 107 downtime events.",
    "Built on a documented latent-wear degradation process: sensor readings drift and quality degrades as wear increases.",
    "A failure is injected once wear crosses a threshold, giving both SPC and the ML model real, physically-motivated signal.",
  ]); }

{ const s = sectionHeader("What We're Testing For", "Hypothesis");
  bulletBlock(s, [
    "Whether a real X-bar/R chart can visually surface tool-wear-driven quality drift. It does, drift climbs visibly into the UCL band.",
    "Whether Cpk correctly quantifies how incapable a degrading process is. It does: ~0.02 on every line, far below the 1.33 capable threshold.",
    "Whether a Random Forest can predict failure from sensor data alone. It does: 0.976 ROC-AUC, vibration the dominant feature.",
  ]); }

{ const s = sectionHeader("Stack & Verification", "Architecture");
  const rows = [
    ["Layer", "Tool", "Verification"],
    ["Lakehouse / ML", "Databricks (via PySpark)", "Real, executing medallion transformation"],
    ["Predictive maintenance", "MLflow + Random Forest", "Real model, registered, 0.976 ROC-AUC"],
    ["Statistical modeling", "Python (X-bar/R, Cpk)", "Real Shewhart control-chart math"],
    ["Governed warehouse", "Snowflake (synced, via DuckDB)", "Real dbt build, 11/11 tests passing"],
    ["Orchestration", "Dagster", "Real 5-step asset graph, RUN_SUCCESS"],
  ];
  s.addTable(rows, { x: 0.8, y: 1.9, w: 11.5, h: 3.6, fontSize: 13, fontFace: "Arial", border: { type: "solid", color: "DDDDDD", pt: 1 }, autoPage: false, color: NAVY, fill: { color: WHITE }, valign: "middle", rowH: 0.6 }); }

{ const s = sectionHeader("The Task", "Scope");
  bulletBlock(s, [
    "Transform telemetry through a real Databricks-equivalent medallion pipeline.",
    "Compute real SPC control charts and process capability, train and register a predictive-maintenance model.",
    "Sync the governed layer into Snowflake and certify OEE and downtime Pareto metrics via dbt.",
    "Orchestrate the entire chain as one Dagster asset graph spanning both platforms.",
  ]); }

{ const s = sectionHeader("Results: Control Chart & Capability", "KPI Snapshot");
  s.addImage({ path: "../charts/xbar_control_chart.png", x: 0.5, y: 1.85, w: 7.2, h: 3.96 });
  s.addImage({ path: "../charts/cpk_by_line.png", x: 7.9, y: 1.85, w: 4.6, h: 3.61 });
  s.addText("The control chart makes the wear drift visible by eye. Cpk confirms it numerically: every line is dramatically below the 1.33 capable threshold.",
    { x: 0.8, y: 6.0, w: 11.5, h: 0.6, fontSize: 11, color: GRAY, italic: true, fontFace: "Arial" }); }

{ const s = sectionHeader("Results: Downtime & Maintenance", "KPI Snapshot, Continued");
  s.addImage({ path: "../charts/downtime_pareto.png", x: 1.7, y: 1.9, w: 8.6, h: 5.9 });
  s.addText("Equipment Failure and Unplanned Maintenance together account for 45% of downtime hours, the top two levers for a plant manager's next improvement project.",
    { x: 0.8, y: 6.5, w: 11.5, h: 0.6, fontSize: 11, color: GRAY, italic: true, fontFace: "Arial" }); }

pres.writeFile({ fileName: "kpi_walkthrough.pptx" }).then(() => console.log("Deck written"));
