import { useState, useEffect } from 'react';
import appointmentsApi from '../../api/appointments';
import { toast } from 'react-hot-toast';

export default function DailySchedule() {
  const [loading, setLoading] = useState(true);
  const [schedule, setSchedule] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [filterType, setFilterType] = useState('all'); // all, submission, collection

  useEffect(() => {
  const fetchSchedule = async () => {
    setLoading(true);
    try {
      const data = await appointmentsApi.getOfficerSchedule(selectedDate);
      setSchedule(data);
    } catch (error) {
      console.error('Error fetching schedule:', error);
      toast.error('Failed to load schedule');
    } finally {
      setLoading(false);
    }
  };

    fetchSchedule();
  }, [selectedDate]);

  const fetchSchedule = async () => {
    setLoading(true);
    try {
      const data = await appointmentsApi.getOfficerSchedule(selectedDate);
      setSchedule(data);
    } catch (error) {
      console.error('Error fetching schedule:', error);
      toast.error('Failed to load schedule');
    } finally {
      setLoading(false);
    }
  };

  // ADD THESE HANDLERS
  const handleCheckIn = async (appointmentId) => {
    try {
      await appointmentsApi.checkInAppointment(appointmentId);
      toast.success('Appointment checked in successfully!');
      fetchSchedule();
    } catch (error) {
      console.error('Full error object:', error);
      console.error('Error response:', error.response);
      console.error('Error response data:', error.response?.data);
      console.error('Error detail:', error.response?.data?.detail);
      
      const errorMessage = error.data?.detail || error.message || 'Failed to check in';
      
      toast.error(errorMessage, {
        duration: 5000,
        style: {
          background: '#DC2626',
          color: 'white',
        }
      });
    }
  };

  const handleComplete = async (appointmentId) => {
    if (!window.confirm('Mark this appointment as completed?')) {
      return;
    }

    try {
      await appointmentsApi.completeAppointment(appointmentId);
      toast.success('Appointment completed! Passport collected.', {
        duration: 5000,
        style: { background: '#009543', color: 'white' }
      });
      fetchSchedule(); // Refresh the schedule
    } catch (error) {
      console.error('Error:', error);
      
      // Show the specific error message from backend
      const errorMessage = error.data?.detail || error.message || 'Failed to complete';
      
      toast.error(errorMessage, {
        duration: 5000,
        style: {
          background: '#DC2626',
          color: 'white',
        }
      });
    }
  };

  const getTypeColor = (type) => {
    return type === 'submission' 
      ? 'bg-blue-100 text-blue-800 border-blue-300'
      : 'bg-green-100 text-green-800 border-green-300';
  };

  const getTypeIcon = (type) => {
    return type === 'submission' ? '📝' : '📦';
  };

  const getStatusColor = (status) => {
    const colors = {
      scheduled: 'bg-yellow-100 text-yellow-800',
      checked_in: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      no_show: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const filteredAppointments = schedule?.appointments?.filter(apt => {
    if (filterType === 'all') return true;
    return apt.type === filterType;
  }) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading schedule...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Daily Schedule</h1>
        <p className="text-gray-600 mt-2">View and manage your daily appointments</p>
      </div>

      {/* Date Selector & Filters */}
      <div className="card p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Date
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="input-field"
              />
            </div>

            {schedule?.location && (
              <div className="pt-6">
                <div className="text-sm text-gray-600">Your Office</div>
                <div className="font-medium">{schedule.location.name}</div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setFilterType('all')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filterType === 'all'
                  ? 'bg-[#00209F] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({schedule?.summary?.total || 0})
            </button>
            <button
              onClick={() => setFilterType('submission')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filterType === 'submission'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Submissions ({schedule?.summary?.submission || 0})
            </button>
            <button
              onClick={() => setFilterType('collection')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filterType === 'collection'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Collections ({schedule?.summary?.collection || 0})
            </button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {schedule && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="card p-4">
            <div className="text-sm text-gray-600">Total Appointments</div>
            <div className="text-2xl font-bold text-gray-900">{schedule.summary.total}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-gray-600">Checked In</div>
            <div className="text-2xl font-bold text-purple-600">{schedule.summary.checked_in}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-2xl font-bold text-green-600">{schedule.summary.completed}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-gray-600">Remaining</div>
            <div className="text-2xl font-bold text-yellow-600">
              {schedule.summary.total - schedule.summary.completed}
            </div>
          </div>
        </div>
      )}

      {/* Appointments List */}
      {!schedule?.location ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">📍</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Location Assigned</h3>
          <p className="text-gray-600">
            You need to be assigned to a location to view appointments.
          </p>
        </div>
      ) : filteredAppointments.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">📅</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Appointments</h3>
          <p className="text-gray-600">
            {filterType === 'all' 
              ? 'No appointments scheduled for this date'
              : `No ${filterType} appointments for this date`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAppointments.map((appointment) => (
            <div key={appointment.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getTypeIcon(appointment.type)}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {appointment.applicant_name}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Application: {appointment.application_number}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-xs text-gray-600">Time</p>
                      <p className="font-medium">{appointment.time}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Type</p>
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${getTypeColor(appointment.type)}`}>
                        {appointment.type === 'submission' ? 'Submission' : 'Collection'}
                      </span>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Status</p>
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.status)}`}>
                        {appointment.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Confirmation</p>
                      <p className="font-medium text-sm">{appointment.confirmation_code}</p>
                    </div>
                  </div>
                </div>

                {/* ACTION BUTTONS - UPDATED */}
                <div className="flex flex-col gap-2 ml-4">
                  {(appointment.status === 'scheduled' || 
                    appointment.status === 'confirmed' || 
                    appointment.status === 'rescheduled') ? (
                    <button
                      onClick={() => handleCheckIn(appointment.id)}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm whitespace-nowrap"
                    >
                      ✓ Check In
                    </button>
                  ) : appointment.status === 'checked_in' ? (
                    <button
                      onClick={() => handleComplete(appointment.id)}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm whitespace-nowrap"
                    >
                      ✓ Complete
                    </button>
                  ) : appointment.status === 'completed' ? (
                    <div className="text-green-600 font-medium text-sm">
                      ✓ Completed
                    </div>
                  ) : (
                    // Don't show anything for cancelled/no-show - status badge is enough
                    <div></div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}