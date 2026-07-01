export function EmptyState({ message }: { message: string }) {
  return <p className="state state-empty">{message}</p>;
}

export function ErrorState({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "Something went wrong.";
  return <p className="state state-error">{message}</p>;
}

export function LoadingState() {
  return <p className="state">Loading…</p>;
}
