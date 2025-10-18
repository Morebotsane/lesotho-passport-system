const STATUSES = [
  { key: 'submitted', label: 'Submitted', icon: '📝' },
  { key: 'under_review', label: 'Under Review', icon: '🔍' },
  { key: 'processing', label: 'Processing', icon: '⚙️' },
  { key: 'quality_check', label: 'Quality Check', icon: '✓' },
  { key: 'ready_for_pickup', label: 'Ready for Pickup', icon: '📦' },
  { key: 'collected', label: 'Collected', icon: '✅' }
];

export default function StatusTimeline({ status }) {
  const currentIndex = STATUSES.findIndex(s => s.key === status);
  
  const isCompleted = (index) => index <= currentIndex;
  const isCurrent = (index) => index === currentIndex;

  return (
    <div className="card p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Application Progress</h2>
      
      <div className="relative">
        {STATUSES.map((step, index) => (
          <div key={step.key} className="flex items-start mb-8 last:mb-0">
            {/* Icon */}
            <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-xl border-2 ${
              isCompleted(index)
                ? 'bg-[#00209F] border-[#00209F] text-white'
                : 'bg-gray-100 border-gray-300 text-gray-400'
            }`}>
              {step.icon}
            </div>

            {/* Content */}
            <div className="ml-4 flex-1">
              <h3 className={`font-semibold ${
                isCompleted(index) ? 'text-gray-900' : 'text-gray-400'
              }`}>
                {step.label}
              </h3>
              {isCurrent(index) && (
                <p className="text-sm text-[#00209F] font-medium mt-1">
                  Current Status
                </p>
              )}
            </div>

            {/* Connecting Line */}
            {index < STATUSES.length - 1 && (
              <div className={`absolute left-6 w-0.5 h-8 ${
                isCompleted(index) ? 'bg-[#00209F]' : 'bg-gray-300'
              }`} style={{ top: `${(index + 1) * 5}rem` }} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}