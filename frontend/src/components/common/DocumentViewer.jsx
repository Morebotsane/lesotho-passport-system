import { useState, useEffect, useCallback } from 'react';
import { X } from 'lucide-react';
import { toast } from 'react-hot-toast';  // ADD THIS IMPORT
import applicationsApi from '../../api/applications';

export default function DocumentViewer({ applicationId, documents, onClose }) {
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [documentUrl, setDocumentUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  // FIX: Wrap in useCallback to avoid dependency warning
  const loadDocument = useCallback(async (docType) => {
    setLoading(true);
    try {
      const url = await applicationsApi.getDocument(applicationId, docType);
      setDocumentUrl(url);
    } catch (error) {
      console.error('Error loading document:', error);
      toast.error('Failed to load document');
    } finally {
      setLoading(false);
    }
  }, [applicationId]);  // Only depends on applicationId

  // Load document when selected
  useEffect(() => {
    if (selectedDoc) {
      loadDocument(selectedDoc.type);
    } else {
      setDocumentUrl(null);
    }
  }, [selectedDoc, loadDocument]);  // FIX: Add loadDocument to dependencies

  const getDocumentIcon = (docType) => {
    const icons = {
      passport_photo: '📷',
      id_document: '🪪',
      previous_passport: '📘'
    };
    return icons[docType] || '📄';
  };

  const getDocumentName = (docType) => {
    const names = {
      passport_photo: 'Passport Photo',
      id_document: 'ID Document',
      previous_passport: 'Previous Passport'
    };
    return names[docType] || docType;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">Application Documents</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {!selectedDoc ? (
            // Document list
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {documents.map((doc) => (
                <button
                  key={doc.type}
                  onClick={() => setSelectedDoc(doc)}
                  className="card p-6 hover:shadow-lg transition text-left"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-4xl">{getDocumentIcon(doc.type)}</span>
                    <div>
                      <h4 className="font-semibold text-gray-900">
                        {getDocumentName(doc.type)}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {doc.uploaded ? 'Click to view' : 'Not uploaded'}
                      </p>
                    </div>
                  </div>
                </button>
              ))}

              {documents.length === 0 && (
                <div className="col-span-2 text-center py-12">
                  <div className="text-6xl mb-4">📄</div>
                  <p className="text-gray-600">No documents uploaded yet</p>
                </div>
              )}
            </div>
          ) : (
            // Document viewer
            <div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="text-[#00209F] hover:underline mb-4"
              >
                ← Back to documents
              </button>

              <div className="bg-gray-100 rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-lg mb-2">
                  {getDocumentIcon(selectedDoc.type)} {getDocumentName(selectedDoc.type)}
                </h4>
              </div>

              {/* Image/PDF viewer */}
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : documentUrl ? (
                <div className="bg-white border rounded-lg p-4">
                  {selectedDoc.type === 'passport_photo' ? (
                    <img
                      src={documentUrl}
                      alt={getDocumentName(selectedDoc.type)}
                      className="max-w-full h-auto mx-auto"
                      style={{ maxHeight: '60vh' }}
                    />
                  ) : (
                    <iframe
                      src={documentUrl}
                      className="w-full border-0"
                      style={{ height: '60vh' }}
                      title={getDocumentName(selectedDoc.type)}
                    />
                  )}

                  <div className="mt-4 flex gap-3">
                    <a>
                      href={documentUrl}
                      download={`${getDocumentName(selectedDoc.type)}.${selectedDoc.type === 'passport_photo' ? 'png' : 'pdf'}`}
                      className="btn-primary"
                      📥 Download
                    </a>
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}