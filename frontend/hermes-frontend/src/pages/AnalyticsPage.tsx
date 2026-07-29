import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiService from '@/api/client';
import { BarChart3, Loader2, TrendingUp } from 'lucide-react';

const AnalyticsPage: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['analytics-dashboard'],
    queryFn: async () => {
      try {
        const res = await apiService.getDashboardStats();
        return res.data;
      } catch {
        return null;
      }
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const metrics = [
    { label: 'Total Sent', value: stats?.emails_sent ?? 0 },
    { label: 'Delivered', value: stats?.delivered ?? 0 },
    { label: 'Opened', value: stats?.opened ?? 0 },
    { label: 'Clicked', value: stats?.clicked ?? 0 },
    { label: 'Bounced', value: stats?.bounced ?? 0 },
    { label: 'Complaints', value: stats?.complaints ?? 0 },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
        <p className="text-muted-foreground mt-1">Track your email marketing performance</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="rounded-xl border border-border bg-card p-5 shadow-sm"
          >
            <p className="text-sm text-muted-foreground">{metric.label}</p>
            <p className="text-3xl font-bold text-foreground mt-2">{metric.value.toLocaleString()}</p>
          </div>
        ))}
      </div>

      {/* Chart placeholder */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-6">
          <TrendingUp className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Sending Trends</h2>
        </div>
        <div className="flex items-center justify-center h-64 bg-muted/30 rounded-lg">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 text-muted-foreground/50 mx-auto mb-2" />
            <p className="text-muted-foreground">Charts will appear here once you have campaign data</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
