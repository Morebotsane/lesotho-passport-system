import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getOfficers, deactivateUser, activateUser } from '../../api/admin';
import { toast } from 'react-hot-toast';

export default function Officers() {
  const [officers, setOfficers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all'); // all, active, inactive

  useEffect(() => {
    fetchOfficers();
  }, []);

  const fetchOfficers = async () => {
    setLoading(true);
    try {
      const data = await getOfficers();
      setOfficers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching officers:', error);
      toast.error('Failed to load officers');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (officer) => {
    const action = officer.is_active ? 'deactivate' : 'activate';
    
    if (!window.confirm(`Are you sure you want to ${action} ${officer.first_name} ${officer.last_name}?`)) {
      return;
    }

    try {
      if (officer.is_active) {
        await deactivateUser(officer.id);
        toast.success('Officer deactivated successfully');
      } else {
        await activateUser(officer.id);
        toast.success('Officer activated successfully');
      }
      fetchOfficers(); // Refresh list
    } catch (error) {
      console.error(`Error ${action}ing officer:`, error);
      toast.error(`Failed to ${action} officer`);
    }
  };

  const filteredOfficers = officers
    .filter(officer => {
      // Status filter
      if (filterStatus === 'active' && !officer.is_active) return false;
      if (filterStatus === 'inactive' && officer.is_active) return false;
      
      // Search filter
      if (!searchTerm) return true;
      const search = searchTerm.toLowerCase();
      return (
        officer.first_name?.toLowerCase().includes(search) ||
        officer.last_name?.toLowerCase().includes(search) ||
        officer.email?.toLowerCase().includes(search)
      );
    });

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading officers...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Officer Management</h1>
          <p className="text-gray-600 mt-2">Manage officer accounts and permissions</p>
        </div>
        <Link to="/admin/officers/new" className="btn-primary">
          ➕ Add New Officer
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filterStatus === 'all'
                  ? 'bg-[#00209F] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({officers.length})
            </button>
            <button
              onClick={() => setFilterStatus('active')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filterStatus === 'active'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Active ({officers.filter(o => o.is_active).length})
            </button>
            <button
              onClick={() => setFilterStatus('inactive')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filterStatus === 'inactive'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Inactive ({officers.filter(o => !o.is_active).length})
            </button>
          </div>
        </div>
      </div>

      {/* Officers Table */}
      {/* Replace the table with this updated version */}
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Officer
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Email
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Location
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Created
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {filteredOfficers.map((officer) => (
            <tr key={officer.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-[#009543] rounded-full flex items-center justify-center">
                    <span className="text-white font-semibold">
                      {officer.first_name?.[0]}{officer.last_name?.[0]}
                    </span>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">
                      {officer.first_name} {officer.last_name}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">{officer.email}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">
                  {officer.assigned_location?.name || (
                    <span className="text-gray-400 italic">Not assigned</span>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  officer.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {officer.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(officer.created_at)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div className="flex justify-end gap-2">
                  <Link
                    to={`/admin/officers/${officer.id}/edit`}
                    className="text-[#00209F] hover:text-[#001870]"
                  >
                    Edit
                  </Link>
                  <button
                    onClick={() => handleToggleStatus(officer)}
                    className={officer.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}
                  >
                    {officer.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}