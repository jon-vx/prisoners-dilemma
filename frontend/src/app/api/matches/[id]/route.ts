import { forwardApi } from "@/lib/api";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  return forwardApi(`/matches/${encodeURIComponent(id)}`);
}
