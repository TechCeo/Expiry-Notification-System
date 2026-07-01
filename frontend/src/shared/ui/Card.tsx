import { PropsWithChildren } from "react";

export function Card({ children }: PropsWithChildren) {
  return <section className="card">{children}</section>;
}
