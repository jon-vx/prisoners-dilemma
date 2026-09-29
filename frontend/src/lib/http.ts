export async function readResponse<T>(response: Response): Promise<T> {
  let data: unknown;
  try {
    data = await response.json();
  } catch (error) {
    if (!(error instanceof SyntaxError)) throw error;
    throw new Error(
      response.ok
        ? "The simulation service returned an invalid response."
        : `Request failed (${response.status}). Please try again.`,
    );
  }
  if (!response.ok) {
    const detail =
      data !== null && typeof data === "object" && "detail" in data
        ? data.detail
        : undefined;
    const message =
      typeof detail === "string"
        ? detail
        : response.status === 422
          ? "Check your strategies, round count, and payoff values."
          : `Request failed (${response.status}). Please try again.`;
    throw new Error(message);
  }
  return data as T;
}
