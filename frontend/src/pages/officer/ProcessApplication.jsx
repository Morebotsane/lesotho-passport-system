import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import applicationsApi from '../../api/applications';
import { toast } from 'react-hot-toast';

const STATUS_OPTIONS = [
  { value: 'submitted', label: 'Submitted' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'documents_required', label: 'Documents Required' },
  { value: 'processing', label: 'Processing' },
  { value: 'quality_check', label: 'Quality Check' },
  { value: 'ready_for_pickup', label: 'Ready for Pickup' },
  { value: 'rejected', label: 'Rejected' }
];

export default function ProcessApplication() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [sendAutoNotification, setSendAutoNotification] = useState(true);
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  
  const [newStatus, setNewStatus] = useState('');
  const [notes, setNotes] = useState('');

  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  const [sending, setSending] = useState(false);

  const NOTIFICATION_TEMPLATES = application ? {
    payment: `Please pay for your passport application at subaccountancy. ${application.first_name} ${application.last_name}, Amount Due:M175.00 Reference #${application.application_number}`,
    submitted: `Dear ${application.first_name}, your passport application #${application.application_number} has been received and is under review.`,
    under_review: `Dear ${application.first_name}, your application #${application.application_number} is now under review by our officers.`,
    documents_required: `Dear ${application.first_name}, additional documents are required for application #${application.application_number}. Please contact our office.`,
    processing: `Dear ${application.first_name}, your passport #${application.application_number} is being processed.`,
    quality_check: `Dear ${application.first_name}, your passport #${application.application_number} is in final quality check.`,
    ready_for_pickup: `Dear ${application.first_name}, your passport is ready! Application #${application.application_number}. Please collect at Ministry of Home Affairs.`,
    rejected: `Dear ${application.first_name}, application #${application.application_number} could not be approved. Please contact our office for details.`
  } : {};

  useEffect(() => {
  const fetchApplication = async () => {
    try {
      const data = await applicationsApi.getById(id);
      console.log('📦 RECEIVED APPLICATION DATA:', data);
      setApplication(data);
      setNewStatus(data.status);
    } catch (error) {
      console.error('Error fetching application:', error);
      toast.error('Failed to load application');
    } finally {
      setLoading(false);
    }
  };

  fetchApplication();
}, [id]);

  const handleSendNotification = async () => {
    if (!notificationMessage.trim()) {
      toast.error('Please enter a message');
      return;
    }

    setSending(true);
    try {
      await applicationsApi.sendNotification(id, notificationMessage);
      
      toast.success('Notification sent successfully', {
        style: { background: '#009543', color: 'white' }
      });
      
      setShowNotification(false);
      setNotificationMessage('');
    } catch (error) {
      console.error('Error sending notification:', error);
      toast.error(error.response?.data?.detail || 'Failed to send notification');
    } finally {
      setSending(false);
    }
  };

