import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import appointmentsApi from '../../api/appointments';
import applicationsApi from '../../api/applications';
import { toast } from 'react-hot-toast';

export default function BookSubmissionAppointment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const applicationId = searchParams.get('application');
  
  const [loading, setLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [application, setApplication] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [availability, setAvailability] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);

  useEffect(() => {
      const fetchApplication = async () => {
        try {
          const data = await applicationsApi.getById(applicationId);
          setApplication(data);
        } catch (error) {
          console.error('Error fetching application:', error);
          toast.error('Failed to load application');
        }
      };
    if (applicationId) {
      fetchApplication();
    }
  }, [applicationId]);

  const handleCheckAvailability = async () => {
    if (!selectedDate) {
      toast.error('Please select a date');
      return;
    }

    setLoading(true);
    try {
      const data = await appointmentsApi.checkAvailability({
        application_id: applicationId,
        location_id: application.submission_location_id,
        preferred_date: selectedDate
      });
      
      setAvailability(data);
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
      await appointmentsApi.createAppointment({
        passport_application_id: applicationId,
        time_slot_id: selectedSlot.id,
        location_id: application.submission_location_id,
        appointment_type: 'submission'  // ADD THIS - specify it's a submission appointment
      });
      
      toast.success('Submission appointment booked successfully!', {
        style: { background: '#009543', color: 'white' },
        duration: 4000
      });
      
      navigate('/applicant/appointments');
    } catch (error) {
      console.error('Error booking appointment:', error);
      toast.error(error.response?.data?.detail || 'Failed to book appointment');
    } finally {
      setBookingLoading(false);
    }
  };

  const getMinDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  if (!application) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Book Submission Appointment</h1>
        <p className="text-gray-600 mt-2">Schedule your visit for biometric capture and document verification</p>
      </div>

      {/* Application Info */}
      <div className="card p-6 mb-6">
        <h3 className="font-semibold text-gray-900 mb-2">Application Details</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600">Application Number</p>
            <p className="font-medium">{application.application_number}</p>
          </div>
          <div>
            <p className="text-gray-600">Applicant</p>
            <p className="font-medium">{application.first_name} {application.last_name}</p>
          </div>
          <div className="col-span-2">
            <p className="text-gray-600">Submission Office</p>
            <p className="font-medium">{application.submission_location?.name}</p>
            <p className="text-sm text-gray-500">{application.submission_location?.address}</p>
          </div>
        </div>
      </div>

      {!availability ? (
        <div className="card p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Select Date</h2>
          
          <div className="max-w-md space-y-4">
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
      ) : (
        <div>
          <button
            onClick={() => {
              setAvailability(null);
              setSelectedSlot(null);
            }}
            className="text-[#00209F] hover:underline mb-4"
          >
            ← Choose Different Date
          </button>

          <div className="card p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Available Time Slots</h2>
            
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
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
                <button
                  onClick={() => {
                    setAvailability(null);
                    setSelectedSlot(null);
                  }}
                  className="btn-outline"
                >
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

      {/* Important Information */}
      <div className="card p-6 mt-6 bg-yellow-50 border-yellow-200">
        <h3 className="font-semibold text-gray-900 mb-3">📋 What to Bring</h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li>✓ Original National ID</li>
          <li>✓ Birth Certificate (original & copy)</li>
          <li>✓ Proof of Residence</li>
          <li>✓ 2 Passport Photos (if not done at office)</li>
          <li>✓ Application confirmation (print or on phone)</li>
        </ul>
      </div>
    </div>
  );
}