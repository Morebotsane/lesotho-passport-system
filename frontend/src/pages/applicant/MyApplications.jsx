import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import applicationsApi from '../../api/applications';
import { toast } from 'react-hot-toast';

export default function MyApplications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const data = await applicationsApi.getMyApplications();
      setApplications(data);
    } catch (error) {
      console.error('Error fetching applications:', error);
      toast.error('Failed to load applications');
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

  const filteredApplications = applications.filter(app =>
    app.application_number?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Applications</h1>
          <p className="text-gray-600 mt-2">
            Track and manage your passport applications
          </p>
        </div>
        <Link to="/applicant/applications/new" className="btn-primary">
          New Application
        </Link>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search by application number..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input-field max-w-md"
        />
      </div>

      {/* Applications List */}
      {filteredApplications.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {searchTerm ? 'No applications found' : 'No applications yet'}
          </h3>
          <p className="text-gray-600 mb-6">
            {searchTerm 
              ? 'Try a different search term' 
              : 'Start by submitting your first passport application'}
          </p>
          {!searchTerm && (
            <Link to="/applicant/applications/new" className="btn-primary">
              Submit New Application
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredApplications.map((application) => (
            <Link
              key={application.id}
              to={`/applicant/applications/${application.id}`}
              className="card p-6 hover:shadow-lg transition-shadow block"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {application.first_name} {application.last_name}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(application.status)}`}>
                      {formatStatus(application.status)}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-1">
                    Application #{application.application_number}
                  </p>
                  
                  <p className="text-sm text-gray-600">
                    {application.email} • {application.phone}
                  </p>
                </div>
                
                <div className="text-gray-400 text-2xl ml-4">
                  →
                </div>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200 text-sm">
                <div>
                  <span className="text-gray-600">Date of Birth:</span>
                  <p className="font-medium">{application.date_of_birth}</p>
                </div>
                <div>
                  <span className="text-gray-600">Place of Birth:</span>
                  <p className="font-medium">{application.place_of_birth}</p>
                </div>
                <div>
                  <span className="text-gray-600">Address:</span>
                  <p className="font-medium truncate">{application.residential_address}</p>
                </div>
                <div>
                  <span className="text-gray-600">Reason:</span>
                  <p className="font-medium capitalize">{application.reason_for_issuance.replace('_', ' ')}</p>
                </div>
                <div>
                  <span className="text-gray-600">Submitted:</span>
                  <p className="font-medium">{formatDate(application.submitted_at)}</p>
                </div>
                <div>
                  <span className="text-gray-600">Processing:</span>
                  <p className="font-medium">{application.days_in_processing} days</p>
                </div>
              </div>

              {application.is_overdue && (
                <div className="mt-3 text-red-600 text-sm font-medium">
                  Overdue
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}