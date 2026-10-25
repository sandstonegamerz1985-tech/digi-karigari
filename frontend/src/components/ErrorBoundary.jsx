import { Component } from "react";

// If any page crashes while drawing, React would normally leave a blank screen.
// This catches the crash and shows a readable message instead.
export default class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Digi Karigari crashed while drawing the page:", error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ maxWidth: 560, margin: "3rem auto", padding: "0 1rem", fontFamily: "system-ui, sans-serif" }}>
        <h1>Something went wrong</h1>
        <p>The page could not be shown. Try reloading. If it keeps happening, open the browser console (F12) and check the error.</p>
        <pre style={{ whiteSpace: "pre-wrap", background: "#fde4e1", padding: "0.75rem", borderRadius: 8 }}>
          {String(this.state.error && this.state.error.message ? this.state.error.message : this.state.error)}
        </pre>
        <button onClick={() => window.location.reload()} style={{ padding: "0.5rem 1.1rem", borderRadius: 999, cursor: "pointer" }}>
          Reload
        </button>
      </div>
    );
  }
}
