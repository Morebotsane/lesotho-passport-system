import { useState, useEffect } from 'react';
import applicationsApi from '../../api/applications';
import appointmentsApi from '../../api/appointments';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const STEPS = [
  { id: 1, name: 'Personal Information', icon: '👤' },
  { id: 2, name: 'Passport Details', icon: '📘' },
  { id: 3, name: 'Document Upload', icon: '📎' },
  { id: 4, name: 'Review & Submit', icon: '✅' }
];

export default function ApplicationForm() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [locations, setLocations] = useState([]); 
  const [locationsLoading, setLocationsLoading] = useState(true); 
  
  const [formData, setFormData] = useState({
    // Personal info
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    place_of_birth: '',
    nationality: 'Lesotho',
    gender: '', 
    residential_address: '',
    submission_location_id: '',
    
    // Emergency contact - ADD THESE THREE
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    
    // Passport details
    passport_type: 'regular',
    reason_for_issuance: '',
    previous_passport_number: '',
    
    // Documents
    photo: null,
    id_document: null,
    
    // Additional
    notes: ''
  });

  useEffect(() => {
  const fetchLocations = async () => {
    try {
      const data = await appointmentsApi.getLocations(true);
      setLocations(data);
    } catch (error) {
      console.error('Error fetching locations:', error);
      toast.error('Failed to load locations');
    } finally {
      setLocationsLoading(false);
    }
  };
  
  fetchLocations();
}, []);

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleFileChange = (e) => {
    const { name, files } = e.target;
    if (files && files[0]) {
      setFormData(prev => ({ ...prev, [name]: files[0] }));
      if (errors[name]) {
        setErrors(prev => ({ ...prev, [name]: '' }));
      }
    }
  };

  const validateStep = (step) => {
    const newErrors = {};
    
    if (step === 1) {
      if (!formData.first_name) newErrors.first_name = 'First name is required';
      if (!formData.last_name) newErrors.last_name = 'Last name is required';
      if (!formData.gender) newErrors.gender = 'Gender is required';
      if (!formData.email) newErrors.email = 'Email is required';
      if (!formData.phone) newErrors.phone = 'Phone is required';
      if (!formData.date_of_birth) newErrors.date_of_birth = 'Date of birth is required';
      if (!formData.place_of_birth) newErrors.place_of_birth = 'Place of birth is required';
      if (!formData.residential_address) newErrors.residential_address = 'Address is required';
        if (!formData.submission_location_id) newErrors.submission_location_id = 'Office location is required';  // A
    }
    
    if (step === 2) {
      if (!formData.reason_for_issuance) newErrors.reason_for_issuance = 'Reason is required';
    }
    
    if (step === 3) {
      if (!formData.photo) newErrors.photo = 'Passport photo is required';
      if (!formData.id_document) newErrors.id_document = 'ID document is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, STEPS.length));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

const handleSubmit = async () => {
  if (!validateStep(currentStep)) return;

  setIsSubmitting(true);
  try {
    // Step 1: Submit application data (without files)
    const applicationData = {
      first_name: formData.first_name,
      last_name: formData.last_name,
      gender: formData.gender,
      email: formData.email,
      phone: formData.phone,
      date_of_birth: formData.date_of_birth,
      place_of_birth: formData.place_of_birth,
      nationality: formData.nationality,
      residential_address: formData.residential_address,
      submission_location_id: formData.submission_location_id,
      emergency_contact_name: formData.emergency_contact_name || undefined,
      emergency_contact_phone: formData.emergency_contact_phone || undefined,
      emergency_contact_relationship: formData.emergency_contact_relationship || undefined,
      passport_type: formData.passport_type,
      pages: 32,
      reason_for_issuance: formData.reason_for_issuance.toLowerCase(),
      previous_passport_number: formData.previous_passport_number || undefined,
      notes: formData.notes || undefined
    };

    console.log('📝 Creating application...');
    const response = await applicationsApi.create(applicationData);
    console.log('✅ Application created:', response.id);
    
    // Step 2: Upload documents if any
    console.log('📎 Checking for documents...');
    console.log('Photo:', formData.photo);
    console.log('ID Doc:', formData.id_document);
    
    if (formData.photo || formData.id_document) {
      console.log('📤 Uploading documents...');
      const formDataFiles = new FormData();
      
      if (formData.photo) {
        formDataFiles.append('passport_photo', formData.photo);
        console.log('Added passport_photo');
      }
      
      if (formData.id_document) {
        formDataFiles.append('id_document', formData.id_document);
        console.log('Added id_document');
      }
      
      try {
        const uploadResponse = await applicationsApi.uploadDocuments(response.id, formDataFiles);
        console.log('✅ Documents uploaded:', uploadResponse);
      } catch (uploadError) {
        console.error('❌ Document upload failed:', uploadError);
        toast.error('Documents failed to upload, but application was created');
      }
    } else {
      console.log('⚠️ No documents to upload');
    }
    
    toast.success(
      `Application submitted successfully! Application #: ${response.application_number}`,
      {
        duration: 5000,
        style: {
          background: '#009543',
          color: 'white',
        }
      }
    );
    
    navigate(`/applicant/appointments/book-submission?application=${response.id}`);
    
  } catch (error) {
    console.error('❌ Submission error:', error);
    toast.error(error.response?.data?.detail || 'Failed to submit application');
  } finally {
    setIsSubmitting(false);
  }
};

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          {STEPS.map((step, index) => (
            <div key={step.id} className="flex-1">
              <div className="flex items-center">
                <div className={`flex items-center justify-center w-12 h-12 rounded-full text-2xl
                  ${currentStep >= step.id 
                    ? 'bg-[#00209F] text-white' 
                    : 'bg-gray-200 text-gray-400'
                  }`}>
                  {step.icon}
                </div>
                <div className="ml-3 flex-1">
                  <p className={`text-sm font-medium ${
                    currentStep >= step.id ? 'text-[#00209F]' : 'text-gray-400'
                  }`}>
                    Step {step.id}
                  </p>
                  <p className="text-xs text-gray-500">{step.name}</p>
                </div>
                {index < STEPS.length - 1 && (
                  <div className={`h-1 flex-1 mx-4 ${
                    currentStep > step.id ? 'bg-[#00209F]' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Form Content */}
      <div className="card p-8">
        {/* Step 1: Personal Information */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Personal Information</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className={`input-field ${errors.first_name ? 'border-red-500' : ''}`}
                />
                {errors.first_name && (
                  <p className="text-red-500 text-sm mt-1">{errors.first_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name *
                </label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className={`input-field ${errors.last_name ? 'border-red-500' : ''}`}
                />
                {errors.last_name && (
                  <p className="text-red-500 text-sm mt-1">{errors.last_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gender *
                </label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className={`input-field ${errors.gender ? 'border-red-500' : ''}`}
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
                {errors.gender && (
                  <p className="text-red-500 text-sm mt-1">{errors.gender}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date of Birth *
                </label>
                <input
                  type="date"
                  name="date_of_birth"
                  value={formData.date_of_birth}
                  onChange={handleChange}
                  className={`input-field ${errors.date_of_birth ? 'border-red-500' : ''}`}
                />
                {errors.date_of_birth && (
                  <p className="text-red-500 text-sm mt-1">{errors.date_of_birth}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Place of Birth *
                </label>
                <input
                  type="text"
                  name="place_of_birth"
                  value={formData.place_of_birth}
                  onChange={handleChange}
                  placeholder="City, Country"
                  className={`input-field ${errors.place_of_birth ? 'border-red-500' : ''}`}
                />
                {errors.place_of_birth && (
                  <p className="text-red-500 text-sm mt-1">{errors.place_of_birth}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`input-field ${errors.email ? 'border-red-500' : ''}`}
                />
                {errors.email && (
                  <p className="text-red-500 text-sm mt-1">{errors.email}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number *
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="5XXXXXXX"
                  className={`input-field ${errors.phone ? 'border-red-500' : ''}`}
                />
                {errors.phone && (
                  <p className="text-red-500 text-sm mt-1">{errors.phone}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Residential Address *
                </label>
                <input
                  type="text"
                  name="residential_address"
                  value={formData.residential_address}
                  onChange={handleChange}
                  placeholder="Street, City, District"
                  className={`input-field ${errors.residential_address ? 'border-red-500' : ''}`}
                />
                {errors.residential_address && (
                  <p className="text-red-500 text-sm mt-1">{errors.residential_address}</p>
                )}
              </div>
            </div>

            {/* ADD THIS ENTIRE BLOCK */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Passport Office *
              </label>
              <select
                name="submission_location_id"
                value={formData.submission_location_id}
                onChange={handleChange}
                disabled={locationsLoading}
                className={`input-field ${errors.submission_location_id ? 'border-red-500' : ''}`}
                >
                <option value="">Select office location...</option>
                {locations.map(loc => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name} - {loc.address}
                  </option>
                ))}
              </select>
              {errors.submission_location_id && (
                <p className="text-red-500 text-sm mt-1">{errors.submission_location_id}</p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                📍 Select where you'll submit your application for processing
              </p>
            </div>

            {/* Emergency Contact Section */}
            <div className="border-t border-gray-200 pt-6 mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Emergency Contact</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Emergency Contact Name
                  </label>
                  <input
                    type="text"
                    name="emergency_contact_name"
                    value={formData.emergency_contact_name}
                    onChange={handleChange}
                    placeholder="Full name"
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Emergency Contact Phone
                  </label>
                  <input
                    type="tel"
                    name="emergency_contact_phone"
                    value={formData.emergency_contact_phone}
                    onChange={handleChange}
                    placeholder="5XXXXXXX"
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Relationship
                  </label>
                  <select
                    name="emergency_contact_relationship"
                    value={formData.emergency_contact_relationship}
                    onChange={handleChange}
                    className="input-field"
                  >
                    <option value="">Select relationship</option>
                    <option value="spouse">Spouse</option>
                    <option value="parent">Parent</option>
                    <option value="sibling">Sibling</option>
                    <option value="child">Child</option>
                    <option value="friend">Friend</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Passport Details */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Passport Details</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Passport Type *
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition ${
                  formData.passport_type === 'regular'
                    ? 'border-[#00209F] bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <input
                    type="radio"
                    name="passport_type"
                    value="regular"
                    checked={formData.passport_type === 'regular'}
                    onChange={handleChange}
                    className="mr-3"
                  />
                  <div>
                    <p className="font-medium">Regular Passport</p>
                    <p className="text-sm text-gray-600">Standard processing time</p>
                  </div>
                </label>

                <label className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition ${
                  formData.passport_type === 'diplomatic'
                    ? 'border-[#00209F] bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <input
                    type="radio"
                    name="passport_type"
                    value="diplomatic"
                    checked={formData.passport_type === 'diplomatic'}
                    onChange={handleChange}
                    className="mr-3"
                  />
                  <div>
                    <p className="font-medium">Diplomatic Passport</p>
                    <p className="text-sm text-gray-600">For official use</p>
                  </div>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason for Issuance *
              </label>
              <select
                name="reason_for_issuance"
                value={formData.reason_for_issuance}
                onChange={handleChange}
                className={`input-field ${errors.reason_for_issuance ? 'border-red-500' : ''}`}
              >
                <option value="">Select a reason</option>
                <option value="new">New Passport</option>
                <option value="renewal">Renewal</option>
                <option value="lost">Lost/Stolen</option>
                <option value="damaged">Damaged</option>
                <option value="name_change">Name Change</option>
              </select>
              {errors.reason_for_issuance && (
                <p className="text-red-500 text-sm mt-1">{errors.reason_for_issuance}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Previous Passport Number (if applicable)
              </label>
              <input
                type="text"
                name="previous_passport_number"
                value={formData.previous_passport_number}
                onChange={handleChange}
                placeholder="e.g., A1234567"
                className="input-field"
              />
            </div>
          </div>
        )}

        {/* Step 3: Document Upload */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Document Upload</h2>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-sm text-blue-800">
                Required Documents: Please upload clear, readable copies
              </p>
              <ul className="text-sm text-blue-700 mt-2 ml-6 list-disc">
                <li>Passport-sized photograph (white background)</li>
                <li>National ID or Birth Certificate</li>
              </ul>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Passport Photo * (JPEG/PNG, max 5MB)
              </label>
              <input
                type="file"
                name="photo"
                accept="image/*"
                onChange={handleFileChange}
                className={`input-field ${errors.photo ? 'border-red-500' : ''}`}
              />
              {errors.photo && (
                <p className="text-red-500 text-sm mt-1">{errors.photo}</p>
              )}
              {formData.photo && (
                <p className="text-green-600 text-sm mt-2">{formData.photo.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID Document * (JPEG/PNG/PDF, max 5MB)
              </label>
              <input
                type="file"
                name="id_document"
                accept="image/*,application/pdf"
                onChange={handleFileChange}
                className={`input-field ${errors.id_document ? 'border-red-500' : ''}`}
              />
              {errors.id_document && (
                <p className="text-red-500 text-sm mt-1">{errors.id_document}</p>
              )}
              {formData.id_document && (
                <p className="text-green-600 text-sm mt-2">{formData.id_document.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Notes (optional)
              </label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                rows={4}
                placeholder="Any additional information..."
                className="input-field"
              />
            </div>
          </div>
        )}

        {/* Step 4: Review & Submit */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Review Your Application</h2>
            
            <div className="space-y-4">
              <div className="card bg-gray-50">
                <h3 className="font-semibold text-lg mb-3">Personal Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Name:</p>
                    <p className="font-medium">{formData.first_name} {formData.last_name}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Email:</p>
                    <p className="font-medium">{formData.email}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Phone:</p>
                    <p className="font-medium">{formData.phone}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Date of Birth:</p>
                    <p className="font-medium">{formData.date_of_birth}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Place of Birth:</p>
                    <p className="font-medium">{formData.place_of_birth}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Address:</p>
                    <p className="font-medium">{formData.residential_address}</p>
                  </div>
                </div>
              </div>

              <div className="card bg-gray-50">
                <h3 className="font-semibold text-lg mb-3">Passport Details</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Type:</p>
                    <p className="font-medium capitalize">{formData.passport_type}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Reason:</p>
                    <p className="font-medium capitalize">{formData.reason_for_issuance.replace('_', ' ')}</p>
                  </div>
                  {formData.previous_passport_number && (
                    <div>
                      <p className="text-gray-600">Previous Passport:</p>
                      <p className="font-medium">{formData.previous_passport_number}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="card bg-gray-50">
                <h3 className="font-semibold text-lg mb-3">Uploaded Documents</h3>
                <div className="space-y-2 text-sm">
                  <p className="text-green-600">Passport Photo: {formData.photo?.name}</p>
                  <p className="text-green-600">ID Document: {formData.id_document?.name}</p>
                </div>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                Before submitting: Please ensure all information is correct. 
                You will receive SMS notifications about your application status.
              </p>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={prevStep}
            disabled={currentStep === 1}
            className="btn-outline disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          {currentStep < STEPS.length ? (
            <button onClick={nextStep} className="btn-primary">
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="btn-primary disabled:opacity-50"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Application'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}