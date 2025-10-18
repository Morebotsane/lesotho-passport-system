import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import appointmentsApi from '../../api/appointments';
import { toast } from 'react-hot-toast';

export default function MyAppointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCompleted, setShowCompleted] = useState(false);

  useEffect(() => {
      const fetchAppointments = async () => {
    setLoading(true);
    try {
      const data = await appointmentsApi.getMyAppointments(showCompleted);
      setAppointments(data);
    } catch (error) {
      console.error('Error fetching appointments:', error);
      toast.error('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

    fetchAppointments();
  }, [showCompleted]);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const data = await appointmentsApi.getMyAppointments(showCompleted);
      setAppointments(data);
    } catch (error) {
      console.error('Error fetching appointments:', error);
      toast.error('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (appointmentId) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) {
      return;
    }

    try {
      await appointmentsApi.cancelAppointment(appointmentId, 'Cancelled by user');
      toast.success('Appointment cancelled successfully');
      fetchAppointments();
    } catch (error) {
      console.error('Error cancelling appointment:', error);
      toast.error(error.response?.data?.detail || 'Failed to cancel appointment');
    }
  };

  const formatDateTime = (dateTimeString) => {
    return new Date(dateTimeString).toLocaleString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      scheduled: 'bg-blue-100 text-blue-800',
      checked_in: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      no_show: 'bg-orange-100 text-orange-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading appointments...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Appointments</h1>
          <p className="text-gray-600 mt-2">View and manage your collection appointments</p>
        </div>
        <Link to="/applicant/appointments/book" className="btn-primary">
          📅 Book Appointment
        </Link>
      </div>

      {/* Filter Toggle */}
      <div className="card p-4 mb-6">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="showCompleted"
            checked={showCompleted}
            onChange={(e) => setShowCompleted(e.target.checked)}
            className="w-4 h-4 text-[#00209F] border-gray-300 rounded focus:ring-[#00209F]"
          />
          <label htmlFor="showCompleted" className="ml-2 text-sm text-gray-700">
            Show completed appointments
          </label>
        </div>
      </div>

      {appointments.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">📅</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {showCompleted ? 'No completed appointments' : 'No upcoming appointments'}
          </h3>
          <p className="text-gray-600 mb-4">
            {showCompleted 
              ? 'You haven\'t completed any appointments yet'
              : 'Book an appointment to collect your passport'}
          </p>
          {!showCompleted && (
            <Link to="/applicant/appointments/book" className="btn-primary">
              Book Appointment
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {appointments.map((appointment) => (
            <div key={appointment.id} className="card p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {appointment.location_name}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.status)}`}>
                      {appointment.status.replace('_', ' ').toUpperCase()}
                    </span>
                    {/* ADD THIS - Show appointment type */}
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
                      appointment.type === 'submission' 
                        ? 'bg-blue-100 text-blue-800 border-blue-300'
                        : 'bg-green-100 text-green-800 border-green-300'
                    }`}>
                      {appointment.type === 'submission' ? '📝 Submission' : '📦 Collection'}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-1">
                    Application: {appointment.application_number}
                  </p>
                  
                  <p className="text-sm text-gray-600">
                    Confirmation: {appointment.confirmation_code}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg mb-4">
                <div>
                  <p className="text-xs text-gray-600">Date & Time</p>
                  <p className="font-medium">{formatDateTime(appointment.scheduled_datetime)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Type</p>
                  <p className="font-medium">
                    {appointment.type === 'submission' 
                      ? 'Submission (Lodge Application)' 
                      : 'Collection (Pick Up Passport)'}
                  </p>
                </div>
              </div>

    {appointment.status === 'scheduled' && appointment.can_be_rescheduled && (
      <div className="flex gap-3">
        <button
          onClick={() => handleCancel(appointment.id)}
          className="btn-outline text-red-600 border-red-600 hover:bg-red-50"
        >
          Cancel Appointment
        </button>
      </div>
    )}
  </div>
))}
        </div>
      )}
    </div>
  );
}