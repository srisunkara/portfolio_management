import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    try {
      // eslint-disable-next-line no-console
      console.error("ErrorBoundary caught: ", error, errorInfo);
    } catch {}
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 16, color: "#b91c1c" }}>
          <h2 style={{ marginTop: 0 }}>Something went wrong on this page.</h2>
          <div style={{ whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 12 }}>
            {String(this.state.error)}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
