import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import appointmentsApi from '../../api/appointments';
import applicationsApi from '../../api/applications';


import { toast } from 'react-hot-toast';

export default function RescheduleAppointment() {
  const { id } = useParams(); // appointment ID
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const applicationId = searchParams.get('application');

  const [loading, setLoading] = useState(false);
  const [appointment, setAppointment] = useState(null);
  const [application, setApplication] = useState(null); 
  const [selectedDate, setSelectedDate] = useState('');
  const [availability, setAvailability] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [reason, setReason] = useState('');

  useEffect(() => {
    // Fetch both appointment and application details
    const fetchData = async () => {
      try {
        const [appointments, appData] = await Promise.all([
          appointmentsApi.getMyAppointments(),
          applicationId ? applicationsApi.getById(applicationId) : null
        ]);
        
        const apt = appointments.find(a => a.id === id);
        setAppointment(apt);
        
        if (appData) {
          setApplication(appData);
        }
      } catch (error) {
        console.error('Error:', error);
        toast.error('Failed to load details');
      }
    };

    fetchData();
  }, [id, applicationId]);

  const handleCheckAvailability = async () => {
    if (!selectedDate || !application) {
      toast.error('Missing required information');
      return;
    }

    setLoading(true);
    try {
      const data = await appointmentsApi.checkAvailability({
        application_id: applicationId,
        location_id: application.submission_location_id,  // FIXED: Get from application
        preferred_date: selectedDate
      });
      
      setAvailability(data);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to check availability');
    } finally {
      setLoading(false);
    }
  };

  const handleReschedule = async () => {
    if (!selectedSlot) {
      toast.error('Please select a time slot');
      return;
    }

    setLoading(true);
    try {
      await appointmentsApi.rescheduleAppointment(id, selectedSlot.id, reason);
      toast.success('Appointment rescheduled successfully!');
      navigate(`/applicant/applications/${applicationId}`);
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.response?.data?.detail || 'Failed to reschedule');
    } finally {
      setLoading(false);
    }
  };


  if (!appointment || !application) {  // FIXED: Check both
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Reschedule Appointment</h1>

      {/* Current Appointment */}
      <div className="card p-6 mb-6 bg-yellow-50 border-yellow-200">
        <h3 className="font-semibold mb-2">Current Appointment</h3>
        <p className="text-sm text-gray-700">
          📅 {new Date(appointment.scheduled_datetime).toLocaleString()}<br />
          📍 {appointment.location_name}<br />
          🎫 Confirmation: {appointment.confirmation_code}
        </p>
      </div>

      {/* Reason */}
      <div className="card p-6 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Reason for Rescheduling (Optional)
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          className="input-field"
          placeholder="Why are you rescheduling?"
        />
      </div>

      {/* Date Selection */}
      <div className="card p-6 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select New Date
        </label>
        <div className="flex gap-4">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            min={new Date().toISOString().split('T')[0]}
            className="input-field"
          />
          <button
            onClick={handleCheckAvailability}
            disabled={!selectedDate || loading}
            className="btn-primary"
          >
            Check Availability
          </button>
        </div>
      </div>

      {/* Available Slots */}
      {availability && (
        <div className="card p-6 mb-6">
          <h3 className="font-semibold mb-4">Available Time Slots</h3>
          
          {availability.available_slots?.length > 0 ? (
            <div className="grid grid-cols-3 gap-3">
              {availability.available_slots.map((slot) => (
                <button
                  key={slot.id}
                  onClick={() => setSelectedSlot(slot)}
                  className={`p-3 border-2 rounded-lg transition ${
                    selectedSlot?.id === slot.id
                      ? 'border-[#00209F] bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">{slot.start_time}</div>
                  <div className="text-xs text-gray-600">
                    {slot.available_capacity} slots
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No slots available for this date</p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4">
        <button
          onClick={() => navigate(-1)}
          className="btn-outline"
        >
          Cancel
        </button>
        <button
          onClick={handleReschedule}
          disabled={!selectedSlot || loading}
          className="btn-primary"
        >
          {loading ? 'Rescheduling...' : 'Confirm Reschedule'}
        </button>
      </div>
    </div>
  );
}