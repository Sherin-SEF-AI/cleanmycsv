import React, { useEffect, useState } from 'react';

interface CleaningResultsProps {
  result: any;
}

// Confetti component
const Confetti: React.FC = () => {
  const [particles, setParticles] = useState<Array<{
    id: number;
    x: number;
    y: number;
    color: string;
    size: number;
    speed: number;
  }>>([]);

  useEffect(() => {
    const colors = ['#fbbf24', '#34d399', '#60a5fa', '#f87171', '#a78bfa'];
    const newParticles = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * window.innerWidth,
      y: -20,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: Math.random() * 8 + 4,
      speed: Math.random() * 3 + 2,
    }));
    setParticles(newParticles);

    const interval = setInterval(() => {
      setParticles(prev => 
        prev.map(particle => ({
          ...particle,
          y: particle.y + particle.speed,
        })).filter(particle => particle.y < window.innerHeight + 50)
      );
    }, 50);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {particles.map(particle => (
        <div
          key={particle.id}
          className="absolute w-2 h-2 rounded-full animate-bounce"
          style={{
            left: particle.x,
            top: particle.y,
            backgroundColor: particle.color,
            width: particle.size,
            height: particle.size,
          }}
        />
      ))}
    </div>
  );
};

export const CleaningResults: React.FC<CleaningResultsProps> = ({ result }) => {
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    setShowConfetti(true);
    const timer = setTimeout(() => setShowConfetti(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  const handleDownload = () => {
    const blob = new Blob([result.download_csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cleaned_data.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const report = result.report;
  const qualityImprovement = report.data_quality_score_after - report.data_quality_score_before;
  const isQualityImproved = qualityImprovement > 0;

  return (
    <>
      {showConfetti && <Confetti />}
      
      <div className="bg-white rounded-xl shadow-lg p-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mr-3">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900">Cleaning Complete!</h2>
          </div>
          <p className="text-gray-600">Your CSV has been successfully cleaned and optimized</p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{report.original_rows}</div>
            <div className="text-sm text-gray-600">Original Rows</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{report.final_rows}</div>
            <div className="text-sm text-gray-600">Final Rows</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{report.rows_removed}</div>
            <div className="text-sm text-gray-600">Rows Removed</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{report.data_quality_score_after}%</div>
            <div className="text-sm text-gray-600">Quality Score</div>
          </div>
        </div>

        {/* Quality Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Data Quality</span>
            <span className="text-sm text-gray-500">
              {isQualityImproved ? '+' : ''}{qualityImprovement.toFixed(1)}%
            </span>
          </div>
          <div className="relative bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-1000 ${
                isQualityImproved ? 'bg-green-500' : 'bg-gray-400'
              }`}
              style={{ width: `${report.data_quality_score_after}%` }}
            />
            <div 
              className="absolute top-0 h-2 bg-gray-300 rounded-full transition-all duration-1000"
              style={{ width: `${report.data_quality_score_before}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Before: {report.data_quality_score_before}%</span>
            <span>After: {report.data_quality_score_after}%</span>
          </div>
        </div>

        {/* Operations */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Operations Applied</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {report.operations_performed.map((operation: string, index: number) => (
              <div key={index} className="flex items-center p-3 bg-green-50 rounded-lg">
                <svg className="w-4 h-4 text-green-600 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="text-sm text-gray-700">{operation}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Issues Found */}
        {report.issues_found && report.issues_found.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Issues Detected</h3>
            <div className="space-y-2">
              {report.issues_found.map((issue: string, index: number) => (
                <div key={index} className="flex items-center p-3 bg-yellow-50 rounded-lg">
                  <svg className="w-4 h-4 text-yellow-600 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">{issue}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* LLM Error */}
        {report.llm_error && (
          <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-blue-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-blue-800">AI features temporarily unavailable. Basic cleaning applied.</span>
            </div>
          </div>
        )}

        {/* Download Button */}
        <div className="text-center">
          <button
            onClick={handleDownload}
            className="bg-green-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <svg className="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download Cleaned CSV
          </button>
        </div>
      </div>
    </>
  );
}; 