import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import applicationsApi from '../../api/applications';
import { toast } from 'react-hot-toast';

export default function ApplicationQueue() {
  const [searchParams] = useSearchParams();
  const filterParam = searchParams.get('filter');
  
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(filterParam || 'all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchApplications();
  }, [filter]);

const fetchApplications = async () => {
  setLoading(true);
  try {
    const data = await applicationsApi.getAll();  // Should return array
    console.log('Queue applications:', data); // Debug
    
    // Ensure we have an array
    const apps = Array.isArray(data) ? data : [];
    setApplications(apps);
  } catch (error) {
    console.error('Error fetching applications:', error);
    toast.error('Failed to load applications');
    setApplications([]);
  } finally {
    setLoading(false);
  }
};

  const getStatusColor = (status) => {
    const colors = {
      submitted: 'bg-blue-100 text-blue-800',
      under_review: 'bg-yellow-100 text-yellow-800',
      documents_required: 'bg-orange-100 text-orange-800',
      processing: 'bg-purple-100 text-purple-800',
      quality_check: 'bg-indigo-100 text-indigo-800',
      ready_for_pickup: 'bg-green-100 text-green-800',
      collected: 'bg-gray-100 text-gray-800',
      expired: 'bg-red-100 text-red-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatStatus = (status) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const filteredApplications = applications
    .filter(app => {
      // Apply status filter
      if (filter === 'submitted') return app.status === 'submitted';
      if (filter === 'overdue') return app.is_overdue;
      if (filter === 'in_progress') return ['under_review', 'processing', 'quality_check'].includes(app.status);
      return true; // 'all'
    })
    .filter(app => {
      // Apply search term
      if (!searchTerm) return true;
      const search = searchTerm.toLowerCase();
      return (
        app.application_number?.toLowerCase().includes(search) ||
        app.first_name?.toLowerCase().includes(search) ||
        app.last_name?.toLowerCase().includes(search) ||
        app.email?.toLowerCase().includes(search)
      );
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading applications...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Application Queue</h1>
        <p className="text-gray-600 mt-2">Review and process passport applications</p>
      </div>

      {/* Filters */}
      <div className="card p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by name, email, or application number..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'all'
                  ? 'bg-[#00209F] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({applications.length})
            </button>
            <button
              onClick={() => setFilter('submitted')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'submitted'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              New ({applications.filter(a => a.status === 'submitted').length})
            </button>
            <button
              onClick={() => setFilter('in_progress')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'in_progress'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              In Progress ({applications.filter(a => ['under_review', 'processing', 'quality_check'].includes(a.status)).length})
            </button>
            <button
              onClick={() => setFilter('overdue')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'overdue'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Overdue ({applications.filter(a => a.is_overdue).length})
            </button>
          </div>
        </div>
      </div>

      {/* Applications List */}
      {filteredApplications.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {searchTerm ? 'No applications found' : 'No applications in this category'}
          </h3>
          <p className="text-gray-600">
            {searchTerm ? 'Try a different search term' : 'Check back later for new applications'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredApplications.map((application) => (
            <div key={application.id} className="card p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {application.first_name} {application.last_name}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(application.status)}`}>
                      {formatStatus(application.status)}
                    </span>
                    {application.is_overdue && (
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Overdue
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-1">
                    Application #{application.application_number}
                  </p>
                  
                  <p className="text-sm text-gray-600">
                    {application.email} • {application.phone}
                  </p>
                </div>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 pt-4 border-t border-gray-200 text-sm">
                <div>
                  <span className="text-gray-600">Reason:</span>
                  <p className="font-medium capitalize">{application.reason_for_issuance?.replace('_', ' ')}</p>
                </div>
                <div>
                  <span className="text-gray-600">Submitted:</span>
                  <p className="font-medium">{formatDate(application.submitted_at)}</p>
                </div>
                <div>
                  <span className="text-gray-600">Days in Process:</span>
                  <p className="font-medium">{application.days_in_processing} days</p>
                </div>
                <div>
                  <span className="text-gray-600">Priority:</span>
                  <p className="font-medium capitalize">{application.priority_level}</p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-gray-200">
                <Link
                  to={`/officer/process/${application.id}`}
                  className="btn-primary"
                >
                  Process Application
                </Link>
                <Link
                  to={`/officer/applications/${application.id}`}
                  className="btn-outline"
                >
                  View Details
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}