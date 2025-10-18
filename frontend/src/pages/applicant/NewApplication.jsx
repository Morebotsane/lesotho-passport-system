import ApplicationForm from '../../components/applicant/ApplicationForm';

export default function NewApplication() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">New Passport Application</h1>
        <p className="text-gray-600 mt-2">
          Complete the form below to apply for a new Lesotho passport
        </p>
      </div>
      
      <ApplicationForm />
    </div>
  );
}