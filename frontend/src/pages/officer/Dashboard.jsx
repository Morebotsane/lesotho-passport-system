import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import applicationsApi from '../../api/applications';

export default function OfficerDashboard() {
  const [stats, setStats] = useState({
    total: 0,
    submitted: 0,
    under_review: 0,
    processing: 0,
    overdue: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

const fetchStats = async () => {
  try {
    const applications = await applicationsApi.getAll();  // This should return an array
    console.log('Dashboard applications:', applications); // Debug
    
    // Ensure we have an array
    const apps = Array.isArray(applications) ? applications : [];
    
    const total = apps.length;
    const submitted = apps.filter(app => app.status === 'submitted').length;
    const underReview = apps.filter(app => app.status === 'under_review').length;
    const processing = apps.filter(app => 
      ['processing', 'quality_check', 'documents_required'].includes(app.status)
    ).length;
    const overdue = apps.filter(app => app.is_overdue).length;
    
    setStats({ total, submitted, under_review: underReview, processing, overdue });
  } catch (error) {
    console.error('Error fetching stats:', error);
  } finally {
    setLoading(false);
  }
};

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Officer Dashboard</h1>
        <p className="text-gray-600 mt-2">Process and manage passport applications</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card p-6">
          <div className="text-3xl mb-2">📋</div>
          <p className="text-gray-600 text-sm">Total Applications</p>
          {loading ? (
            <div className="text-2xl font-bold text-gray-400">...</div>
          ) : (
            <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
          )}
        </div>

        <div className="card p-6">
          <div className="text-3xl mb-2">📥</div>
          <p className="text-gray-600 text-sm">Submitted</p>
          {loading ? (
            <div className="text-2xl font-bold text-gray-400">...</div>
          ) : (
            <p className="text-2xl font-bold text-blue-600">{stats.submitted}</p>
          )}
        </div>

        <div className="card p-6">
          <div className="text-3xl mb-2">⏳</div>
          <p className="text-gray-600 text-sm">In Progress</p>
          {loading ? (
            <div className="text-2xl font-bold text-gray-400">...</div>
          ) : (
            <p className="text-2xl font-bold text-yellow-600">
              {stats.under_review + stats.processing}
            </p>
          )}
        </div>

        <div className="card p-6">
          <div className="text-3xl mb-2">🚨</div>
          <p className="text-gray-600 text-sm">Overdue</p>
          {loading ? (
            <div className="text-2xl font-bold text-gray-400">...</div>
          ) : (
            <p className="text-2xl font-bold text-red-600">{stats.overdue}</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="space-y-3">
          <Link 
            to="/officer/queue?filter=submitted" 
            className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Process New Applications</p>
                <p className="text-sm text-gray-600">
                  Review newly submitted applications
                  {!loading && stats.submitted > 0 && (
                    <span className="ml-2 px-2 py-0.5 bg-blue-600 text-white text-xs rounded-full">
                      {stats.submitted}
                    </span>
                  )}
                </p>
              </div>
              <span className="text-2xl">→</span>
            </div>
          </Link>

          <Link 
            to="/officer/queue?filter=overdue" 
            className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Handle Overdue Applications</p>
                <p className="text-sm text-gray-600">
                  Applications requiring urgent attention
                  {!loading && stats.overdue > 0 && (
                    <span className="ml-2 px-2 py-0.5 bg-red-600 text-white text-xs rounded-full">
                      {stats.overdue}
                    </span>
                  )}
                </p>
              </div>
              <span className="text-2xl">→</span>
            </div>
          </Link>

          <Link 
            to="/officer/queue" 
            className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">View All Applications</p>
                <p className="text-sm text-gray-600">Browse and filter all applications</p>
              </div>
              <span className="text-2xl">→</span>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}