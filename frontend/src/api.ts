import type { LogAnalysisResponse, LogInput, StoredLogAnalysis } from "./types";

async function readError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    return JSON.stringify(payload.detail ?? payload);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

export async function analyzeLog(input: LogInput): Promise<LogAnalysisResponse> {
  const response = await fetch("/logs/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json();
}

export async function listLogAnalyses(): Promise<StoredLogAnalysis[]> {
  const response = await fetch("/logs");

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json();
}

export async function deleteLogAnalysis(id: number): Promise<void> {
  const response = await fetch(`/logs/${id}`, { method: "DELETE" });

  if (!response.ok) {
    throw new Error(await readError(response));
  }
}
