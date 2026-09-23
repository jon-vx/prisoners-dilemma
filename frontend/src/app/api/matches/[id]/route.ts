import { forwardApi } from "@/lib/api";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/i.test(id)) {
    return Response.json({ detail: "Invalid match ID" }, { status: 422 });
  }
  return forwardApi(`/matches/${encodeURIComponent(id)}`);
}
