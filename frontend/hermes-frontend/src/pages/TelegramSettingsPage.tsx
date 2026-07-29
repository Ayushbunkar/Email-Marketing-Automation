import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Server, Shield, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import apiService from '@/api/client';

const TelegramSettingsPage: React.FC = () => {
  const { data: status, isLoading } = useQuery({
    queryKey: ['telegram-status'],
    queryFn: async () => {
      try {
        // Assume apiService.getTelegramStatus is implemented in client.ts
        const res = await apiService.get('/api/telegram/status');
        return res.data;
      } catch {
        return null;
      }
    },
    refetchInterval: 5000, // Refresh every 5s
  });

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Telegram Operator</h1>
        <p className="text-muted-foreground mt-1">Configure your mobile command center</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Status Card */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="rounded-lg bg-blue-500/10 p-2 text-blue-500">
                <MessageSquare className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">Bot Status</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-border/50">
                <span className="text-muted-foreground">Enabled</span>
                {status?.enabled ? (
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-500">
                    <CheckCircle2 className="h-4 w-4" /> Yes
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-red-500">
                    <XCircle className="h-4 w-4" /> No
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border/50">
                <span className="text-muted-foreground">Is Running</span>
                {status?.is_running ? (
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-500">
                    <CheckCircle2 className="h-4 w-4" /> Running
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-red-500">
                    <XCircle className="h-4 w-4" /> Stopped
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-muted-foreground">Bot Name</span>
                <span className="text-sm font-medium text-foreground">
                  {status?.bot_info?.first_name || 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Connection Mode */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="rounded-lg bg-purple-500/10 p-2 text-purple-500">
                <Server className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">Connection Mode</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-border/50">
                <span className="text-muted-foreground">Mode</span>
                <span className="text-sm font-medium text-foreground capitalize">
                  {status?.mode || 'Unknown'}
                </span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-muted-foreground">Webhook URL</span>
                <span className="text-sm font-medium text-foreground max-w-[200px] truncate" title={status?.webhook_url}>
                  {status?.webhook_url || 'Using Polling'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Security */}
          <div className="md:col-span-2 rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-500">
                <Shield className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">Security</h2>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              The bot is protected by strict middleware. Only Telegram Users with IDs specified in the <code className="bg-muted px-1.5 py-0.5 rounded text-foreground">TELEGRAM_ADMIN_IDS</code> environment variable can access it.
            </p>
            <div className="bg-muted/50 p-4 rounded-lg">
              <p className="text-sm text-foreground">To set this up, find your Telegram ID by messaging @userinfobot and add it to your <code>.env</code> file:</p>
              <pre className="mt-2 text-xs text-muted-foreground bg-background p-3 rounded border border-border overflow-x-auto">
                TELEGRAM_ENABLED=true<br/>
                TELEGRAM_BOT_TOKEN=your:token_here<br/>
                TELEGRAM_ADMIN_IDS=123456789,987654321
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TelegramSettingsPage;
