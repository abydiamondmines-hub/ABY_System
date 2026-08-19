import { useLocation, Link } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';
import {
    UsersIcon,
    BriefcaseIcon,
    WrenchScrewdriverIcon,
    ShieldCheckIcon,
    ArchiveBoxIcon,
    ChartBarSquareIcon,
    Squares2X2Icon
} from '@heroicons/react/24/solid';
import logo from "/assets/ABY.png";

function classNames(...classes) {
    return classes.filter(Boolean).join(' ')
}

export default function Sidebar({ sidebarOpen, setSidebarOpen, user, roles, appPermissions }) {
    const location = useLocation();

    const navigation = [
        { name: 'Dashboard', href: '/dashboard', icon: Squares2X2Icon, app: 'dashboard' },
        { name: 'User Management', href: '/users', icon: UsersIcon, app: 'users' },
        { name: 'Equipment Management', href: '/equipment', icon: BriefcaseIcon, app: 'equipment' },
        { name: 'Project Management', href: '/project', icon: WrenchScrewdriverIcon, app: 'projects' },
        { name: 'Safety Management', href: '/safety', icon: ShieldCheckIcon, app: 'safety' },
        { name: 'Inventory Management', href: '/inventory', icon: ArchiveBoxIcon, app: 'inventory' },
        { name: 'Production', href: '/production', icon: ChartBarSquareIcon, app: 'production' },
    ];

    const userRoleId = typeof user?.role === 'object' ? user?.role?.id : user?.role;
    const userRole = roles?.find(r => r.id === userRoleId);
    const userPermIds = userRole?.permissions || [];

    const hasAccess = (itemApp) => {
        if (!user) return false;
        const isSuperuser = Boolean(user.superuser || user.is_superuser || user.is_staff);
        const roleName = userRole?.name?.toLowerCase() || (typeof user?.role === 'string' ? user.role.toLowerCase() : '');
        const isAdmin = isSuperuser || roleName.includes('admin');

        // Superusers and Admins have global access to all sidebar links
        if (isAdmin || isSuperuser) return true;

        const allPerms = Object.values(appPermissions).flat();

        // Dashboard specific check
        if (itemApp === 'dashboard') {
            const dashPerm = allPerms.find(p => p.codename === 'view_dashboardaccess');
            if (dashPerm) {
                return userPermIds.includes(dashPerm.id);
            }
            return false; // If there's no dashPerm defined, fallback to false for safety
        }

        // User Management specific check (must have permission to view customuser, role, or rolemodulepermission)
        if (itemApp === 'users') {
            const allowedCodenames = ['view_customuser', 'view_role', 'view_rolemodulepermission'];
            const usersPerms = allPerms.filter(p => allowedCodenames.includes(p.codename));
            return usersPerms.some(p => userPermIds.includes(p.id));
        }

        // Feature modules dynamic check
        const permissionModule = itemApp === 'dashboard' ? 'users' : itemApp;
        const modulePerms = appPermissions?.[permissionModule] || [];

        return modulePerms.some(perm => userPermIds.includes(perm.id));
    };

    const allowedNavigation = navigation.filter(item => hasAccess(item.app));

    return (
        <div className="flex relative font-sans h-screen">
            <div
                className={`fixed top-0 left-0 h-screen w-55 bg-white transform transition-transform duration-300 ease-in-out shadow-md z-50 flex flex-col ${sidebarOpen ? "translate-x-0" : "-translate-x-full"
                    }`}
            >
                {/* Container for content with internal padding */}
                <div className="px-3 py-6 h-full overflow-y-auto relative">

                    {/* Close button - Visible on Mobile AND Desktop now */}
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="absolute top-4 right-4 p-1 text-gray-500 hover:text-gray-800 transition-colors z-50"
                        title="Close Sidebar"
                    >
                        <XMarkIcon className="h-6 w-6" />
                    </button>

                    {/* Header with logo */}
                    <div className="flex flex-col items-center pt-2">
                        <img
                            src={logo}
                            alt="Logo"
                            className="h-35 w-35 object-contain"
                        />
                    </div>

                    {/* Navigation links */}
                    <nav className="space-y-1">
                        {allowedNavigation.map((item) => {
                            const isActive = location.pathname.startsWith(item.href);
                            return (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className={classNames(
                                        isActive
                                            ? "bg-blue-700 text-white shadow-sm"
                                            : "text-gray-600 hover:bg-gray-50 hover:text-blue-700",
                                        "group flex items-center gap-3 px-3 py-3 text-sm font-medium rounded-lg transition-all duration-200"
                                    )}
                                >
                                    <item.icon
                                        className={classNames(
                                            isActive ? "text-white" : "text-gray-400 group-hover:text-blue-700",
                                            "h-5 w-5 flex-shrink-0"
                                        )}
                                    />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>
                </div>
            </div>
        </div>
    )
}
