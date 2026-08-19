import React from "react";
import {
  UsersIcon,
  BriefcaseIcon,
  WrenchScrewdriverIcon,
  ShieldCheckIcon,
  ArchiveBoxIcon,
  ChartBarSquareIcon,
  ClockIcon,
  ChevronRightIcon,
  EllipsisHorizontalIcon,
  CogIcon,
  WrenchIcon,
  UserIcon
} from "@heroicons/react/24/outline";
import { useState, useEffect } from "react";
import api from "../../api";

// 1️⃣ CONFIGURATION: Map Types to Icons & Colors
const CATEGORY_CONFIG = {
  user: {
    icon: UsersIcon,
    color: "text-indigo-600",
    bg: "bg-indigo-50",
    border: "border-indigo-100"
  },
  equipment: {
    icon: BriefcaseIcon,
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-100"
  },
  project: {
    icon: WrenchScrewdriverIcon,
    color: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-100"
  },
  safety: {
    icon: ShieldCheckIcon,
    color: "text-red-600",
    bg: "bg-red-50",
    border: "border-red-100"
  },
  inventory: {
    icon: ArchiveBoxIcon,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
    border: "border-emerald-100"
  },
  production: {
    icon: ChartBarSquareIcon,
    color: "text-purple-600",
    bg: "bg-purple-50",
    border: "border-purple-100"
  },
  operation: {
    icon: CogIcon,
    color: "text-cyan-600",
    bg: "bg-cyan-50",
    border: "border-cyan-100"
  },
  maintenance: {
    icon: WrenchIcon,
    color: "text-orange-600",
    bg: "bg-orange-50",
    border: "border-orange-100"
  },
  employee: {
    icon: UserIcon,
    color: "text-violet-600",
    bg: "bg-violet-50",
    border: "border-violet-100"
  },
};

// 2️⃣ HELPER: Relative Time Formatter (No External Libs)
const getRelativeTime = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return "just now";
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes} min ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? "s" : ""} ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? "s" : ""} ago`;

  return date.toLocaleDateString(); // Fallback for older dates
};

export default function RecentActivity() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        const response = await api.get("/dashboard/activity/recent/");

        const rawActivities = Array.isArray(response.data)
          ? response.data
          : (response.data?.results || []);

        const mappedActivities = rawActivities
          .map(item => {
            const actionStr = item.action ? (item.action.charAt(0).toUpperCase() + item.action.slice(1)) : '';
            let cleanUser = item.user ? item.user.trim() : "System";
            if (cleanUser.startsWith("(") && cleanUser.endsWith(")")) {
              cleanUser = cleanUser.slice(1, -1);
            }

            // Resolve the category key to use in CATEGORY_CONFIG
            // 'projects' → 'project', 'production' stays 'production'
            let typeKey = item.app_name ? item.app_name.toLowerCase() : 'project';
            if (typeKey === 'projects') typeKey = 'project';
            // Map model_name to a more specific type key if available
            if (item.model_name === 'Operation Record') typeKey = 'production';
            if (item.model_name === 'Maintenance Record') typeKey = 'production';
            if (item.model_name === 'Employee') typeKey = 'user';

            return {
              id: item.id,
              type: typeKey,
              title: `${item.model_name || 'System'} ${actionStr}`.trim(),
              description: item.description || "No details provided.",
              time: getRelativeTime(item.created_at),
              user: cleanUser,
              raw_id: item.id,
              created_at: item.created_at
            };
          })
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        setActivities(mappedActivities);
      } catch (err) {
        console.error("❌ Failed to fetch recent activity:", err);
        const serverMsg = err.response?.data && typeof err.response.data === 'string'
          ? err.response.data
          : (err.message || "Unknown Error");
        setError(`Failed to load activities: ${serverMsg.substring(0, 100)}`);
      } finally {
        setLoading(false);
      }
    };

    fetchActivities();
  }, []);

  if (loading) {
    return (
      <div className="w-full h-full flex justify-center items-center bg-gray-50 py-4">
        <div className="w-full max-w-7xl mx-auto h-[400px] flex justify-center items-center bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="animate-pulse flex flex-col items-center">
            <div className="h-4 w-4 bg-gray-200 rounded-full mb-2"></div>
            <div className="h-2 w-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full h-full flex justify-center items-center bg-gray-50 py-4">
        <div className="w-full max-w-7xl mx-auto h-[400px] flex justify-center items-center bg-white rounded-xl shadow-sm border border-gray-200">
          <p className="text-red-500 text-sm font-semibold">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex justify-center items-center bg-gray-50 py-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 w-full max-w-7xl mx-auto h-[400px] flex flex-col">

        {/* Header - Fixed */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <ClockIcon className="h-5 w-5 text-gray-400" />
            <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Recent Activity</h3>
          </div>
          <button className="p-1 hover:bg-gray-100 rounded-full text-black hover:text-blue-700 transition-colors">
            <EllipsisHorizontalIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Activity List - Scrollable */}
        <div className="flex-1 overflow-y-auto scroll-smooth custom-scrollbar p-0">
          {activities.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <p className="text-sm">No recent activity</p>
            </div>
          ) : (
            activities.map((activity, index) => {
              // Fallback config if type doesn't match
              const config = CATEGORY_CONFIG[activity.type] || CATEGORY_CONFIG.project;
              const Icon = config.icon;

              return (
                <div
                  key={activity.id}
                  className="group flex items-start gap-4 px-6 py-4 hover:bg-gray-50 border hover:border-blue-700 transition-colors border-b border-gray-50 last:border-0 cursor-pointer relative"
                >
                  {/* Visual Connector Line (Timeline Effect) */}
                  {index !== activities.length - 1 && (
                    <span className="absolute left-[35px] top-10 bottom-0 w-px bg-gray-100 group-hover:bg-gray-200 transition-colors" />
                  )}

                  {/* Icon Container */}
                  <div className={`relative z-10 flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${config.bg} border ${config.border}`}>
                    <Icon className={`h-4 w-4 ${config.color}`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <p className="text-xs font-semibold text-gray-900 truncate pr-2 capitalize">
                        {activity.title}
                      </p>
                      <span className="text-[10px] text-gray-600 whitespace-nowrap bg-gray-50 px-2 py-0.5 rounded-full border border-gray-100">
                        {activity.time}
                      </span>
                    </div>

                    <p className="text-xs font-semibold text-gray-700 mt-0.5 line-clamp-2">
                      {activity.description}
                    </p>

                    <p className="text-[10px] text-black mt-2 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-300 group-hover:bg-blue-400 transition-colors"></span>
                      by {activity.user}
                    </p>
                  </div>

                  {/* Hover Action Arrow */}
                  <div className="self-center opacity-0 group-hover:opacity-100 transition-opacity -translate-x-2 group-hover:translate-x-0 duration-200">
                    <ChevronRightIcon className="h-4 w-4 text-blue-700" />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer (Optional) */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 rounded-b-xl text-center">
          <button className="text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline">
            View All History
          </button>
        </div>

      </div>
    </div>
  );
}