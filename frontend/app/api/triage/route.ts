import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const traceId = req.headers.get("x-trace-id") ?? crypto.randomUUID();

  const backendRes = await fetch(`${BACKEND_URL}/api/triage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Trace-ID": traceId,
    },
    body: JSON.stringify(body),
    // Node 18+ supports streaming with fetch
    // @ts-ignore
    duplex: "half",
  });

  if (!backendRes.ok) {
    const text = await backendRes.text();
    return new Response(text, { status: backendRes.status });
  }

  // Pipe the SSE stream through
  return new Response(backendRes.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
      "X-Trace-ID": traceId,
    },
  });
}
