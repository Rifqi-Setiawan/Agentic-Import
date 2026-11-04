import { ReactNode } from "react";
import { label } from "../api";
export function Card({
  title,
  children,
}: {
  title?: string;
  children: ReactNode;
}) {
  return (
    <section className="card">
      {title && <h2>{title}</h2>}
      {children}
    </section>
  );
}
export function Badge({ value }: { value?: string }) {
  return (
    <span
      className={`badge ${["ready", "approved", "succeeded", "provided"].includes(value || "") ? "good" : ["failed", "blocked", "rejected", "high"].includes(value || "") ? "bad" : ""}`}
    >
      {label(value)}
    </span>
  );
}
export function Empty({
  children = "Belum ada data.",
}: {
  children?: ReactNode;
}) {
  return <p className="empty">{children}</p>;
}
export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}
