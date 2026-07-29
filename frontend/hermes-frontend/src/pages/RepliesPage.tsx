import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '@/api/client';
import { MessageSquare, Loader2, Check, X, Clock } from 'lucide-react';
import { toast } from 'sonner';

const RepliesPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['replies'],
    queryFn: async () => {
      try {
        const res = await apiService.getReplies();
        return res.data;
      } catch {
        return [];
      }
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => apiService.approveReply(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['replies'] });
      toast.success('Reply approved');
    },
    onError: () => toast.error('Failed to approve reply'),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => apiService.rejectReply(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['replies'] });
      toast.success('Reply rejected');
    },
    onError: () => toast.error('Failed to reject reply'),
  });

  const replies = Array.isArray(data) ? data : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Replies</h1>
        <p className="text-muted-foreground mt-1">Review and manage automated reply drafts</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : replies.length === 0 ? (
        <div className="rounded-xl border border-border bg-card p-12 text-center shadow-sm">
          <MessageSquare className="h-12 w-12 text-muted-foreground/50 mx-auto mb-3" />
          <p className="text-lg font-medium text-foreground">No replies pending</p>
          <p className="text-muted-foreground mt-1">All caught up!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {replies.map((reply: any) => (
            <div
              key={reply.id}
              className="rounded-xl border border-border bg-card p-5 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-foreground">{reply.to_email || 'Contact'}</span>
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                      reply.status === 'pending' ? 'bg-amber-500/10 text-amber-500' :
                      reply.status === 'approved' ? 'bg-emerald-500/10 text-emerald-500' :
                      'bg-red-500/10 text-red-500'
                    }`}>
                      <Clock className="h-3 w-3" />
                      {reply.status || 'pending'}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    {reply.subject || 'No subject'}
                  </p>
                  <div className="bg-muted/50 rounded-lg p-3 text-sm text-foreground">
                    {reply.body_text || reply.body_html || 'No content'}
                  </div>
                </div>
              </div>
              {reply.status === 'pending' && (
                <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
                  <button
                    onClick={() => approveMutation.mutate(reply.id)}
                    disabled={approveMutation.isPending}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-600 transition-colors disabled:opacity-50"
                  >
                    <Check className="h-3.5 w-3.5" />
                    Approve
                  </button>
                  <button
                    onClick={() => rejectMutation.mutate(reply.id)}
                    disabled={rejectMutation.isPending}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-red-500 px-3 py-2 text-xs font-medium text-white hover:bg-red-600 transition-colors disabled:opacity-50"
                  >
                    <X className="h-3.5 w-3.5" />
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RepliesPage;
