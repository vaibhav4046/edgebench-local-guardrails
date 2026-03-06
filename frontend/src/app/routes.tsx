import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { App } from "./App";
import { DashboardPage } from "../pages/DashboardPage";
import { RunDetailPage } from "../pages/RunDetailPage";

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<DashboardPage />} />
          <Route path="run" element={<RunDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
