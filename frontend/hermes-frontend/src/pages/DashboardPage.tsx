import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiService from '@/api/client';
import {
  Users,
  Megaphone,
  Mail,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
} from 'lucide-react';

interface StatCard {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
}

const DashboardPage: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      try {
        const res = await apiService.getDashboardStats();
        return res.data;
      } catch {
        return null;
      }
    },
  });

  const cards: StatCard[] = [
    {
      title: 'Total Contacts',
      value: stats?.total_contacts ?? '—',
      icon: Users,
      color: 'bg-blue-500/10 text-blue-500',
    },
    {
      title: 'Active Campaigns',
      value: stats?.total_campaigns ?? '—',
      icon: Megaphone,
      color: 'bg-emerald-500/10 text-emerald-500',
    },
    {
      title: 'Emails Sent',
      value: stats?.emails_sent ?? '—',
      icon: Mail,
      color: 'bg-violet-500/10 text-violet-500',
    },
    {
      title: 'Open Rate',
      value: stats?.open_rate !== undefined ? `${stats.open_rate}%` : '—',
      icon: TrendingUp,
      color: 'bg-amber-500/10 text-amber-500',
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-1">Overview of your email marketing performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <div
            key={card.title}
            className="rounded-xl border border-border bg-card p-5 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">{card.title}</span>
              <div className={`rounded-lg p-2 ${card.color}`}>
                <card.icon className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-foreground">{card.value}</span>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};

export default DashboardPage;
