import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export const UsageIndicator: React.FC = () => {
  const { usageInfo } = useAuth();

  if (!usageInfo) return null;

  if (usageInfo.user_type === 'anonymous') {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-blue-900">Free Usage</h3>
            <p className="text-sm text-blue-700">
              {usageInfo.files_used} of 3 free cleanings used this month
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-16 bg-blue-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(usageInfo.files_used / 3) * 100}%` }}
              />
            </div>
            <span className="text-sm font-medium text-blue-900">
              {usageInfo.files_remaining} left
            </span>
          </div>
        </div>
        {usageInfo.needs_signup && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              You've used all free cleanings. Sign up for unlimited access!
            </p>
          </div>
        )}
      </div>
    );
  }

  // Registered user
  const usagePercentage = usageInfo.files_limit === -1 
    ? 0 
    : (usageInfo.files_used / (usageInfo.files_limit || 1)) * 100;

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-green-900">
            {(usageInfo.plan || 'Free').charAt(0).toUpperCase() + (usageInfo.plan || 'Free').slice(1)} Plan
          </h3>
          <p className="text-sm text-green-700">
            {usageInfo.files_used} of {usageInfo.files_limit === -1 ? '∞' : usageInfo.files_limit} files processed this month
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {usageInfo.files_limit !== -1 && (
            <div className="w-16 bg-green-200 rounded-full h-2">
              <div 
                className="bg-green-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(usagePercentage, 100)}%` }}
              />
            </div>
          )}
          <span className="text-sm font-medium text-green-900">
            {usageInfo.files_limit === -1 ? 'Unlimited' : `${(usageInfo.files_limit || 0) - usageInfo.files_used} left`}
          </span>
        </div>
      </div>
    </div>
  );
}; 