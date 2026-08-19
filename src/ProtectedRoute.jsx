import React from "react";
import { Navigate, useOutletContext } from "react-router-dom";

const ProtectedRoute = ({ children, app }) => {
  const token = localStorage.getItem("access_token") || localStorage.getItem("token");

  // If no token, redirect to login
  if (!token) {
    return <Navigate to="/" replace />;
  }

  const context = useOutletContext();

  // If no context yet (e.g. Layout is still fetching), we just render children 
  // or return null/loading. To prevent flicker, Layout handles loading state globally.
  if (context && app) {
    const { user: contextUser, roles, appPermissions, loadingAuth } = context;

    // Grab user from context or fallback to localStorage
    let user = contextUser;
    if (!user) {
      try {
        const saved = localStorage.getItem("user");
        if (saved) user = JSON.parse(saved);
      } catch {}
    }

    // Wait for authentication checks to finish before deciding to kick the user out
    if (loadingAuth && !user) {
      return (
        <div className="flex justify-center items-center h-full min-h-[50vh]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!user && !loadingAuth) return <Navigate to="/" replace />;
    if (!user) return children;

    const userRoleId = typeof user?.role === 'object' ? user?.role?.id : user?.role;
    const userRole = roles?.find(r => r.id === userRoleId);
    const roleName = userRole?.name?.toLowerCase() || (typeof user?.role === 'string' ? user.role.toLowerCase() : '');
    const isSuperuser = Boolean(user.superuser || user.is_superuser || user.is_staff);
    const isAdmin = isSuperuser || roleName.includes('admin');

    // Superusers & Admins have full access to ALL pages (including users and dashboard)
    if (isAdmin || isSuperuser) return children;

    const userPermIds = userRole?.permissions || [];
    const allPerms = Object.values(appPermissions || {}).flat();

    let hasAccess = false;

    if (app === 'dashboard') {
      // Dashboard: check for specific view_dashboardaccess permission
      const dashPerm = allPerms.find(p => p.codename === 'view_dashboardaccess');
      if (dashPerm) {
        hasAccess = userPermIds.includes(dashPerm.id);
      }
    } else if (app === 'users') {
      // User Management: check for specific view_customuser, view_role, or view_rolemodulepermission permission
      const allowedCodenames = ['view_customuser', 'view_role', 'view_rolemodulepermission'];
      const usersPerms = allPerms.filter(p => allowedCodenames.includes(p.codename));
      hasAccess = usersPerms.some(p => userPermIds.includes(p.id));
    } else {
      const modulePerms = appPermissions?.[app] || [];
      hasAccess = modulePerms.some(perm => userPermIds.includes(perm.id));
    }

    if (!hasAccess && !loadingAuth) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  // Otherwise, render the protected page
  return children;
};

export default ProtectedRoute;
