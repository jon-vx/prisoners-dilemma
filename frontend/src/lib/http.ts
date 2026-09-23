export async function readResponse<T>(response: Response): Promise<T> {
  const data: unknown = await response.json();
  if (!response.ok) {
    const detail =
      data !== null && typeof data === "object" && "detail" in data
        ? data.detail
        : undefined;
    const message =
      typeof detail === "string"
        ? detail
        : "Check your strategies, round count, and payoff values.";
    throw new Error(message);
  }
  return data as T;
}
