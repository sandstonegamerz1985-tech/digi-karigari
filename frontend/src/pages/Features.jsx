import { api } from "../api";
import { ErrorBox, Loading } from "../components/States";
import { FeatureTag } from "../components/Tag";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";

const GROUPS = [
  ["implemented", "Implemented: works in this demo"],
  ["demo-only", "Demo-only: works, but simulated or simplified"],
  ["planned", "Planned: NOT built yet"],
];

export default function Features() {
  const { t } = useLang();
  const { data, loading, error, reload } = useFetch(() => api.features(), []);
  return (
    <div className="container narrow-lg section">
      <h1>{t("features.title")}</h1>
      <p className="muted">{t("features.intro")}</p>
      {loading && <Loading />}
      <ErrorBox message={error} onRetry={reload} />
      {data &&
        GROUPS.map(([status, label]) => (
          <section key={status} className="section">
            <h2>{label}</h2>
            <ul className="feature-list">
              {data
                .filter((f) => f.status === status)
                .map((f) => (
                  <li key={f.key}>
                    <FeatureTag status={f.status} /> <strong>{f.name}</strong>
                    {f.note && <p className="small muted">{f.note}</p>}
                  </li>
                ))}
            </ul>
          </section>
        ))}
    </div>
  );
}
