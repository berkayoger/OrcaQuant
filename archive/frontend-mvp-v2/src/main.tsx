import React from "react";
import { createRoot } from "react-dom/client";
import { Link, RouterProvider, createBrowserRouter } from "react-router-dom";

import Alerts from "./pages/Alerts";
import Indicators from "./pages/Indicators";
import Market from "./pages/Market";
import Portfolio from "./pages/Portfolio";

const router = createBrowserRouter([
  { path: "/", element: <Market /> },
  { path: "/ind", element: <Indicators /> },
  { path: "/portfolio", element: <Portfolio /> },
  { path: "/alerts", element: <Alerts /> }
]);

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <nav style={{ display: "flex", gap: 12, padding: 8, background: "#0B1220" }}>
      <a href="/" style={{ color: "#fff" }}>Market</a>
      <a href="/ind" style={{ color: "#fff" }}>Indicators</a>
      <a href="/portfolio" style={{ color: "#fff" }}>Portföy</a>
      <a href="/alerts" style={{ color: "#fff" }}>Uyarılar</a>
    </nav>
    <RouterProvider router={router} />
  </React.StrictMode>
);
