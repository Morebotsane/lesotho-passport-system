import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import applicationsApi from '../../api/applications';
import { toast } from 'react-hot-toast';
import DocumentViewer from '../../components/common/DocumentViewer';

export default function OfficerApplicationDetail() {
  const { id } = useParams();
  //const navigate = useNavigate();
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDocuments, setShowDocuments] = useState(false);

  useEffect(() => {
    const fetchApplication = async () => {
      try {
        const data = await applicationsApi.getById(id);
        setApplication(data);
      } catch (error) {
        console.error('Error:', error);
        toast.error('Failed to load application');
      } finally {
        setLoading(false);
      }
    };

    fetchApplication();
  }, [id]);

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
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!application) {
    return <div className="text-center py-12">Application not found</div>;
  }

  return (
    <div>
      <div className="mb-8">
        <Link to="/officer/queue" className="text-[#00209F] hover:underline mb-4 inline-block">
          ← Back to Queue
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">
          Application #{application.application_number}
        </h1>
        <p className="text-gray-600 mt-2">
          Applicant: {application.first_name} {application.last_name}
        </p>
      </div>

      {/* Show all application details here - similar to applicant view but officer perspective */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="font-semibold text-lg mb-4">Personal Information</h3>
          <div className="space-y-2 text-sm">
            <div><span className="text-gray-600">Name:</span> {application.first_name} {application.last_name}</div>
            <div><span className="text-gray-600">Email:</span> {application.email}</div>
            <div><span className="text-gray-600">Phone:</span> {application.phone}</div>
            <div><span className="text-gray-600">Date of Birth:</span> {application.date_of_birth}</div>
            <div><span className="text-gray-600">Address:</span> {application.residential_address}</div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="font-semibold text-lg mb-4">Passport Details</h3>
          <div className="space-y-2 text-sm">
            <div><span className="text-gray-600">Type:</span> {application.passport_type}</div>
            <div><span className="text-gray-600">Reason:</span> {application.reason_for_issuance}</div>
            <div><span className="text-gray-600">Status:</span> {application.status}</div>
          </div>
        </div>
      </div>

      {/* Documents Card */}
      <div className="card p-6">
        <h3 className="font-semibold text-lg mb-4">📄 Documents</h3>
        
        {getUploadedDocuments().length > 0 ? (
          <button
            onClick={() => setShowDocuments(true)}
            className="btn-primary w-full"
          >
            View Documents ({getUploadedDocuments().length})
          </button>
        ) : (
          <p className="text-gray-600 text-sm">No documents uploaded</p>
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

      {/* Officer Actions */}
      <div className="card p-6 mt-6">
        <h3 className="font-semibold text-lg mb-4">Officer Actions</h3>
        <div className="flex gap-3">
          <Link
            to={`/officer/process/${application.id}`}
            className="btn-primary"
          >
            Process Application
          </Link>
        </div>
      </div>
    </div>
  );
}