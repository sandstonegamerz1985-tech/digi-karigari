import { useEffect, useState } from "react";

// Runs an async function and tracks loading / error / data. Call reload() to run it again.
export function useFetch(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: "" });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: "" }));
    fn()
      .then((data) => !cancelled && setState({ data, loading: false, error: "" }))
      .catch((e) => !cancelled && setState({ data: null, loading: false, error: e.message }));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { ...state, reload: () => setTick((t) => t + 1) };
}
