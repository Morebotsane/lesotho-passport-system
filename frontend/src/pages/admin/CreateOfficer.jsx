import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createOfficer } from '../../api/admin';
import appointmentsApi from '../../api/appointments';
import { toast } from 'react-hot-toast';

export default function CreateOfficer() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [locationsLoading, setLocationsLoading] = useState(true);
  const [locations, setLocations] = useState([]);
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    assigned_location_id: ''  // ADD THIS
  });

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      const data = await appointmentsApi.getLocations(true);
      setLocations(data);
    } catch (error) {
      console.error('Error fetching locations:', error);
      toast.error('Failed to load locations');
    } finally {
      setLocationsLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await createOfficer({
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        phone: formData.phone,
        password: formData.password,
        confirm_password: formData.confirm_password,
        assigned_location_id: formData.assigned_location_id || null  // ADD THIS
      });

      toast.success('Officer created successfully', {
        style: { background: '#009543', color: 'white' }
      });

      navigate('/admin/officers');
    } catch (error) {
      console.error('Error creating officer:', error);
      toast.error(error.response?.data?.detail || 'Failed to create officer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <Link to="/admin/officers" className="text-[#00209F] hover:underline mb-4 inline-block">
          ← Back to Officers
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Create New Officer</h1>
        <p className="text-gray-600 mt-2">Add a new officer account to the system</p>
      </div>

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit} className="card p-6 space-y-6">
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
            />
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
              disabled={locationsLoading}
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

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password *
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={8}
              className="input-field"
            />
            <p className="text-xs text-gray-500 mt-1">
              Minimum 8 characters
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirm Password *
            </label>
            <input
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              required
              className="input-field"
            />
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Officer'}
            </button>
            <Link to="/admin/officers" className="btn-outline">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}