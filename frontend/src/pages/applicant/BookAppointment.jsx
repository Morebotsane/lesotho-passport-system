import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import appointmentsApi from '../../api/appointments';
import applicationsApi from '../../api/applications';
import { toast } from 'react-hot-toast';

export default function BookAppointment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const applicationId = searchParams.get('application');
  
  const [step, setStep] = useState(1); // 1: Select app & location, 2: Select time
  const [loading, setLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  
  // Step 1 data
  const [applications, setApplications] = useState([]);
  const [locations, setLocations] = useState([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState(applicationId || '');
  const [selectedLocationId, setSelectedLocationId] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  
  // Step 2 data
  const [availability, setAvailability] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [apps, locs] = await Promise.all([
        applicationsApi.getMyApplications(),
        appointmentsApi.getLocations()
      ]);
      
      // Only show applications that are ready for pickup
      const readyApps = apps.filter(app => app.status === 'ready_for_pickup');
      setApplications(readyApps);
      setLocations(locs);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckAvailability = async () => {
    if (!selectedApplicationId || !selectedLocationId || !selectedDate) {
      toast.error('Please fill all fields');
      return;
    }

    setLoading(true);
    try {
      const data = await appointmentsApi.checkAvailability({
        application_id: selectedApplicationId,
        location_id: selectedLocationId,
        preferred_date: selectedDate
      });
      
      setAvailability(data);
      setStep(2);
    } catch (error) {
      console.error('Error checking availability:', error);
      toast.error(error.response?.data?.detail || 'Failed to check availability');
    } finally {
      setLoading(false);
    }
  };

  const handleBookAppointment = async () => {
    if (!selectedSlot) {
      toast.error('Please select a time slot');
      return;
    }

    setBookingLoading(true);
    try {
      const result = await appointmentsApi.createAppointment({
        passport_application_id: selectedApplicationId,
        time_slot_id: selectedSlot.id,
        location_id: selectedLocationId
      });

      toast.success(`Appointment booked! Confirmation: ${result.confirmation_code}`, {
        style: { background: '#009543', color: 'white' },
        duration: 5000
      });
      
      navigate('/applicant/appointments');
    } catch (error) {
      console.error('Error booking appointment:', error);
      toast.error(error.response?.data?.detail || 'Failed to book appointment');
    } finally {
      setBookingLoading(false);
    }
  };

  // Get minimum date (tomorrow)
  const getMinDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  if (loading && applications.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (applications.length === 0) {
    return (
      <div className="card p-12 text-center">
        <div className="text-6xl mb-4">📅</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No Applications Ready</h3>
        <p className="text-gray-600 mb-4">
          You don't have any passports ready for pickup yet.
        </p>
        <button onClick={() => navigate('/applicant/applications')} className="btn-primary">
          View My Applications
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Book Collection Appointment</h1>
        <p className="text-gray-600 mt-2">Schedule a time to collect your passport</p>
      </div>

      {/* Progress Steps */}
      <div className="card p-6 mb-6">
        <div className="flex items-center justify-center">
          <div className="flex items-center">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              step >= 1 ? 'bg-[#00209F] text-white' : 'bg-gray-200 text-gray-600'
            }`}>
              1
            </div>
            <span className="ml-2 font-medium">Select Details</span>
          </div>
          <div className={`w-24 h-1 mx-4 ${step >= 2 ? 'bg-[#00209F]' : 'bg-gray-200'}`}></div>
          <div className="flex items-center">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              step >= 2 ? 'bg-[#00209F] text-white' : 'bg-gray-200 text-gray-600'
            }`}>
              2
            </div>
            <span className="ml-2 font-medium">Choose Time</span>
          </div>
        </div>
      </div>

      {step === 1 && (
        <div className="card p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Step 1: Select Details</h2>
          
          <div className="space-y-6 max-w-2xl">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Application *
              </label>
              <select
                value={selectedApplicationId}
                onChange={(e) => setSelectedApplicationId(e.target.value)}
                className="input-field"
              >
                <option value="">Choose an application...</option>
                {applications.map(app => (
                  <option key={app.id} value={app.id}>
                    {app.application_number} - {app.first_name} {app.last_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pickup Location *
              </label>
              <select
                value={selectedLocationId}
                onChange={(e) => setSelectedLocationId(e.target.value)}
                className="input-field"
              >
                <option value="">Choose a location...</option>
                {locations.map(loc => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name} - {loc.address}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preferred Date *
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                min={getMinDate()}
                className="input-field"
              />
              <p className="text-xs text-gray-500 mt-1">
                Appointments must be booked at least 1 day in advance
              </p>
            </div>

            <button
              onClick={handleCheckAvailability}
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50"
            >
              {loading ? 'Checking Availability...' : 'Check Availability'}
            </button>
          </div>
        </div>
      )}

      {step === 2 && availability && (
        <div>
          <button
            onClick={() => setStep(1)}
            className="text-[#00209F] hover:underline mb-4"
          >
            ← Back to Details
          </button>

          <div className="card p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Step 2: Choose Time Slot</h2>
            
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>Location:</strong> {availability.location.name}
              </p>
              <p className="text-sm text-gray-700">
                <strong>Date:</strong> {new Date(availability.requested_date).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>

            {availability.available_slots.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-600 mb-4">No slots available for this date</p>
                <button onClick={() => setStep(1)} className="btn-outline">
                  Choose Different Date
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {availability.available_slots.map(slot => (
                    <button
                      key={slot.id}
                      onClick={() => setSelectedSlot(slot)}
                      className={`p-4 border-2 rounded-lg transition ${
                        selectedSlot?.id === slot.id
                          ? 'border-[#00209F] bg-blue-50'
                          : 'border-gray-200 hover:border-[#00209F]'
                      }`}
                    >
                      <div className="font-medium">{slot.start_time}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {slot.remaining_capacity} slots left
                      </div>
                    </button>
                  ))}
                </div>

                <button
                  onClick={handleBookAppointment}
                  disabled={!selectedSlot || bookingLoading}
                  className="btn-primary w-full disabled:opacity-50"
                >
                  {bookingLoading ? 'Booking...' : 'Confirm Appointment'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}