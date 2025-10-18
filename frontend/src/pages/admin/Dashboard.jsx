import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import applicationsApi from '../../api/applications';
import { getOfficers, getSystemHealth } from '../../api/admin';

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    totalApplications: 0,
    totalOfficers: 0,
    activeOfficers: 0,
    pendingApplications: 0,
    overdueApplications: 0
  });
  
  const [systemHealth, setSystemHealth] = useState({
    status: 'checking',
    components: {
      database: { healthy: null },
      redis: { healthy: null },
      celery: { healthy: null }
    }
  });
  
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAllData = async () => {
      await Promise.all([
        fetchStats(),
        fetchHealthData()
      ]);
      setLoading(false);
    };

    fetchAllData();
    
    // Refresh health every 30 seconds
    const interval = setInterval(fetchHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const applications = await applicationsApi.getAll();
      const apps = Array.isArray(applications) ? applications : [];
      
      const officers = await getOfficers();
      const officersList = Array.isArray(officers) ? officers : [];
      
      setStats({
        totalApplications: apps.length,
        totalOfficers: officersList.length,
        activeOfficers: officersList.filter(o => o.is_active).length,
        pendingApplications: apps.filter(a => a.status === 'submitted').length,
        overdueApplications: apps.filter(a => a.is_overdue).length
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchHealthData = async () => {
    try {
      const health = await getSystemHealth();
      setSystemHealth(health);
    } catch (error) {
      console.error('Error fetching health:', error);
      setSystemHealth({ 
        status: 'error',
        components: {
          database: { healthy: false },
          redis: { healthy: false },
          celery: { healthy: false }
        }
      });
    }
  };

  const getStatusColor = (healthy) => {
    if (healthy === null) return 'bg-gray-100 text-gray-600';
    return healthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
  };

  const getStatusIcon = (healthy) => {
    if (healthy === null) return '⏳';
    return healthy ? '✅' : '❌';
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">System overview and management</p>
      </div>

      {/* System Health Status */}
      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">System Health</h2>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            systemHealth.status === 'healthy' ? 'bg-green-100 text-green-800' :
            systemHealth.status === 'unhealthy' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-600'
          }`}>
            {systemHealth.status === 'checking' ? 'Checking...' : systemHealth.status}
          </span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Database</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(systemHealth.components?.database?.healthy)}`}>
                {getStatusIcon(systemHealth.components?.database?.healthy)} 
                {systemHealth.components?.database?.healthy === null ? 'Checking' : 
                 systemHealth.components?.database?.healthy ? 'Healthy' : 'Down'}
              </span>
            </div>
            {systemHealth.components?.database?.response_time_ms && (
              <p className="text-xs text-gray-500 mt-1">
                {systemHealth.components.database.response_time_ms}ms
              </p>
            )}
          </div>

          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Redis Cache</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(systemHealth.components?.redis?.healthy)}`}>
                {getStatusIcon(systemHealth.components?.redis?.healthy)}
                {systemHealth.components?.redis?.healthy === null ? 'Checking' : 
                 systemHealth.components?.redis?.healthy ? 'Healthy' : 'Down'}
              </span>
            </div>
            {systemHealth.components?.redis?.memory_used && (
              <p className="text-xs text-gray-500 mt-1">
                {systemHealth.components.redis.memory_used}
              </p>
            )}
          </div>

          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Celery Workers</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(systemHealth.components?.celery?.healthy)}`}>
                {getStatusIcon(systemHealth.components?.celery?.healthy)}
                {systemHealth.components?.celery?.healthy === null ? 'Checking' : 
                 systemHealth.components?.celery?.healthy ? 'Healthy' : 'Down'}
              </span>
            </div>
            {systemHealth.components?.celery?.worker_count !== undefined && (
              <p className="text-xs text-gray-500 mt-1">
                {systemHealth.components.celery.worker_count} workers
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Applications</p>
              {loading ? (
                <div className="text-2xl font-bold text-gray-400">...</div>
              ) : (
                <p className="text-3xl font-bold text-gray-900">{stats.totalApplications}</p>
              )}
            </div>
            <div className="text-4xl">📋</div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Active Officers</p>
              {loading ? (
                <div className="text-2xl font-bold text-gray-400">...</div>
              ) : (
                <p className="text-3xl font-bold text-green-600">
                  {stats.activeOfficers}/{stats.totalOfficers}
                </p>
              )}
            </div>
            <div className="text-4xl">👥</div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Pending Applications</p>
              {loading ? (
                <div className="text-2xl font-bold text-gray-400">...</div>
              ) : (
                <p className="text-3xl font-bold text-yellow-600">{stats.pendingApplications}</p>
              )}
            </div>
            <div className="text-4xl">⏳</div>
          </div>
        </div>
      </div>

      {/* Overdue Alert */}
      {!loading && stats.overdueApplications > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-8">
          <div className="flex items-center">
            <span className="text-2xl mr-3">⚠️</span>
            <div>
              <p className="font-semibold text-orange-900">
                {stats.overdueApplications} Overdue Applications
              </p>
              <p className="text-sm text-orange-700">These applications require immediate attention</p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Officer Management</h2>
          <div className="space-y-3">
            <Link 
              to="/admin/officers/new" 
              className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Add New Officer</p>
                  <p className="text-sm text-gray-600">Create officer account</p>
                </div>
                <span className="text-2xl">➕</span>
              </div>
            </Link>
            
            <Link 
              to="/admin/officers" 
              className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Manage Officers</p>
                  <p className="text-sm text-gray-600">View and edit officer accounts</p>
                </div>
                <span className="text-2xl">👥</span>
              </div>
            </Link>
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">System Management</h2>
          <div className="space-y-3">
            <Link 
              to="/admin/appointments" 
              className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Appointment Settings</p>
                  <p className="text-sm text-gray-600">Configure appointment slots</p>
                </div>
                <span className="text-2xl">📅</span>
              </div>
            </Link>
            
            <Link 
              to="/officer/queue" 
              className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Application Queue</p>
                  <p className="text-sm text-gray-600">View all pending applications</p>
                </div>
                <span className="text-2xl">📋</span>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}