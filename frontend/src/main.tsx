import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ClaimChartDemo from "./ClaimChartDemo";
import ExamplePage from "./ExamplePage";
import "./styles.css";

function Root() {
  const [locationState, setLocationState] = useState(() => ({
    hash: window.location.hash,
    pathname: window.location.pathname,
  }));

  useEffect(() => {
    function syncLocation() {
      setLocationState({
        hash: window.location.hash,
        pathname: window.location.pathname,
      });
    }

    window.addEventListener("hashchange", syncLocation);
    window.addEventListener("popstate", syncLocation);
    return () => {
      window.removeEventListener("hashchange", syncLocation);
      window.removeEventListener("popstate", syncLocation);
    };
  }, []);

  const demoMode = locationState.pathname === "/demo";

  if (locationState.pathname === "/example") {
    return <ExamplePage />;
  }

  if (locationState.hash === "#claim-chart-demo") {
    return <ClaimChartDemo demoMode={demoMode} />;
  }

  return <App demoMode={demoMode} />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
