import React from "react";
import ReactDOM from "react-dom/client";

import { AppRoutes } from "./app/routes";
import "./styles/variables.css";
import "./styles/app.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppRoutes />
  </React.StrictMode>,
);
