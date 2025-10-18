import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';

// Auth Pages
import Login from './pages/auth/Login';
import Signup from './pages/auth/Signup';

// Admin pages
import AdminLayout from './layouts/AdminLayout';
import AdminDashboard from './pages/admin/Dashboard';
import EditOfficer from './pages/admin/EditOfficer';
import AppointmentSettings from './pages/admin/AppointmentSettings';

// Layouts
import ApplicantLayout from './layouts/ApplicantLayout';

// Applicant Pages
import Dashboard from './pages/applicant/Dashboard';
import NewApplication from './pages/applicant/NewApplication';
import MyApplications from './pages/applicant/MyApplications';
import ApplicationDetail from './pages/applicant/ApplicationDetail';
import MyAppointments from './pages/applicant/MyAppointments';
import BookAppointment from './pages/applicant/BookAppointment';
import BookSubmissionAppointment from './pages/applicant/BookSubmissionAppointment';
import RescheduleAppointment from './pages/applicant/RescheduleAppointment';


// Officer pages
import OfficerLayout from './layouts/OfficerLayout';
import OfficerDashboard from './pages/officer/Dashboard';
import ApplicationQueue from './pages/officer/ApplicationQueue';
import ProcessApplication from './pages/officer/ProcessApplication';
import Officers from './pages/admin/Officers';
import CreateOfficer from './pages/admin/CreateOfficer';
import DailySchedule from './pages/officer/DailySchedule'; 
import OfficerApplicationDetail from './pages/officer/ApplicationDetail';

// Temporary dashboards for officer/admin (we'll build these later)
function TemporaryDashboard() {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="card max-w-2xl mx-auto p-8">
        <h1 className="text-2xl font-bold mb-4">Welcome, {user?.first_name}!</h1>
        <p className="text-gray-600 mb-4">Role: {user?.role}</p>
        <p className="text-gray-600 mb-6">{user?.role} dashboard coming soon...</p>
      </div>
    </div>
  );
}

function App() {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00209F] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Applicant Routes (with layout) */}
      <Route path="/applicant" element={<ApplicantLayout />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="applications/new" element={<NewApplication />} />
        <Route path="applications" element={<MyApplications />} />
        <Route path="applications/:id" element={<ApplicationDetail />} />
        <Route path="appointments" element={<MyAppointments />} />
        <Route path="appointments/book" element={<BookAppointment />} />
        <Route path="appointments/book-submission" element={<BookSubmissionAppointment />} />
        <Route path="appointments/:id/reschedule" element={<RescheduleAppointment />} /> 
      </Route>

      {/* Officer and Admin routes (temporary) */}
      <Route path="/officer" element={<OfficerLayout />}>
        <Route path="dashboard" element={<OfficerDashboard />} />
        <Route path="queue" element={<ApplicationQueue />} />
        <Route path="applications/:id" element={<OfficerApplicationDetail />} /> 
        <Route path="process/:id" element={<ProcessApplication />} />
        <Route path="schedule" element={<DailySchedule />} />
      </Route>

      <Route path="/admin" element={<AdminLayout />}>
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="officers" element={<Officers />} />
        <Route path="officers/new" element={<CreateOfficer />} />
        <Route path="officers/:id/edit" element={<EditOfficer />} />
        <Route path="appointments" element={<AppointmentSettings />} />
      </Route>

      {/* Default Route */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      
      {/* Catch all */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
