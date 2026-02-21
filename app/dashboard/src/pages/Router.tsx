import { createHashRouter } from "react-router-dom";
import { fetch } from "../service/http";
import { getAuthToken } from "../utils/authStorage";
import { Dashboard } from "./Dashboard";
import { AdminManager } from "./AdminManager";
import { Login } from "./Login";

const fetchAdminLoader = async () => {
    try {
        const token = getAuthToken();
        if (!token) {
            console.log("Router: No token found, redirecting to login");
            throw new Error("No token found");
        }
        
        console.log("Router: Validating admin token...");
        const response = await fetch("/admin", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        
        console.log("Router: Admin validation successful");
        return response;
    } catch (error) {
        console.error("Router: Admin loader failed:", error);
        throw error;
    }
};

export const router = createHashRouter([
    {
        path: "/",
        element: <Dashboard />,
        errorElement: <Login />,
        loader: fetchAdminLoader,
    },
    {
        path: "/admin-manager/",
        element: <AdminManager />,
        errorElement: <Login />,
        loader: fetchAdminLoader,
    },
    {
        path: "/login/",
        element: <Login />,
    },
]);
