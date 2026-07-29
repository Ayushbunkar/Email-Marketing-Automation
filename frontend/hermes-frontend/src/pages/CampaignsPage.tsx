import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '@/api/client';
import { Megaphone, Plus, Loader2, MoreHorizontal, Play, Pause, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import CreateCampaignModal from '@/components/modals/CreateCampaignModal';
import ConfirmDeleteModal from '@/components/modals/ConfirmDeleteModal';

const CampaignsPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [openDropdownId, setOpenDropdownId] = React.useState<string | null>(null);
  const [itemToDelete, setItemToDelete] = React.useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      try {
        const res = await apiService.getCampaigns();
        return res.data;
      } catch {
        return [];
      }
    },
  });

  const campaigns = Array.isArray(data) ? data : [];

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiService.deleteCampaign(id),
    onSuccess: () => {
      toast.success('Campaign deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setOpenDropdownId(null);
      setItemToDelete(null);
    },
    onError: () => {
      toast.error('Failed to delete campaign');
    }
  });

  const handleDelete = (id: string) => {
    setItemToDelete(id);
    setOpenDropdownId(null);
  };

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = () => setOpenDropdownId(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      draft: 'bg-gray-500/10 text-gray-500',
      active: 'bg-emerald-500/10 text-emerald-500',
      paused: 'bg-amber-500/10 text-amber-500',
      completed: 'bg-blue-500/10 text-blue-500',
      archived: 'bg-red-500/10 text-red-500',
    };
    return styles[status] || styles.draft;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Campaigns</h1>
          <p className="text-muted-foreground mt-1">Create and manage email campaigns</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 transition-opacity"
        >
          <Plus className="h-4 w-4" />
          New Campaign
        </button>
      </div>

      <CreateCampaignModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />

      <ConfirmDeleteModal
        isOpen={!!itemToDelete}
        onClose={() => setItemToDelete(null)}
        onConfirm={() => itemToDelete && deleteMutation.mutate(itemToDelete)}
        title="Delete Campaign"
        message="Are you sure you want to delete this campaign? This action cannot be undone."
        isDeleting={deleteMutation.isPending}
      />

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : campaigns.length === 0 ? (
        <div className="rounded-xl border border-border bg-card p-12 text-center shadow-sm">
          <Megaphone className="h-12 w-12 text-muted-foreground/50 mx-auto mb-3" />
          <p className="text-muted-foreground">No campaigns yet. Create your first campaign!</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {campaigns.map((campaign: any) => (
            <div
              key={campaign.id}
              className="rounded-xl border border-border bg-card p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-foreground truncate">{campaign.name}</h3>
                  <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                    {campaign.description || 'No description'}
                  </p>
                </div>
                <div className="relative ml-2">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      setOpenDropdownId(openDropdownId === campaign.id ? null : campaign.id);
                    }}
                    className="p-1 rounded hover:bg-accent transition-colors"
                  >
                    <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                  </button>
                  {openDropdownId === campaign.id && (
                    <div className="absolute right-0 top-8 z-10 w-32 rounded-md border border-border bg-popover text-popover-foreground shadow-md outline-none">
                      <div className="p-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(campaign.id);
                          }}
                          className="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground text-red-500 focus:bg-accent focus:text-accent-foreground"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          <span>Delete</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
                <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${getStatusBadge(campaign.status)}`}>
                  {campaign.status || 'draft'}
                </span>
                <span className="text-xs text-muted-foreground">
                  {campaign.type || 'broadcast'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CampaignsPage;
