import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiService from '@/api/client';
import { Inbox as InboxIcon, Loader2, Mail, Clock } from 'lucide-react';

const InboxPage: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['inbox'],
    queryFn: async () => {
      try {
        const res = await apiService.getInbox();
        return res.data;
      } catch {
        return [];
      }
    },
  });

  const messages = Array.isArray(data) ? data : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Inbox</h1>
        <p className="text-muted-foreground mt-1">View incoming messages and notifications</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : messages.length === 0 ? (
        <div className="rounded-xl border border-border bg-card p-12 text-center shadow-sm">
          <InboxIcon className="h-12 w-12 text-muted-foreground/50 mx-auto mb-3" />
          <p className="text-lg font-medium text-foreground">Inbox is empty</p>
          <p className="text-muted-foreground mt-1">No messages to display right now</p>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card shadow-sm divide-y divide-border">
          {messages.map((message: any) => (
            <div
              key={message.id}
              className="flex items-start gap-4 p-4 hover:bg-muted/30 transition-colors cursor-pointer"
            >
              <div className="flex-shrink-0 h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Mail className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-foreground truncate">
                    {message.from_email || message.subject || 'New Message'}
                  </h3>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground ml-2">
                    <Clock className="h-3 w-3" />
                    <span>{message.created_at ? new Date(message.created_at).toLocaleDateString() : '—'}</span>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                  {message.body_text || message.subject || 'No content'}
                </p>
              </div>
              <span className={`flex-shrink-0 inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                message.status === 'read' ? 'bg-gray-500/10 text-gray-500' : 'bg-blue-500/10 text-blue-500'
              }`}>
                {message.status || 'unread'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default InboxPage;