const handleUpdateStatus = async () => {
  if (!newStatus) {
    toast.error('Please select a status');
    return;
  }

  setUpdating(true);
  try {
    const response = await applicationsApi.updateStatus(id, {
      status: newStatus,
      notes: notes || undefined,
      send_notification: sendAutoNotification
    });
    
    const notificationMsg = response.notification_sent 
      ? ' Notification sent to applicant.'
      : '';
    
    toast.success(`Status updated successfully!${notificationMsg}`, {
      style: { background: '#009543', color: 'white' },
      duration: 4000
    });
    
    navigate('/officer/queue');
  } catch (error) {
    console.error('Error updating status:', error);
    toast.error(error.response?.data?.detail || 'Failed to update status');
  } finally {
    setUpdating(false);
  }
};

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading application...</p>
        </div>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="card p-12 text-center">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Application Not Found</h3>
        <Link to="/officer/queue" className="btn-primary">Back to Queue</Link>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <Link to="/officer/queue" className="text-[#00209F] hover:underline mb-4 inline-block">
          ← Back to Queue
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">
          Process Application #{application.application_number}
        </h1>
        <p className="text-gray-600 mt-2">
          Submitted on {formatDate(application.submitted_at)}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Application Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Applicant Info */}
          <div className="card p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Applicant Information</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Full Name</p>
                <p className="font-medium">{application.first_name} {application.last_name}</p>
              </div>
              <div>
                <p className="text-gray-600">Email</p>
                <p className="font-medium">{application.email}</p>
              </div>
              <div>
                <p className="text-gray-600">Phone</p>
                <p className="font-medium">{application.phone}</p>
              </div>
              <div>
                <p className="text-gray-600">Date of Birth</p>
                <p className="font-medium">{application.date_of_birth}</p>
              </div>
              <div className="col-span-2">
                <p className="text-gray-600">Address</p>
                <p className="font-medium">{application.residential_address}</p>
              </div>
            </div>
          </div>

          {/* Passport Details */}
          <div className="card p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Passport Details</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Type</p>
                <p className="font-medium capitalize">{application.passport_type}</p>
              </div>
              <div>
                <p className="text-gray-600">Reason</p>
                <p className="font-medium capitalize">{application.reason_for_issuance?.replace('_', ' ')}</p>
              </div>
              {application.previous_passport_number && (
                <div>
                  <p className="text-gray-600">Previous Passport</p>
                  <p className="font-medium">{application.previous_passport_number}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Status Update Panel */}
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Update Status</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Status
                </label>
                <p className="text-lg font-semibold capitalize">
                  {application.status.replace('_', ' ')}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  New Status *
                </label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="input-field"
                >
                  {STATUS_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes (Optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={4}
                  placeholder="Add processing notes..."
                  className="input-field"
                />
              </div>

              {/* ADD THIS CHECKBOX */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="sendNotification"
                  checked={sendAutoNotification}
                  onChange={(e) => setSendAutoNotification(e.target.checked)}
                  className="w-4 h-4 text-[#00209F] border-gray-300 rounded focus:ring-[#00209F]"
                />
                <label htmlFor="sendNotification" className="ml-2 text-sm text-gray-700">
                  Send SMS notification to applicant
                </label>
              </div>

              <button
                onClick={handleUpdateStatus}
                disabled={updating || newStatus === application.status}
                className="btn-primary w-full disabled:opacity-50"
              >
                {updating ? 'Updating...' : 'Update Status'}
              </button>
            </div>
          </div>

          {/* Notification Panel */}
  <div className="card p-6">
    <h2 className="text-lg font-bold text-gray-900 mb-4">Send Notification</h2>
    
    {!showNotification ? (
      <button
        onClick={() => setShowNotification(true)}
        className="btn-outline w-full"
      >
        Notify Applicant
      </button>
    ) : (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quick Templates
          </label>
          <select
            onChange={(e) => setNotificationMessage(e.target.value)}
            className="input-field text-sm">
            <option value="">Select a template...</option>
            <option value={NOTIFICATION_TEMPLATES.payment}>Make Payment</option>
            <option value={NOTIFICATION_TEMPLATES.submitted}>Application Received</option>
            <option value={NOTIFICATION_TEMPLATES.under_review}>Under Review</option>
            <option value={NOTIFICATION_TEMPLATES.documents_required}>Documents Required</option>
            <option value={NOTIFICATION_TEMPLATES.processing}>Processing</option>
            <option value={NOTIFICATION_TEMPLATES.quality_check}>Quality Check</option>
            <option value={NOTIFICATION_TEMPLATES.ready_for_pickup}>Ready for Pickup</option>
            <option value={NOTIFICATION_TEMPLATES.rejected}>Rejected</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Message *
          </label>
          <textarea
            value={notificationMessage}
            onChange={(e) => setNotificationMessage(e.target.value)}
            rows={4}
            placeholder="Enter custom message..."
            className="input-field"
            maxLength={160}
          />
          <p className="text-xs text-gray-500 mt-1">
            {notificationMessage.length}/160 characters
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleSendNotification}
            disabled={sending || !notificationMessage.trim()}
            className="btn-primary flex-1 disabled:opacity-50"
          >
            {sending ? 'Sending...' : 'Send SMS'}
          </button>
          <button
            onClick={() => {
              setShowNotification(false);
              setNotificationMessage('');
            }}
            className="btn-outline"
          >
            Cancel
          </button>
        </div>
      </div>
    )}
  </div>

          {/* Processing Info */}
          <div className="card p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Processing Info</h2>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-gray-600">Days in Processing</p>
                <p className="font-medium">{application.days_in_processing} days</p>
              </div>
              <div>
                <p className="text-gray-600">Priority</p>
                <p className="font-medium capitalize">{application.priority_level}</p>
              </div>
              {application.is_overdue && (
                <div className="bg-red-50 border border-red-200 rounded p-3">
                  <p className="text-red-800 font-medium text-xs">Overdue - Requires Attention</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}