import { useCallback, useEffect, useState } from "react";
import { analyzeLog, deleteLogAnalysis, listLogAnalyses } from "./api";
import type { LogAnalysisResponse, LogInput, Severity, StoredLogAnalysis } from "./types";

function generateTitle(rawLog: string): string {
  if (!rawLog.trim()) return "Log Analysis";

  // Java / Kotlin / Scala exceptions
  const javaException = rawLog.match(
    /([A-Z][a-zA-Z]*(?:Exception|Error|Fault|Throwable)[^:\n]*):\s*([^\n]+)/
  );
  if (javaException) {
    const exName = javaException[1].split(".").pop()!.trim();
    const msg = javaException[2].trim().replace(/\s+/g, " ").slice(0, 80);
    return `${exName}: ${msg}`;
  }

  // Python tracebacks
  const pyException = rawLog.match(/^([A-Z][a-zA-Z]*(?:Error|Exception|Warning)):\s*(.+)$/m);
  if (pyException) {
    return `${pyException[1]}: ${pyException[2].trim().slice(0, 80)}`;
  }

  // ERROR / FATAL lines with a message
  const errorLine = rawLog.match(/(?:ERROR|FATAL|CRITICAL)\s+[\w.]+\s*[-–]?\s*(.+)/i);
  if (errorLine) {
    return errorLine[1].trim().slice(0, 100);
  }

  // Fallback: first non-empty line
  const firstLine = rawLog.split("\n").find((l) => l.trim().length > 0) ?? "Log Analysis";
  return firstLine.trim().slice(0, 100);
}

const SEVERITY_CLASS: Record<Severity, string> = {
  low: "badge-low",
  medium: "badge-medium",
  high: "badge-high",
  critical: "badge-critical",
};

const EMPTY_FORM: LogInput = {
  title: "",
  language: "java",
  source: "production",
  raw_log: "",
};


function App() {
  const [form, setForm] = useState<LogInput>(EMPTY_FORM);
  const [result, setResult] = useState<LogAnalysisResponse | null>(null);
  const [analyses, setAnalyses] = useState<StoredLogAnalysis[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnalyses = useCallback(async () => {
    try {
      setAnalyses(await listLogAnalyses());
    } catch {
      // Ignore startup history errors. Analysis errors are shown explicitly.
    }
  }, []);

  useEffect(() => {
    void loadAnalyses();
  }, [loadAnalyses]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const titleToUse = form.title.trim() || generateTitle(form.raw_log);
      const response = await analyzeLog({ ...form, title: titleToUse });
      setResult(response);
      setSelectedId(response.analysis_id);
      await loadAnalyses();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    await deleteLogAnalysis(id);
    if (selectedId === id) {
      setSelectedId(null);
      setResult(null);
    }
    await loadAnalyses();
  }

  function selectStoredAnalysis(item: StoredLogAnalysis) {
    setError(null);
    setSelectedId(item.id);
    setResult({ analysis_id: item.id, analysis: item.analysis });
  }

  function scrollToSection(sectionId: string) {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="page-shell">
      <header className="app-header">
        <div className="header-inner">
          <nav className="header-nav" aria-label="Navigation">
            <button
              type="button"
              className="nav-pill nav-pill-button"
              onClick={() => scrollToSection("analyzer")}
            >
              Log &amp; Incident Analyzer
            </button>
            <button
              type="button"
              className="nav-pill nav-pill-button"
              onClick={() => scrollToSection("history")}
            >
              Analysis History ({analyses.length})
            </button>
          </nav>
        </div>
      </header>

      <main className="content">
        <div className="main-layout">
        <section className="box" id="analyzer">
          <h2>New Log Analysis</h2>
          <form onSubmit={handleSubmit}>
            <div className="row">
              <div className="field-box">
                <label>
                  Language
                  <select
                    value={form.language}
                    onChange={(e) => setForm({ ...form, language: e.target.value })}
                  >
                    <option value="java">Java</option>
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="php">PHP</option>
                    <option value="sql">SQL</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </label>
              </div>

              <div className="field-box">
                <label>
                  Source
                  <input
                    value={form.source}
                    onChange={(e) => setForm({ ...form, source: e.target.value })}
                    placeholder="e.g. production, staging, local"
                  />
                </label>
              </div>
            </div>

            <label>
              Logs / Stacktrace *
              <textarea
                required
                minLength={20}
                rows={14}
                value={form.raw_log}
                onChange={(e) => setForm({ ...form, raw_log: e.target.value })}
                placeholder="Paste relevant logs, stacktraces or error output here."
              />
            </label>

            {form.raw_log.trim() && (
              <p className="muted title-preview">
                <strong>Title:</strong> {generateTitle(form.raw_log)}
              </p>
            )}

            <button type="submit" disabled={loading}>
              {loading ? "Analyzing..." : "Analyze Logs"}
            </button>
          </form>
        </section>

        <section className="box">
          <h2>Analysis Result</h2>
          {error && <div className="error-box">{error}</div>}
          {!result && !error && <p className="muted">Submit logs to see the analysis.</p>}

          {result && (
            <div className="result">
              <div className="result-header">
                <span className="analysis-id">#{result.analysis_id}</span>
                <span className={`badge ${SEVERITY_CLASS[result.analysis.severity]}`}>
                  {result.analysis.severity}
                </span>
                <span className="category">{result.analysis.incident_type}</span>
              </div>

              <h3>{result.analysis.short_summary}</h3>
              <p className="muted">Component: {result.analysis.affected_component}</p>

              <div className="confidence">
                <span>Confidence</span>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ width: `${result.analysis.confidence * 100}%` }}
                  />
                </div>
                <span>{Math.round(result.analysis.confidence * 100)}%</span>
              </div>

              <h3>Probable Root Cause</h3>
              <p>{result.analysis.probable_root_cause}</p>

              <h3>Important Log Lines</h3>
              <ul>
                {result.analysis.important_log_lines.map((line, index) => (
                  <li key={index}>
                    <code>{line}</code>
                  </li>
                ))}
              </ul>

              <h3>Recommended Debug Steps</h3>
              <ol>
                {result.analysis.recommended_debug_steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>

              <h3>Possible Fix Direction</h3>
              <p>{result.analysis.possible_fix_direction}</p>

              <h3>Test Cases</h3>
              <ul>
                {result.analysis.test_cases.map((testCase, index) => (
                  <li key={index}>{testCase}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
        </div>
      </main>

      <section className="box" id="history">
        <h2>Analysis History ({analyses.length})</h2>
        {analyses.length === 0 && <p className="muted">No analyses stored yet.</p>}
        <div className="analysis-list">
          {analyses.map((item) => (
            <article
              key={item.id}
              className={`analysis-card ${selectedId === item.id ? "analysis-card-active" : ""}`}
              onClick={() => selectStoredAnalysis(item)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  selectStoredAnalysis(item);
                }
              }}
            >
              <div className="card-header">
                <span className="analysis-id">#{item.id}</span>
                <span className={`badge ${SEVERITY_CLASS[item.analysis.severity]}`}>
                  {item.analysis.severity}
                </span>
                <span className="category">{item.analysis.incident_type}</span>
                <button
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleDelete(item.id);
                  }}
                  title="Delete analysis"
                >
                  ×
                </button>
              </div>
              <h3>{item.title}</h3>
              <p className="muted">{item.analysis.short_summary}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
