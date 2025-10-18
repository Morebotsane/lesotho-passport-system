import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import applicationsApi from '../../api/applications';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    total: 0,
    submitted: 0,
    under_review: 0,
    processing: 0,
    ready_for_pickup: 0,
    collected: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const applications = await applicationsApi.getMyApplications();
      
      // Calculate statistics
      const total = applications.length;
      const submitted = applications.filter(app => app.status === 'submitted').length;
      const underReview = applications.filter(app => app.status === 'under_review').length;
      const processing = applications.filter(app => 
        ['processing', 'quality_check', 'documents_required'].includes(app.status)
      ).length;
      const readyForPickup = applications.filter(app => app.status === 'ready_for_pickup').length;
      const collected = applications.filter(app => app.status === 'collected').length;
      
      setStats({
        total,
        submitted,
        under_review: underReview,
        processing,
        ready_for_pickup: readyForPickup,
        collected
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.first_name}!
        </h1>
        <p className="text-gray-600 mt-2">
          Manage your passport applications and appointments
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
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
          <div className="text-3xl mb-2">⏳</div>
          <p className="text-gray-600 text-sm">In Progress</p>
          {loading ? (
            <div className="text-2xl font-bold text-gray-400">...</div>
          ) : (
            <p className="text-2xl font-bold text-yellow-600">
              {stats.submitted + stats.under_review + stats.processing}
            </p>
          )}
        </div>
        
        <div className="card p-6">
          <div className="text-3xl mb-2">✅</div>
          <p className="text-gray-600 text-sm">Completed</p>
          {loading ? (
            <div className="text-2xl font-bold text-gray-400">...</div>
          ) : (
            <p className="text-2xl font-bold text-green-600">
              {stats.ready_for_pickup + stats.collected}
            </p>
          )}
        </div>
      </div>

      {/* Status Breakdown */}
      {!loading && stats.total > 0 && (
        <div className="card p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Status Breakdown</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{stats.submitted}</p>
              <p className="text-xs text-gray-600 mt-1">Submitted</p>
            </div>
            <div className="text-center p-3 bg-yellow-50 rounded-lg">
              <p className="text-2xl font-bold text-yellow-600">{stats.under_review}</p>
              <p className="text-xs text-gray-600 mt-1">Under Review</p>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-600">{stats.processing}</p>
              <p className="text-xs text-gray-600 mt-1">Processing</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{stats.ready_for_pickup}</p>
              <p className="text-xs text-gray-600 mt-1">Ready</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-600">{stats.collected}</p>
              <p className="text-xs text-gray-600 mt-1">Collected</p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="space-y-3">
          <Link 
            to="/applicant/applications/new" 
            className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Apply for New Passport</p>
                <p className="text-sm text-gray-600">Start a new passport application</p>
              </div>
              <span className="text-2xl">➡️</span>
            </div>
          </Link>
          
          <Link 
            to="/applicant/applications" 
            className="block p-4 border-2 border-gray-200 rounded-lg hover:border-[#00209F] hover:bg-blue-50 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">View My Applications</p>
                <p className="text-sm text-gray-600">
                  Track your application status
                  {!loading && stats.total > 0 && (
                    <span className="ml-2 px-2 py-0.5 bg-[#00209F] text-white text-xs rounded-full">
                      {stats.total}
                    </span>
                  )}
                </p>
              </div>
              <span className="text-2xl">📋</span>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}