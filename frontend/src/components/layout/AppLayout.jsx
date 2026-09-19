import { Outlet } from "react-router-dom";
import { DocumentsProvider } from "../../context/DocumentsContext.jsx";
import Sidebar from "./Sidebar.jsx";

export default function AppLayout() {
  return (
    <DocumentsProvider>
      <div className="flex h-full flex-col md:flex-row">
        <Sidebar />
        <main className="flex min-h-0 min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </DocumentsProvider>
  );
}
