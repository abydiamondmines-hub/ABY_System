import { useState, useEffect } from "react";
import {
  Briefcase, Truck, Users, Archive, ShieldCheck,
  Factory, Save, RotateCcw, Loader2, CheckCircle, XCircle,
  ChevronDown, ChevronUp
} from "lucide-react";
import api from "../../api";

export default function RolesAndPermissions() {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [selectedRoleId, setSelectedRoleId] = useState(null);
  const [editedRolePermissions, setEditedRolePermissions] = useState([]); // IDs of permissions for selected role
  const [editedDefaultRoute, setEditedDefaultRoute] = useState("/dashboard");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState({}); // Track expanded accordions

  const toggleGroupExpansion = (groupName) => {
    setExpandedGroups(prev => ({ ...prev, [groupName]: !prev[groupName] }));
  };

  const handleToggleGroupAll = (groupPermIds, isChecked) => {
    if (isChecked) {
      setEditedRolePermissions(prev => Array.from(new Set([...prev, ...groupPermIds])));
    } else {
      setEditedRolePermissions(prev => prev.filter(id => !groupPermIds.includes(id)));
    }
  };

  // ────────────────────────────────
  // 1️⃣ Fetch Data
  // ────────────────────────────────
  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        // Define the apps we need permissions for
        const apps = [
          'users',       // → User Management, Employees, Roles
          'projects',    // → Projects
          'equipment',   // → Equipment
          'inventory',   // → Inventory
          'safety',      // → Risk Assessment, Safety Incidents
          'production',  // → Operations, Maintenance, Daily Production
          'operations',  // → OperationRecord, MaintenanceRecord
        ];

        // Fetch roles and all app permissions in parallel
        const [rolesRes, ...permsResList] = await Promise.all([
          api.get("/users/roles/"),
          ...apps.map(app => api.get(`/users/permissions/${app}/`).catch(e => ({ data: [] })))
        ]);

        const rolesDataRaw = Array.isArray(rolesRes.data) ? rolesRes.data : (rolesRes.data.results || []);

        // Basic role info mapping with fallback permissions parsing
        const rolesData = rolesDataRaw.map(r => {
          const rawPerms1 = r.role_permissions || [];
          const rawPerms2 = r.rolemodulepermissions || [];
          const rawPerms3 = r.rolemodulepermission_set || [];
          const rawPerms4 = r.role_module_permissions || [];
          const rawPerms5 = r.module_permissions || [];
          const rawPerms6 = r.permissions || [];
          const combined = [...rawPerms1, ...rawPerms2, ...rawPerms3, ...rawPerms4, ...rawPerms5, ...rawPerms6];
          const parsedPermIds = Array.from(new Set(combined.map(p => {
              let val = typeof p === 'object' && p !== null ? (p.permission || p.permission_id || p.id || p.access_level) : p;
              return Number(val);
          }).filter(id => !isNaN(id) && id !== 0 && id !== null)));

          return {
            ...r,
            id: r.id ?? r.key,
            name: r.name ?? r.label,
            default_route: r.default_route || '/dashboard',
            permissions: parsedPermIds
          };
        });

        const permsData = permsResList.flatMap((res, index) => {
          const rawData = Array.isArray(res.data) ? res.data : (res.data.results || []);
          return rawData
            .filter(p => !p.codename.endsWith('_safety')) // Remove stale permissions
            .map(p => ({ ...p, moduleName: apps[index] }));
        });

        setRoles(rolesData);
        setPermissions(permsData);

        // Select first role by default
        if (rolesData.length > 0) {
          const initialRoleId = rolesData[0].id;
          setSelectedRoleId(initialRoleId);
          await fetchRolePermissions(initialRoleId, rolesData);
        }

      } catch (error) {
        console.error("Failed to fetch data", error);
        alert("Failed to load roles and permissions.");
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  const fetchRolePermissions = async (roleId, currentRoles = roles) => {
    try {
      const res = await api.get(`/users/roles/${roleId}/`);
      const data = res.data;
      const dbPermissions = data.permissions || [];
      const permIds = dbPermissions.map(p => {
        if (typeof p === 'object' && p !== null) {
          return p.permission || p.id || p.permission_id;
        }
        return p;
      });
      setEditedRolePermissions(permIds.filter(id => id != null).map(Number));
      if (data.default_route) {
        setEditedDefaultRoute(data.default_route);
      } else {
        const fallbackRole = currentRoles.find(r => r.id === roleId);
        setEditedDefaultRoute(fallbackRole?.default_route || "/dashboard");
      }
    } catch (error) {
      console.error(`Failed to fetch permissions for role ${roleId} (likely backend 404). Falling back to cached list.`, error);
      // Fallback: if the detailed route fails, grab from the main list so we don't end up empty
      const fallbackRole = currentRoles.find(r => r.id === roleId);
      if (fallbackRole && fallbackRole.permissions) {
        setEditedRolePermissions(fallbackRole.permissions);
      }
      if (fallbackRole && fallbackRole.default_route) {
        setEditedDefaultRoute(fallbackRole.default_route);
      }
    }
  };

  // Sync state when switching roles
  const handleRoleSelect = async (roleId) => {
    setSelectedRoleId(roleId);
    setEditedRolePermissions([]); // clear temporarily while loading
    await fetchRolePermissions(roleId);
  };

  // ────────────────────────────────
  // 2️⃣ Logic
  // ────────────────────────────────

  const handleTogglePermission = (permId) => {
    setEditedRolePermissions(prev => {
      if (prev.includes(permId)) {
        return prev.filter(id => id !== permId);
      } else {
        return [...prev, permId];
      }
    });
  };

  const handleSave = async () => {
    if (selectedRoleId === null || selectedRoleId === undefined) {
      alert("Please select a role first.");
      return;
    }

    setSaving(true);
    let targetIdForLogs = selectedRoleId;
    try {
      const role = roles.find(r => r.id === selectedRoleId);

      if (!role) {
        throw new Error(`Role with ID ${selectedRoleId} not found in local state.`);
      }

      let targetId = selectedRoleId;

      // 🕵️ Fallback ID Resolution
      try {
        const detailRes = await api.get(`/users/roles/${selectedRoleId}/`);
        const detailData = detailRes.data;
        
        if (detailData.id && detailData.id !== selectedRoleId) {
          targetId = detailData.id;
        } else if (detailData.group_id) {
          targetId = detailData.group_id;
        }
      } catch (lookupErr) {
        console.warn("⚠️ Could not fetch role details. Will attempt to use original ID.", lookupErr);
      }
      
      targetIdForLogs = targetId;

      const visiblePermIds = new Set(permissions.map(p => Number(p.id)));
      const cleanPermissionsPayload = editedRolePermissions.filter(id => visiblePermIds.has(Number(id)));

      const payload = {
        name: role.name, // Keep existing name
        default_route: editedDefaultRoute,
        permissions: cleanPermissionsPayload // Send list of IDs to match backend ManyToMany field
      };
      // PUT /api/users/roles/<id>/
      await api.put(`/users/roles/${targetId}/`, payload);

      // Optimistically update the roles cache so the fallback works if GET 404s
      const updatedRoles = roles.map(r =>
        r.id === targetId ? { ...r, default_route: editedDefaultRoute, permissions: cleanPermissionsPayload } : r
      );
      setRoles(updatedRoles);

      // 🔍 VERIFICATION LOG: Re-fetch the detailed role to hydrate checkboxes
      await fetchRolePermissions(targetId, updatedRoles);

      alert("Role updated successfully.");
    } catch (error) {
      console.error("❌ Save failed:", error);
      const urlTried = `/api/users/roles/${targetIdForLogs}/`;
      const errMsg = error.response ? JSON.stringify(error.response.data) : error.message;
      alert(`Backend rejected it!
      
Attempted: PUT ${urlTried}
Status: ${error.response?.status}
Response Message: ${errMsg}

This 404 means the backend Django server literally could not find the role ID ${targetIdForLogs} in its database. 

Please show this EXACT alert to your backend partner. If they built "update/", then either their code is not deployed/running on this URL, or Role ${targetIdForLogs} doesn't actually exist in the DB.`);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (selectedRoleId !== null) {
      fetchRolePermissions(selectedRoleId);
    }
  };

  // Group Permissions by 'content_type' or 'app_label' inferred from codename or provided field
  // Assuming structure has 'codename', 'name', 'id'
  // We'll try to guess groupings or just list them all. 
  // Better: Extract the first word of codename or use a known list if available.
  // Actually, standard Django permissions usually have `content_type` ID. 
  // We'll group by a simple heuristic if 'app_label' isn't explicitly there.

  const GROUP_MAPPING = {
    // Users app
    'Customuser': 'Roles & System Access',
    'Role': 'Roles & System Access',
    'Rolemodulepermission': 'Permissions',
    'Dashboardaccess': 'Dashboard',

    // Production app
    'Dailyproduction': 'Daily Production',
    'Operationrecord': 'Operations Table',
    'Maintenancerecord': 'Maintenance Table',

    // Safety app
    'Safetyincident': 'Safety Incidents',
    'Riskassessment': 'Risk Assessment',

    // Other apps
    'Project': 'Projects',
    'Equipment': 'Equipment',
    'Inventory': 'Inventory',
  };

  const groupedPermissions = permissions.reduce((acc, perm) => {
    // Try to find a group name. E.g. "auth | user" or just "user" from "add_user"
    // Heuristic: Use the last word of codename (usually the model)
    const parts = perm.codename.split('_');
    const groupRaw = parts.length > 1 ? parts.slice(1).join(' ') : 'Other';
    // capitalize
    const groupKey = groupRaw.charAt(0).toUpperCase() + groupRaw.slice(1).replace(/\s/g, '');

    // Use mapping or fallback to capitalized raw string
    const groupName = GROUP_MAPPING[groupKey] || (groupRaw.charAt(0).toUpperCase() + groupRaw.slice(1));

    if (!acc[groupName]) acc[groupName] = [];
    acc[groupName].push(perm);
    return acc;
  }, {});


  // Helper to format codename to clean name
  const formatPermissionName = (codename) => {
    // Map of specific keyword replacements
    const REPLACEMENTS = {
      'customuser': 'User',
      'rolemodulepermission': 'Role Permission',
      'role': 'Role',
      'dashboardaccess': 'Dashboard',
      'operationrecord': 'Operation',
      'maintenancerecord': 'Maintenance',
      'safetyincident': 'Safety Incident',
      'riskassessment': 'Risk Assessment',
      'dailyproduction': 'Daily Production',
      'add': 'Add',
      'change': 'Edit',
      'delete': 'Delete',
      'view': 'View'
    };

    return codename.split('_')
      .map(part => REPLACEMENTS[part] || part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  };

  if (loading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin h-8 w-8 text-blue-600" /></div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden w-full h-full flex flex-col md:flex-row">

      {/* 👈 SIDEBAR: ROLES LIST */}
      <div className="w-full md:w-64 bg-gray-50 border-r border-gray-100 flex-shrink-0 flex flex-col">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-bold text-gray-800">Roles</h3>
          <p className="text-xs text-gray-500">Select a role to edit</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {roles.map(role => (
            <button
              key={role.id}
              onClick={() => handleRoleSelect(role.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${selectedRoleId === role.id
                ? "bg-white shadow-sm text-blue-600 border border-gray-200"
                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
            >
              {role.name}
            </button>
          ))}
        </div>
      </div>

      {/* 👉 MAIN: PERMISSIONS MATRIX */}
      <div className="flex-1 flex flex-col min-h-[400px]">

        {/* Header */}
        <div className="p-4 border-b border-gray-100 flex flex-wrap gap-4 justify-between items-center bg-white sticky top-0 z-10">
          <div>
            <h2 className="text-base font-bold text-gray-900">
              Editing: <span className="text-blue-600">{roles.find(r => r.id === selectedRoleId)?.name}</span>
            </h2>
            <p className="text-xs text-gray-500">
              {editedRolePermissions.length} permissions enabled
            </p>
          </div>

          {/* Default Landing Route Selector */}
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-gray-700 whitespace-nowrap">Default Route:</label>
            <select
              value={editedDefaultRoute}
              onChange={(e) => setEditedDefaultRoute(e.target.value)}
              className="text-xs border border-gray-300 rounded-lg px-2.5 py-1.5 bg-white text-gray-800 font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none shadow-sm cursor-pointer"
            >
              <option value="/dashboard">Admin Dashboard (/dashboard)</option>
              <option value="/equipment">Equipment Management (/equipment)</option>
              <option value="/project">Project Management (/project)</option>
              <option value="/safety">Safety Management (/safety)</option>
              <option value="/inventory">Inventory Management (/inventory)</option>
              <option value="/production">Production (/production)</option>
              <option value="/users">User Management (/users)</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleReset}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <RotateCcw className="w-3 h-3 inline mr-1" /> Reset
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-1.5 text-xs font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm transition-all flex items-center gap-1 disabled:opacity-70"
            >
              {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
              Save
            </button>
          </div>
        </div>

        {/* Permissions Grid */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-white">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">

            {Object.keys(groupedPermissions).sort().map(group => {
              const groupPerms = groupedPermissions[group];
              const groupPermIds = groupPerms.map(p => p.id);
              const isAllChecked = groupPermIds.every(id => editedRolePermissions.includes(id));
              const isExpanded = expandedGroups[group];

              return (
                <div key={group} className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                  {/* Group Header (Accordion Toggle + Select All) */}
                  <div className="flex items-center justify-between bg-white px-4 py-3 border-b border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="relative flex items-center">
                        <input
                          type="checkbox"
                          checked={isAllChecked}
                          onChange={(e) => handleToggleGroupAll(groupPermIds, e.target.checked)}
                          className="peer h-4 w-4 appearance-none rounded border border-gray-300 bg-white checked:bg-blue-600 checked:border-blue-600 focus:ring-2 focus:ring-blue-100 transition-all cursor-pointer"
                        />
                        <CheckCircle className="absolute w-4 h-4 text-white opacity-0 peer-checked:opacity-100 pointer-events-none p-0.5" />
                      </div>
                      <h4 
                        className="font-bold text-gray-800 text-sm capitalize cursor-pointer select-none line-clamp-1" 
                        onClick={() => toggleGroupExpansion(group)}
                      >
                        {group} <span className="text-gray-400 font-normal text-xs ml-1">({groupPerms.length})</span>
                      </h4>
                    </div>
                    <button 
                      onClick={() => toggleGroupExpansion(group)}
                      className="p-1.5 flex-shrink-0 bg-gray-50 rounded-md text-gray-400 hover:bg-gray-200 hover:text-gray-700 transition-colors"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Group Content (Items) */}
                  {isExpanded && (
                    <div className="p-4 space-y-2 bg-gray-50">
                      {groupPerms.map(perm => {
                        const isChecked = editedRolePermissions.includes(perm.id);
                        return (
                          <label
                            key={perm.id}
                            className={`flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors ${isChecked ? "bg-white shadow-sm border border-blue-100" : "hover:bg-gray-200/50"
                              }`}
                          >
                            <div className="relative flex items-center mt-0.5">
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => handleTogglePermission(perm.id)}
                                className="peer h-4 w-4 appearance-none rounded border border-gray-300 bg-white checked:bg-blue-600 checked:border-blue-600 focus:ring-2 focus:ring-blue-100 transition-all cursor-pointer"
                              />
                              <CheckCircle className="absolute w-4 h-4 text-white opacity-0 peer-checked:opacity-100 pointer-events-none p-0.5" />
                            </div>
                            <div className="flex-1">
                              <p className={`text-xs font-medium ${isChecked ? "text-gray-900" : "text-gray-600"}`}>
                                {formatPermissionName(perm.codename)}
                              </p>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}

          </div>
        </div>

      </div>
    </div>
  );
}