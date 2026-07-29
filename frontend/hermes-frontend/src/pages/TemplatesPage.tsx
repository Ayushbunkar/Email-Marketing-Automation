import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '@/api/client';
import { FileText, Plus, Loader2, MoreHorizontal, Copy, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import CreateTemplateModal from '@/components/modals/CreateTemplateModal';
import ConfirmDeleteModal from '@/components/modals/ConfirmDeleteModal';

const TemplatesPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [openDropdownId, setOpenDropdownId] = React.useState<string | null>(null);
  const [itemToDelete, setItemToDelete] = React.useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: async () => {
      try {
        const res = await apiService.getTemplates();
        return res.data;
      } catch {
        return [];
      }
    },
  });

  const templates = Array.isArray(data) ? data : [];

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiService.deleteTemplate(id),
    onSuccess: () => {
      toast.success('Template deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setOpenDropdownId(null);
      setItemToDelete(null);
    },
    onError: () => {
      toast.error('Failed to delete template');
    }
  });

  const duplicateMutation = useMutation({
    mutationFn: (template: any) => {
      const { id, created_at, updated_at, status, ...rest } = template;
      return apiService.createTemplate({
        ...rest,
        name: `${template.name} (Copy)`
      });
    },
    onSuccess: () => {
      toast.success('Template duplicated successfully');
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
    onError: () => {
      toast.error('Failed to duplicate template');
    }
  });

  const handleDelete = (id: string) => {
    setItemToDelete(id);
    setOpenDropdownId(null);
  };

  const handleDuplicate = (template: any) => {
    duplicateMutation.mutate(template);
  };

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = () => setOpenDropdownId(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Templates</h1>
          <p className="text-muted-foreground mt-1">Manage your email templates</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 transition-opacity"
        >
          <Plus className="h-4 w-4" />
          New Template
        </button>
      </div>

      <CreateTemplateModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />

      <ConfirmDeleteModal
        isOpen={!!itemToDelete}
        onClose={() => setItemToDelete(null)}
        onConfirm={() => itemToDelete && deleteMutation.mutate(itemToDelete)}
        title="Delete Template"
        message="Are you sure you want to delete this template? This action cannot be undone."
        isDeleting={deleteMutation.isPending}
      />

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : templates.length === 0 ? (
        <div className="rounded-xl border border-border bg-card p-12 text-center shadow-sm">
          <FileText className="h-12 w-12 text-muted-foreground/50 mx-auto mb-3" />
          <p className="text-muted-foreground">No templates yet. Create your first template!</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((template: any) => (
            <div
              key={template.id}
              className="rounded-xl border border-border bg-card p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-foreground truncate">{template.name}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{template.subject || 'No subject'}</p>
                </div>
                <div className="flex items-center gap-1 ml-2">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDuplicate(template);
                    }}
                    className="p-1 rounded hover:bg-accent transition-colors" 
                    title="Duplicate"
                  >
                    <Copy className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <div className="relative">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setOpenDropdownId(openDropdownId === template.id ? null : template.id);
                      }}
                      className="p-1 rounded hover:bg-accent transition-colors"
                    >
                      <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                    </button>
                    {openDropdownId === template.id && (
                      <div className="absolute right-0 top-8 z-10 w-32 rounded-md border border-border bg-popover text-popover-foreground shadow-md outline-none">
                        <div className="p-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(template.id);
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
              </div>
              <div className="mt-4 pt-4 border-t border-border">
                <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${
                  template.status === 'active' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-gray-500/10 text-gray-500'
                }`}>
                  {template.status || 'draft'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TemplatesPage;
