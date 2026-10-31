import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ fullPage = false, message = 'Loading...' }) => {
  if (fullPage) {
    return (
      <div className="spinner-fullpage" role="status" aria-live="polite">
        <div className="spinner-container">
          <div className="spinner"></div>
          {message && <p className="spinner-text">{message}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="spinner-inline" role="status" aria-live="polite">
      <div className="spinner"></div>
      {message && <p className="spinner-text">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;
