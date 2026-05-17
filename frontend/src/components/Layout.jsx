import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function Layout() {
    return (
        <div className="flex h-screen bg-gray-50 overflow-hidden text-slate-800">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
                <Outlet />
            </div>
        </div>
    );
}
