import { forwardApi } from "@/lib/api";

export async function POST(request: Request) {
  return forwardApi("/tournaments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await request.text(),
  });
}
