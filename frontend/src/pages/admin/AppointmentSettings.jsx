import { useState, useEffect } from 'react';
import appointmentsApi from '../../api/appointments';
import { toast } from 'react-hot-toast';

export default function AppointmentSettings() {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    email: '',
    opens_at: '08:00',
    closes_at: '16:00',
    is_active: true
  });

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    setLoading(true);
    try {
      const data = await appointmentsApi.getLocations(false); // Get all, including inactive
      setLocations(data);
    } catch (error) {
      console.error('Error fetching locations:', error);
      toast.error('Failed to load locations');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (editingLocation) {
        await appointmentsApi.updateLocation(editingLocation.id, formData);
        toast.success('Location updated successfully');
      } else {
        await appointmentsApi.createLocation(formData);
        toast.success('Location created successfully');
      }
      
      setShowAddModal(false);
      setEditingLocation(null);
      resetForm();
      fetchLocations();
    } catch (error) {
      console.error('Error saving location:', error);
      toast.error(error.response?.data?.detail || 'Failed to save location');
    }
  };

  const handleEdit = (location) => {
    setEditingLocation(location);
    setFormData({
      name: location.name,
      address: location.address,
      phone: location.phone || '',
      email: location.email || '',
      opens_at: location.opens_at,
      closes_at: location.closes_at,
      is_active: location.is_active
    });
    setShowAddModal(true);
  };

  const handleToggleActive = async (location) => {
    try {
      await appointmentsApi.updateLocation(location.id, {
        ...location,
        is_active: !location.is_active
      });
      toast.success(`Location ${!location.is_active ? 'activated' : 'deactivated'}`);
      fetchLocations();
    } catch (error) {
      console.error('Error toggling location:', error);
      toast.error('Failed to update location');
    }
  };

  const handleGenerateSlots = async () => {
    if (!window.confirm('Generate time slots for the next 30 days for all active locations?')) {
      return;
    }

    try {
      const response = await appointmentsApi.generateTimeSlots(30);
      toast.success(`Generated ${response.message}`, {
        duration: 5000,
        style: { background: '#009543', color: 'white' }
      });
    } catch (error) {
      console.error('Error generating slots:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate time slots');
    }
  };  

  const resetForm = () => {
    setFormData({
      name: '',
      address: '',
      phone: '',
      email: '',
      opens_at: '08:00',
      closes_at: '16:00',
      is_active: true
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Appointment Settings</h1>
          <p className="text-gray-600 mt-2">Manage pickup locations and appointment configuration</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleGenerateSlots}  // ADD THIS
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
          >
            🔄 Generate Time Slots
          </button>
          <button
            onClick={() => {
              resetForm();
              setEditingLocation(null);
              setShowAddModal(true);
            }}
            className="btn-primary"
          >
            ➕ Add Location
          </button>
        </div>
      </div>

      {/* Locations List */}
      <div className="space-y-4">
        {locations.map((location) => (
          <div key={location.id} className="card p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-semibold text-gray-900">{location.name}</h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    location.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {location.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mt-4">
                  <div>
                    <p className="text-gray-600">Address</p>
                    <p className="font-medium">{location.address}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Phone</p>
                    <p className="font-medium">{location.phone || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Email</p>
                    <p className="font-medium">{location.email || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Hours</p>
                    <p className="font-medium">{location.opens_at} - {location.closes_at}</p>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 ml-4">
                <button
                  onClick={() => handleEdit(location)}
                  className="text-[#00209F] hover:underline"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleToggleActive(location)}
                  className={location.is_active ? 'text-red-600 hover:underline' : 'text-green-600 hover:underline'}
                >
                  {location.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </div>
          </div>
        ))}

        {locations.length === 0 && (
          <div className="card p-12 text-center">
            <div className="text-6xl mb-4">📍</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Locations Yet</h3>
            <p className="text-gray-600 mb-4">Add your first pickup location to start accepting appointments</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-primary"
            >
              Add Location
            </button>
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                {editingLocation ? 'Edit Location' : 'Add New Location'}
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="input-field"
                    placeholder="e.g., Maseru Main Office"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Address *
                  </label>
                  <textarea
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    required
                    rows={3}
                    className="input-field"
                    placeholder="Full street address"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
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
                      placeholder="e.g., 22312345"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="input-field"
                      placeholder="e.g., maseru@homeaffairs.gov.ls"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Opens At *
                    </label>
                    <input
                      type="time"
                      name="opens_at"
                      value={formData.opens_at}
                      onChange={handleChange}
                      required
                      className="input-field"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Closes At *
                    </label>
                    <input
                      type="time"
                      name="closes_at"
                      value={formData.closes_at}
                      onChange={handleChange}
                      required
                      className="input-field"
                    />
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleChange}
                    className="w-4 h-4 text-[#00209F] border-gray-300 rounded focus:ring-[#00209F]"
                  />
                  <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                    Location is active and accepting appointments
                  </label>
                </div>

                <div className="flex gap-4 pt-4">
                  <button type="submit" className="btn-primary flex-1">
                    {editingLocation ? 'Save Changes' : 'Create Location'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddModal(false);
                      setEditingLocation(null);
                      resetForm();
                    }}
                    className="btn-outline flex-1"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}