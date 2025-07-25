import React, { useState } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { CleaningInterface } from './components/CleaningInterface';
import { LandingPage } from './components/LandingPage';
import { Header } from './components/Header';
import { useAuth } from './contexts/AuthContext';

function AppContent() {
  const { user, isLoading } = useAuth();
  const [showLanding, setShowLanding] = useState(!user);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading CleanMyCSV...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main>
        {showLanding && !user ? (
          <LandingPage onGetStarted={() => setShowLanding(false)} />
        ) : (
          <CleaningInterface />
        )}
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App; 