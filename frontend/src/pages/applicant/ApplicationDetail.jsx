import DocumentViewer from '../../components/common/DocumentViewer';
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import applicationsApi from '../../api/applications';
import appointmentsApi from '../../api/appointments';  // ADD THIS IMPORT
import { toast } from 'react-hot-toast';
import StatusTimeline from '../../components/applicant/StatusTimeline';


export default function ApplicationDetail() {
  const { id } = useParams();
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState([]);
  const [showDocuments, setShowDocuments] = useState(false);

  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState({
    passport_photo: null,
    id_document: null
  });

  // Add upload handler
  const handleFileSelect = (documentType, file) => {
    setSelectedFiles(prev => ({
      ...prev,
      [documentType]: file
    }));
  };

  const handleUploadDocuments = async () => {
  if (!selectedFiles.passport_photo && !selectedFiles.id_document) {
    toast.error('Please select at least one document to upload');
    return;
  }

  setUploading(true);
  try {
    const formData = new FormData();
    
    if (selectedFiles.passport_photo) {
      formData.append('passport_photo', selectedFiles.passport_photo);
    }
    
    if (selectedFiles.id_document) {
      formData.append('id_document', selectedFiles.id_document);
    }

    await applicationsApi.uploadDocuments(application.id, formData);
    
    toast.success('Documents uploaded successfully!', {
      duration: 5000,
      style: { background: '#009543', color: 'white' }
    });

    // Refresh application data
    const updatedApp = await applicationsApi.getById(application.id);
    setApplication(updatedApp);
    
    // Clear selections
    setSelectedFiles({ passport_photo: null, id_document: null });
    
  } catch (error) {
    console.error('Upload error:', error);
    toast.error(error.response?.data?.detail || 'Failed to upload documents');
  } finally {
    setUploading(false);
  }
};

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [appData, appointmentsData] = await Promise.all([
          applicationsApi.getById(id),
          appointmentsApi.getMyAppointments()
        ]);
        
        setApplication(appData);
        
        // Filter appointments for this application
        const appAppointments = appointmentsData.filter(
          apt => apt.application_id === id || apt.application_number === appData.application_number
        );
        setAppointments(appAppointments);
        
      } catch (error) {
        console.error('Error:', error);
        toast.error('Failed to load application');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const getStatusColor = (status) => {
    const colors = {
      submitted: 'bg-blue-100 text-blue-800',
      under_review: 'bg-yellow-100 text-yellow-800',
      documents_required: 'bg-orange-100 text-orange-800',
      processing: 'bg-purple-100 text-purple-800',
      quality_check: 'bg-indigo-100 text-indigo-800',
      ready_for_pickup: 'bg-green-100 text-green-800',
      collected: 'bg-gray-100 text-gray-800',
      expired: 'bg-red-100 text-red-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatStatus = (status) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Helper functions
  const getSubmissionAppointment = () => {
    return appointments.find(apt => apt.type === 'submission');
  };

  const getCollectionAppointment = () => {
    return appointments.find(apt => apt.type === 'collection');
  };

  const canBookSubmission = () => {
    return application?.status === 'submitted' && !getSubmissionAppointment();
  };

  const canBookCollection = () => {
    return application?.status === 'ready_for_pickup' && !getCollectionAppointment();
  };

  // ADD THIS HANDLER
  const handleCancelAppointment = async (appointmentId) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) {
      return;
    }

    try {
      await appointmentsApi.cancelAppointment(appointmentId);
      toast.success('Appointment cancelled');
      // Refresh appointments
      const appointmentsData = await appointmentsApi.getMyAppointments();
      const appAppointments = appointmentsData.filter(
        apt => apt.application_id === id || apt.application_number === application.application_number
      );
      setAppointments(appAppointments);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to cancel appointment');
    }
  };

  const getUploadedDocuments = () => {
  const docs = [];
  
  if (application.passport_photo_path) {
    docs.push({ type: 'passport_photo', uploaded: true });
  }
  
  if (application.id_document_path) {
    docs.push({ type: 'id_document', uploaded: true });
  }
  
  return docs;
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
        <div className="text-6xl mb-4">❌</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Application Not Found
        </h3>
        <p className="text-gray-600 mb-6">
          The application you're looking for doesn't exist or you don't have access to it.
        </p>
        <Link to="/applicant/applications" className="btn-primary">
          Back to Applications
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <Link to="/applicant/applications" className="text-[#00209F] hover:underline mb-4 inline-block">
          ← Back to Applications
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Application #{application.application_number}
            </h1>
            <p className="text-gray-600 mt-2">
              Submitted on {formatDate(application.submitted_at)}
            </p>
          </div>
          <span className={`px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(application.status)}`}>
            {formatStatus(application.status)}
          </span>
        </div>
      </div>

      {/* Status Timeline */}
      <div className="mb-8">
        <StatusTimeline status={application.status} />
      </div>

      {/* 🎯 ADD APPOINTMENT MANAGEMENT SECTION HERE */}
      {/* Appointment Management Section */}
      <div className="card p-6 mb-8">
        <h3 className="text-xl font-semibold mb-4">📅 Appointments</h3>
        
        {/* Submission Appointment */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">Submission Appointment (Lodge Application)</h4>
            {getSubmissionAppointment() ? (
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                Booked ✓
              </span>
            ) : canBookSubmission() ? (
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                Required
              </span>
            ) : (
              <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-medium">
                N/A
              </span>
            )}
          </div>

          {getSubmissionAppointment() ? (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                <div>
                  <p className="text-gray-600">Date & Time</p>
                  <p className="font-medium">{formatDate(getSubmissionAppointment().scheduled_datetime)}</p>
                </div>
                <div>
                  <p className="text-gray-600">Location</p>
                  <p className="font-medium">{getSubmissionAppointment().location_name}</p>
                </div>
                <div>
                  <p className="text-gray-600">Confirmation Code</p>
                  <p className="font-medium">{getSubmissionAppointment().confirmation_code}</p>
                </div>
                <div>
                  <p className="text-gray-600">Status</p>
                  <p className="font-medium capitalize">{getSubmissionAppointment().status.replace('_', ' ')}</p>
                </div>
              </div>
              
              {getSubmissionAppointment().can_be_rescheduled && (
                <div className="flex gap-2">
                  <Link
                    to={`/applicant/appointments/${getSubmissionAppointment().id}/reschedule?application=${application.id}`}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    🔄 Reschedule
                  </Link>
                  <button
                    onClick={() => handleCancelAppointment(getSubmissionAppointment().id)}
                    className="text-sm text-red-600 hover:text-red-700 font-medium"
                  >
                    ❌ Cancel
                  </button>
                </div>
              )}
            </div>
          ) : canBookSubmission() ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800 mb-3">
                📍 You need to book a submission appointment to lodge your application at the passport office.
              </p>
              <Link
                to={`/applicant/appointments/book-submission?application=${application.id}`}
                className="btn-primary text-sm inline-block"
              >
                📝 Book Submission Appointment
              </Link>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              {application.status === 'submitted' ? 'Loading...' : 'No submission appointment needed at this stage'}
            </p>
          )}
        </div>

        {/* Collection Appointment */}
        <div className="border-t border-gray-200 pt-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">Collection Appointment (Pick Up Passport)</h4>
            {getCollectionAppointment() ? (
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                Booked ✓
              </span>
            ) : canBookCollection() ? (
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                Ready to Book
              </span>
            ) : (
              <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-medium">
                Not Yet Available
              </span>
            )}
          </div>

          {getCollectionAppointment() ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                <div>
                  <p className="text-gray-600">Date & Time</p>
                  <p className="font-medium">{formatDate(getCollectionAppointment().scheduled_datetime)}</p>
                </div>
                <div>
                  <p className="text-gray-600">Location</p>
                  <p className="font-medium">{getCollectionAppointment().location_name}</p>
                </div>
                <div>
                  <p className="text-gray-600">Confirmation Code</p>
                  <p className="font-medium">{getCollectionAppointment().confirmation_code}</p>
                </div>
                <div>
                  <p className="text-gray-600">Status</p>
                  <p className="font-medium capitalize">{getCollectionAppointment().status.replace('_', ' ')}</p>
                </div>
              </div>
              
              {getCollectionAppointment().can_be_rescheduled && (
                <div className="flex gap-2">
                  <Link
                    to={`/applicant/appointments/${getCollectionAppointment().id}/reschedule?application=${application.id}`}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    🔄 Reschedule
                  </Link>
                  <button
                    onClick={() => handleCancelAppointment(getCollectionAppointment().id)}
                    className="text-sm text-red-600 hover:text-red-700 font-medium"
                  >
                    ❌ Cancel
                  </button>
                </div>
              )}
            </div>
          ) : canBookCollection() ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800 mb-3">
                Your passport is ready! Book an appointment to collect it.
              </p>
              <Link
                to={`/applicant/appointments/book-collection?application=${application.id}`}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm inline-block"
              >
                Book Collection Appointment
              </Link>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              Collection appointment will be available once your passport is ready
            </p>
          )}
        </div>
      </div>
      {/* END OF APPOINTMENT SECTION */}
        
      {/* Documents Section */}
      <div className="card p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold">📄 Documents</h3>
          <span className="text-sm text-gray-600">
            {getUploadedDocuments().length} document(s) uploaded
          </span>
        </div>

        {/* Upload Form */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h4 className="font-medium text-gray-900 mb-3">📤 Upload or Replace Documents</h4>
          
          <div className="space-y-4">
            {/* Passport Photo Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Passport Photo {application.passport_photo_path && '(Replace existing)'}
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleFileSelect('passport_photo', e.target.files[0])}
                className="input-field"
              />
              {selectedFiles.passport_photo && (
                <p className="text-sm text-green-600 mt-1">
                  ✓ Selected: {selectedFiles.passport_photo.name}
                </p>
              )}
              {application.passport_photo_path && (
                <p className="text-xs text-gray-500 mt-1">
                  Current: Uploaded ✓
                </p>
              )}
            </div>

            {/* ID Document Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID Document {application.id_document_path && '(Replace existing)'}
              </label>
              <input
                type="file"
                accept="image/*,application/pdf"
                onChange={(e) => handleFileSelect('id_document', e.target.files[0])}
                className="input-field"
              />
              {selectedFiles.id_document && (
                <p className="text-sm text-green-600 mt-1">
                  ✓ Selected: {selectedFiles.id_document.name}
                </p>
              )}
              {application.id_document_path && (
                <p className="text-xs text-gray-500 mt-1">
                  Current: Uploaded ✓
                </p>
              )}
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUploadDocuments}
              disabled={uploading || (!selectedFiles.passport_photo && !selectedFiles.id_document)}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? '⏳ Uploading...' : '📤 Upload Documents'}
            </button>
          </div>
        </div>

        {/* View Documents Button */}
        {getUploadedDocuments().length > 0 ? (
          <div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
              {application.passport_photo_path && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                  <div className="text-2xl mb-1">📷</div>
                  <div className="text-xs font-medium text-gray-700">Passport Photo</div>
                </div>
              )}
              {application.id_document_path && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                  <div className="text-2xl mb-1">🪪</div>
                  <div className="text-xs font-medium text-gray-700">ID Document</div>
                </div>
              )}
            </div>
            
            <button
              onClick={() => setShowDocuments(true)}
              className="btn-outline w-full"
            >
              👁️ View Uploaded Documents
            </button>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-600">
            <div className="text-4xl mb-2">📄</div>
            <p>No documents uploaded yet. Use the form above to upload.</p>
          </div>
        )}
      </div>

      {/* Document Viewer Modal */}
      {showDocuments && (
        <DocumentViewer
          applicationId={application.id}
          documents={getUploadedDocuments()}
          onClose={() => setShowDocuments(false)}
        />
      )}
        
      {/* Application Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Passport Details */}
          <div className="card p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Passport Details</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Passport Type</p>
                <p className="font-medium capitalize">{application.passport_type}</p>
              </div>
              <div>
                <p className="text-gray-600">Pages</p>
                <p className="font-medium">{application.pages}</p>
              </div>
              <div>
                <p className="text-gray-600">Reason for Issuance</p>
                <p className="font-medium capitalize">{application.reason_for_issuance?.replace('_', ' ')}</p>
              </div>
              {application.previous_passport_number && (
                <div>
                  <p className="text-gray-600">Previous Passport Number</p>
                  <p className="font-medium">{application.previous_passport_number}</p>
                </div>
              )}
            </div>
          </div>

          {/* Emergency Contact */}
          {(application.emergency_contact_name || application.emergency_contact_phone) && (
            <div className="card p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Emergency Contact</h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                {application.emergency_contact_name && (
                  <div>
                    <p className="text-gray-600">Name</p>
                    <p className="font-medium">{application.emergency_contact_name}</p>
                  </div>
                )}
                {application.emergency_contact_phone && (
                  <div>
                    <p className="text-gray-600">Phone</p>
                    <p className="font-medium">{application.emergency_contact_phone}</p>
                  </div>
                )}
                {application.emergency_contact_relationship && (
                  <div>
                    <p className="text-gray-600">Relationship</p>
                    <p className="font-medium capitalize">{application.emergency_contact_relationship}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Additional Notes */}
          {application.notes && (
            <div className="card p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Additional Notes</h2>
              <p className="text-gray-700">{application.notes}</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Processing Info */}
          <div className="card p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Processing Information</h2>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-gray-600">Priority Level</p>
                <p className="font-medium capitalize">{application.priority_level}</p>
              </div>
              <div>
                <p className="text-gray-600">Days in Processing</p>
                <p className="font-medium">{application.days_in_processing} days</p>
              </div>
              {application.is_fast_tracked && (
                <div className="bg-purple-50 border border-purple-200 rounded p-3">
                  <p className="text-purple-800 font-medium text-xs">Fast Tracked</p>
                </div>
              )}
              {application.is_overdue && (
                <div className="bg-red-50 border border-red-200 rounded p-3">
                  <p className="text-red-800 font-medium text-xs">Overdue</p>
                </div>
              )}
            </div>
          </div>

          {/* Important Dates */}
          <div className="card p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Important Dates</h2>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-gray-600">Submitted</p>
                <p className="font-medium">{formatDate(application.submitted_at)}</p>
              </div>
              {application.estimated_completion_date && (
                <div>
                  <p className="text-gray-600">Estimated Completion</p>
                  <p className="font-medium">{formatDate(application.estimated_completion_date)}</p>
                </div>
              )}
              {application.actual_completion_date && (
                <div>
                  <p className="text-gray-600">Completed</p>
                  <p className="font-medium">{formatDate(application.actual_completion_date)}</p>
                </div>
              )}
              {application.pickup_deadline && (
                <div>
                  <p className="text-gray-600">Pickup Deadline</p>
                  <p className="font-medium">{formatDate(application.pickup_deadline)}</p>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          {application.status === 'ready_for_pickup' && (
            <div className="card p-6 bg-green-50 border-green-200">
              <h3 className="font-bold text-gray-900 mb-2">Ready for Pickup</h3>
              <p className="text-sm text-gray-700 mb-4">
                Your passport is ready! Schedule a pickup appointment.
              </p>
              <button className="btn-primary w-full">
                Schedule Pickup
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}        
