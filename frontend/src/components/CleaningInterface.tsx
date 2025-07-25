import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useAuth } from '../contexts/AuthContext';
import { UsageIndicator } from './UsageIndicator';
import { SignupPrompt } from './SignupPrompt';
import { CleaningResults } from './CleaningResults';

export const CleaningInterface: React.FC = () => {
  const { user, usageInfo, refreshUsage } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [instructions, setInstructions] = useState('');
  const [result, setResult] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSignupPrompt, setShowSignupPrompt] = useState(false);
  const [error, setError] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const csvFile = acceptedFiles[0];
    if (csvFile) {
      setFile(csvFile);
      setError('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv']
    },
    maxFiles: 1
  });

  const handleCleanCSV = async () => {
    if (!file) return;
    
    setIsProcessing(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_instructions', instructions);
    
    try {
      const response = await fetch('/upload-csv', {
        method: 'POST',
        body: formData,
        headers: user ? { 
          'Authorization': `Bearer ${localStorage.getItem('token')}` 
        } : {}
      });
      
      if (response.status === 402) {
        const errorData = await response.json();
        if (errorData.detail?.error === 'free_limit_reached') {
          setShowSignupPrompt(true);
          return;
        }
        throw new Error(errorData.detail?.message || 'Payment required');
      }
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Processing failed');
      }
      
      const data = await response.json();
      setResult(data);
      
      // Refresh usage info
      await refreshUsage();
      
      // Show signup prompt if approaching limit
      if (!user && data.usage_info?.show_signup_prompt) {
        setTimeout(() => setShowSignupPrompt(true), 2000); // Show after results
      }
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const canUpload = user || (usageInfo && !usageInfo.needs_signup);
  const fileSizeMB = file ? file.size / (1024 * 1024) : 0;
  const fileSizeKB = file ? file.size / 1024 : 0;
  const fileSizeDisplay = fileSizeMB < 0.01 ? `${fileSizeKB.toFixed(1)}KB` : `${fileSizeMB.toFixed(1)}MB`;
  const maxSize = user ? (usageInfo?.file_size_limit_mb || 100) : 10;
  


  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Clean Your CSV Files in Seconds
        </h1>
        <p className="text-xl text-gray-600">
          {user ? 
            "Upload, clean, and download - powered by AI" :
            "3 free cleanings, no signup required • AI-powered suggestions"
          }
        </p>
      </div>

      <UsageIndicator />

      {/* File Upload Area */}
      <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
        <div 
          {...getRootProps()} 
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            isDragActive ? 'border-blue-500 bg-blue-50' : 
            canUpload ? 'border-gray-300 hover:border-blue-400' : 'border-gray-200 bg-gray-50'
          }`}
        >
          <input {...getInputProps()} disabled={!canUpload} />
          
          <div className="mb-4">
            <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          
          {file ? (
            <div className="text-green-600">
              <p className="font-semibold">{file.name}</p>
              <p className="text-sm">Size: {fileSizeDisplay} {fileSizeMB > maxSize && <span className="text-red-500">(Too large!)</span>}</p>
            </div>
          ) : (
            <div>
              <p className="text-lg font-medium text-gray-900 mb-2">
                {canUpload ? 
                  (isDragActive ? "Drop your CSV file here" : "Drag & drop your CSV file here") :
                  "Sign up to continue cleaning files"
                }
              </p>
              <p className="text-gray-500">
                {canUpload ? `Max file size: ${maxSize}MB` : "You've used all 3 free cleanings"}
              </p>
            </div>
          )}
        </div>

        {/* AI Instructions */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What do you want to clean? {!user && "(Basic cleaning for anonymous users)"}
          </label>
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder={user ? 
              "Examples:\n• Remove duplicate customers\n• Fix phone number formats\n• Standardize all dates\n• Remove rows where age > 100" :
              "Basic cleaning only:\n• Remove duplicates\n• Remove empty rows\n• Basic type conversion\n\nSign up for AI-powered cleaning!"
            }
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={4}
            disabled={!canUpload}
          />
        </div>

        {/* Clean Button */}
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {!user && canUpload && usageInfo && (
              <span>Free cleanings remaining: {usageInfo.files_remaining}</span>
            )}
          </div>
          
          <button
            onClick={handleCleanCSV}
            disabled={!file || isProcessing || !canUpload || (file && fileSizeMB > maxSize)}
            className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {!canUpload ? 'Sign Up to Continue' :
             isProcessing ? (
               <span className="flex items-center">
                 <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                   <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                   <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                 </svg>
                 Cleaning...
               </span>
             ) : 'Clean My CSV'}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}
      </div>

      {/* Results */}
      {result && <CleaningResults result={result} />}

      {/* Signup Prompt */}
      <SignupPrompt 
        isOpen={showSignupPrompt}
        onClose={() => setShowSignupPrompt(false)}
        filesUsed={usageInfo?.files_used || 3}
      />
    </div>
  );
}; 