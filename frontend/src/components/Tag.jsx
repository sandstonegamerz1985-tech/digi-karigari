// Small coloured labels used across the app.
import { useLang } from "../i18n";

export function FeatureTag({ status }) {
  return <span className={`tag tag-${status}`}>{status}</span>;
}

export function VerifiedBadge({ verified = true }) {
  const { t } = useLang();
  if (!verified) return null;
  return (
    <span className="badge-verified" title="Approved by a Digi Karigari admin">
      &#10003; {t("common.verified")}
    </span>
  );
}
