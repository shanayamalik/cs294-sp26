import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ClaimChartDemo from "./ClaimChartDemo";
import "./styles.css";

function Root() {
  const [hash, setHash] = useState(() => window.location.hash);

  useEffect(() => {
    function handleHashChange() {
      setHash(window.location.hash);
    }

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  if (hash === "#claim-chart-demo") {
    return <ClaimChartDemo />;
  }

  return <App />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
