import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiService from '@/api/client';
import { Settings, Loader2, Shield, Mail, Clock, Bell } from 'lucide-react';

const SettingsPage: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      try {
        const res = await apiService.getSettings();
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

  const sections = [
    {
      title: 'Email Configuration',
      icon: Mail,
      items: [
        { label: 'Email Provider', value: 'Brevo' },
        { label: 'From Name', value: 'Pixel Punch Marketing' },
        { label: 'From Email', value: 'marketing@pixelpunch.org' },
      ],
    },
    {
      title: 'Guardrails',
      icon: Shield,
      items: [
        { label: 'Max Sends Per Day', value: '500' },
        { label: 'Max Sends Per Hour', value: '100' },
        { label: 'Max Emails Per Contact/Week', value: '3' },
      ],
    },
    {
      title: 'Quiet Hours',
      icon: Clock,
      items: [
        { label: 'Start', value: '9:00 PM' },
        { label: 'End', value: '8:00 AM' },
      ],
    },
    {
      title: 'Auto-Pause Thresholds',
      icon: Bell,
      items: [
        { label: 'Bounce Rate', value: '2%' },
        { label: 'Complaint Rate', value: '0.1%' },
        { label: 'Require Approval', value: 'Yes' },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-1">Configure your email marketing platform</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {sections.map((section) => (
          <div
            key={section.title}
            className="rounded-xl border border-border bg-card p-6 shadow-sm"
          >
            <div className="flex items-center gap-2 mb-4">
              <section.icon className="h-5 w-5 text-primary" />
              <h2 className="font-semibold text-foreground">{section.title}</h2>
            </div>
            <div className="space-y-3">
              {section.items.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between py-2 border-b border-border last:border-0"
                >
                  <span className="text-sm text-muted-foreground">{item.label}</span>
                  <span className="text-sm font-medium text-foreground">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SettingsPage;
