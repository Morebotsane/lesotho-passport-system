import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { getUserById, updateUser, resetUserPassword } from '../../api/admin';
import appointmentsApi from '../../api/appointments';
import { toast } from 'react-hot-toast';

export default function EditOfficer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [locations, setLocations] = useState([]);
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    assigned_location_id: ''  // ADD THIS
  });
  
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [officer, locs] = await Promise.all([
          getUserById(id),
          appointmentsApi.getLocations(true)
        ]);
        
        setFormData({
          first_name: officer.first_name,
          last_name: officer.last_name,
          email: officer.email,
          phone: officer.phone || '',
          assigned_location_id: officer.assigned_location_id || ''  // ADD THIS
        });
        
        setLocations(locs);
      } catch (error) {
        console.error('Error fetching data:', error);
        toast.error('Failed to load officer details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setUpdating(true);

    try {
      await updateUser(id, formData);
      
      toast.success('Officer updated successfully', {
        style: { background: '#009543', color: 'white' }
      });
      
      navigate('/admin/officers');
    } catch (error) {
      console.error('Error updating officer:', error);
      toast.error(error.response?.data?.detail || 'Failed to update officer');
    } finally {
      setUpdating(false);
    }
  };

  const handlePasswordReset = async () => {
    if (!newPassword || newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    if (!window.confirm('Are you sure you want to reset this officer\'s password?')) {
      return;
    }

    try {
      await resetUserPassword(id, newPassword);
      
      toast.success('Password reset successfully', {
        style: { background: '#009543', color: 'white' }
      });
      
      setShowPasswordReset(false);
      setNewPassword('');
    } catch (error) {
      console.error('Error resetting password:', error);
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading officer details...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <Link to="/admin/officers" className="text-[#00209F] hover:underline mb-4 inline-block">
          ← Back to Officers
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Edit Officer</h1>
        <p className="text-gray-600 mt-2">Update officer account information</p>
      </div>

      <div className="max-w-2xl space-y-6">
        {/* Profile Information */}
        <form onSubmit={handleSubmit} className="card p-6 space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Profile Information</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                First Name *
              </label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Last Name *
              </label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                required
                className="input-field"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email *
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="input-field"
              disabled
              title="Email cannot be changed"
            />
            <p className="text-xs text-gray-500 mt-1">
              Email cannot be changed
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="input-field"
              placeholder="e.g., 59123456"
            />
          </div>

          {/* ADD LOCATION SELECTOR */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assigned Location *
            </label>
            <select
              name="assigned_location_id"
              value={formData.assigned_location_id}
              onChange={handleChange}
              required
              className="input-field"
            >
              <option value="">Select a location...</option>
              {locations.map(loc => (
                <option key={loc.id} value={loc.id}>
                  {loc.name} - {loc.address}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Officer will only see applications from this location
            </p>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={updating}
              className="btn-primary disabled:opacity-50"
            >
              {updating ? 'Updating...' : 'Save Changes'}
            </button>
            <Link to="/admin/officers" className="btn-outline">
              Cancel
            </Link>
          </div>
        </form>

        {/* Password Reset */}
        <div className="card p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Password Reset</h2>
          
          {!showPasswordReset ? (
            <button
              onClick={() => setShowPasswordReset(true)}
              className="btn-outline"
            >
              Reset Password
            </button>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  New Password *
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  minLength={8}
                  className="input-field"
                  placeholder="Minimum 8 characters"
                />
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handlePasswordReset}
                  className="btn-primary"
                  disabled={!newPassword || newPassword.length < 8}
                >
                  Reset Password
                </button>
                <button
                  onClick={() => {
                    setShowPasswordReset(false);
                    setNewPassword('');
                  }}
                  className="btn-outline"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}