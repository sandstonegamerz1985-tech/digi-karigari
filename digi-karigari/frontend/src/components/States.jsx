// Small building blocks for the loading / empty / error states used on every page.
import { Link } from "react-router-dom";
import { useLang } from "../i18n";

export function Loading({ text }) {
  const { t } = useLang();
  return (
    <div className="state" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p>{text || t("common.loading")}</p>
    </div>
  );
}

export function EmptyState({ title, text, actionTo, actionLabel }) {
  return (
    <div className="state">
      <h3>{title}</h3>
      {text && <p>{text}</p>}
      {actionTo && (
        <Link className="btn" to={actionTo}>
          {actionLabel}
        </Link>
      )}
    </div>
  );
}

export function ErrorBox({ message, onRetry }) {
  const { t } = useLang();
  if (!message) return null;
  return (
    <div className="alert alert-error" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button className="btn btn-small btn-outline" onClick={onRetry}>
          {t("common.tryAgain")}
        </button>
      )}
    </div>
  );
}

export function Notice({ kind = "info", children }) {
  return <div className={`alert alert-${kind}`}>{children}</div>;
}
