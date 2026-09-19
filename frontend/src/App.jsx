import { Navigate, Route, Routes } from "react-router-dom";
import { GuestOnly, RequireAuth } from "./components/RouteGuards.jsx";
import AppLayout from "./components/layout/AppLayout.jsx";
import DocumentUpload from "./components/upload/DocumentUpload.jsx";
import QueryWorkspace from "./components/query/QueryWorkspace.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import SignupPage from "./pages/SignupPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<GuestOnly />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
      </Route>
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/documents" element={<DocumentUpload />} />
          <Route path="/query" element={<QueryWorkspace />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/documents" replace />} />
    </Routes>
  );
}
