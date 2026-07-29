import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ServerCrash, Home, RefreshCw } from 'lucide-react';

const ServerErrorPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="text-center max-w-md">
        <ServerCrash className="h-20 w-20 text-destructive/50 mx-auto mb-6" />
        <h1 className="text-6xl font-bold text-foreground mb-2">500</h1>
        <h2 className="text-xl font-semibold text-foreground mb-2">Server Error</h2>
        <p className="text-muted-foreground mb-8">
          Something went wrong on our end. Please try again later.
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-foreground hover:bg-accent transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
          <button
            onClick={() => navigate('/')}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 transition-opacity"
          >
            <Home className="h-4 w-4" />
            Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServerErrorPage;
