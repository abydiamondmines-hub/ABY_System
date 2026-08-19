import React from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { ShieldExclamationIcon } from "@heroicons/react/24/outline";

export default function Unauthorized() {
    const navigate = useNavigate();
    const context = useOutletContext();
    const { user, roles, appPermissions } = context || {};

    const handleHomeClick = () => {
        if (!user || !roles || !appPermissions) {
            navigate("/");
            return;
        }

        const userRoleId = typeof user?.role === 'object' ? user?.role?.id : user?.role;
        const userRole = roles?.find(r => r.id === userRoleId);
        const userPermIds = userRole?.permissions || [];
        const isSuperuser = Boolean(user.superuser || user.is_superuser || user.is_staff);
        const roleName = userRole?.name?.toLowerCase() || (typeof user?.role === 'string' ? user.role.toLowerCase() : '');
        const isAdmin = isSuperuser || roleName.includes('admin');

        // Check each app in order of standard navigation priority
        const order = [
            { path: '/dashboard', app: 'dashboard' },
            { path: '/project', app: 'projects' },
            { path: '/equipment', app: 'equipment' },
            { path: '/safety', app: 'safety' },
            { path: '/inventory', app: 'inventory' },
            { path: '/production', app: 'production' },
            { path: '/users', app: 'users' }
        ];

        for (const item of order) {
            if (isSuperuser || isAdmin) {
                navigate(item.path);
                return;
            }

            if (item.app === 'dashboard') {
                const allPerms = Object.values(appPermissions).flat();
                const dashPerm = allPerms.find(p => p.codename === 'view_dashboardaccess');
                if (dashPerm && userPermIds.includes(dashPerm.id)) {
                    navigate(item.path);
                    return;
                }
            } else if (item.app === 'users') {
                const allPerms = Object.values(appPermissions).flat();
                const allowedCodenames = ['view_customuser', 'view_role', 'view_rolemodulepermission'];
                const usersPerms = allPerms.filter(p => allowedCodenames.includes(p.codename));
                if (usersPerms.some(p => userPermIds.includes(p.id))) {
                    navigate(item.path);
                    return;
                }
            } else {
                const modulePerms = appPermissions?.[item.app] || [];
                if (modulePerms.some(perm => userPermIds.includes(perm.id))) {
                    navigate(item.path);
                    return;
                }
            }
        }

        // Fallback
        navigate("/");
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center">
            <div className="bg-red-50 p-4 rounded-full mb-6">
                <ShieldExclamationIcon className="w-16 h-16 text-red-500" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Access Denied</h1>
            <p className="text-gray-600 max-w-md mb-8">
                You do not have the required permissions to view this page or perform this action. 
                If you believe this is a mistake, please contact your administrator.
            </p>
            <button
                onClick={() => navigate(-2)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors mr-3"
            >
                Go Back
            </button>
            <button
                onClick={handleHomeClick}
                className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
                Home
            </button>
        </div>
    );
}
