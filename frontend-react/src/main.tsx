import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useAuthBootstrap } from './hooks/useAuthBootstrap';

const RootApp = (): JSX.Element => {
  useAuthBootstrap();
  return <App />;
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <RootApp />
    </ErrorBoundary>
  </React.StrictMode>,
);
