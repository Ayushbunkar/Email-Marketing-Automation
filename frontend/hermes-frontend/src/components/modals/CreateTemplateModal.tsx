import React, { useState } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { X, Loader2 } from 'lucide-react';
import apiService from '@/api/client';
import { toast } from 'sonner';

interface CreateTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CreateTemplateModal: React.FC<CreateTemplateModalProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    preheader: '',
    body_markdown: '',
  });

  const loadTemplate = (niche: string) => {
    const templates: Record<string, typeof formData> = {
      ecommerce: {
        name: 'E-commerce Welcome & Discount',
        subject: 'Welcome to the family! Here is 20% off 🎉',
        preheader: 'Your exclusive welcome discount inside...',
        body_markdown: '# Welcome {{first_name}}!\n\nWe are so glad you joined us. As a special thank you, use code **WELCOME20** at checkout for 20% off your first order.\n\n[Shop Now](https://example.com)\n\nCheers,\nThe Team',
      },
      saas: {
        name: 'SaaS Onboarding',
        subject: 'Getting started with your new account 🚀',
        preheader: '3 simple steps to get you up and running...',
        body_markdown: '# Hi {{first_name}},\n\nWelcome aboard! Here are three quick things you can do to get the most out of your account:\n\n1. Complete your profile\n2. Invite your team\n3. Create your first project\n\n[Go to Dashboard](https://example.com)\n\nLet us know if you need any help!',
      },
      newsletter: {
        name: 'Weekly Newsletter',
        subject: 'Your Weekly Digest: Top Stories 📰',
        preheader: 'The latest news, tips, and insights...',
        body_markdown: '# Weekly Digest\n\nHappy Friday {{first_name}}!\n\nHere is what you missed this week:\n\n### 🚀 Product Updates\nWe just launched a new feature that lets you do X faster.\n\n### 💡 Tip of the week\nDid you know you can automate Y by doing Z?\n\nSee you next week!',
      },
      webinar: {
        name: 'Webinar Reminder',
        subject: 'Reminder: Live Masterclass starts in 1 hour! ⏳',
        preheader: 'Don\'t miss out on this exclusive session...',
        body_markdown: '# Hi {{first_name}},\n\nThis is a quick reminder that our live masterclass starts in exactly 1 hour.\n\n**Topic:** How to 10x your growth\n\nGrab a coffee and get ready to take some notes!\n\n[Join the Webinar](https://example.com/join)\n\nSee you there!',
      }
    };
    if (templates[niche]) {
      setFormData(templates[niche]);
      toast.success('Template loaded!');
    }
  };

  const mutation = useMutation({
    mutationFn: (data: typeof formData) => apiService.createTemplate(data),
    onSuccess: () => {
      toast.success('Template created successfully');
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setFormData({ name: '', subject: '', preheader: '', body_markdown: '' });
      onClose();
    },
    onError: () => {
      // Error toast is handled by apiClient interceptor
    }
  });

  if (!isOpen) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0">
      <div 
        className="fixed inset-0 bg-background/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      <div className="relative z-50 w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg sm:my-8 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-semibold text-foreground">Create New Template</h2>
          <button 
            onClick={onClose}
            className="rounded-full p-1.5 hover:bg-accent text-muted-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mb-5 p-3 rounded-lg bg-accent/50 border border-border/50">
          <p className="text-xs font-medium text-muted-foreground mb-2">Need inspiration? Start with a template:</p>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => loadTemplate('ecommerce')} className="text-xs px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 transition-colors">E-commerce</button>
            <button type="button" onClick={() => loadTemplate('saas')} className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition-colors">SaaS</button>
            <button type="button" onClick={() => loadTemplate('newsletter')} className="text-xs px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-500 hover:bg-purple-500/20 transition-colors">Newsletter</button>
            <button type="button" onClick={() => loadTemplate('webinar')} className="text-xs px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 transition-colors">Webinar</button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-foreground mb-1.5">
              Template Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              required
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g., Welcome Email v1"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-foreground mb-1.5">
              Email Subject
            </label>
            <input
              type="text"
              id="subject"
              name="subject"
              required
              value={formData.subject}
              onChange={handleChange}
              placeholder="Welcome to our platform!"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          <div>
            <label htmlFor="preheader" className="block text-sm font-medium text-foreground mb-1.5">
              Preheader (Optional)
            </label>
            <input
              type="text"
              id="preheader"
              name="preheader"
              value={formData.preheader}
              onChange={handleChange}
              placeholder="A short summary that follows the subject line..."
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          <div>
            <label htmlFor="body_markdown" className="block text-sm font-medium text-foreground mb-1.5">
              Email Content (Markdown)
            </label>
            <textarea
              id="body_markdown"
              name="body_markdown"
              required
              rows={5}
              value={formData.body_markdown}
              onChange={handleChange}
              placeholder="# Hello {{name}}!&#10;&#10;Welcome to our platform..."
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none font-mono"
            />
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-border mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
            >
              {mutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Create'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateTemplateModal;
