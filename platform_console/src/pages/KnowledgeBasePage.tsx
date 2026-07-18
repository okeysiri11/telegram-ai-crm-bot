import { useQuery } from '@tanstack/react-query';
import { managementApi } from '../services/management';
import { Card, Badge, Spinner } from '../components/ui/Card';

interface KnowledgeDoc {
  document_id: string;
  title: string;
  doc_type: string;
  chunk_count: number;
  content_length: number;
  tags?: string[];
}

export function KnowledgeBasePage() {
  const docs = useQuery({ queryKey: ['ai-knowledge-list'], queryFn: () => managementApi.aiKnowledgeList(), refetchInterval: 30_000 });
  const stats = useQuery({ queryKey: ['ai-memory-stats'], queryFn: () => managementApi.aiMemoryStatistics(), refetchInterval: 30_000 });

  const indexStats = stats.data?.statistics as {
    knowledge?: { documents: number; content_bytes: number; index: { total_chunks: number } };
    embeddings?: { provider_id: string; dimensions: number }[];
  } | undefined;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Knowledge Base</h1>
      <p className="mb-6 text-sm text-[var(--color-muted)]">
        Indexed documents for RAG retrieval — Markdown, PDF, DOCX, TXT, HTML, JSON, YAML, CSV.
      </p>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card title="Documents">
          {docs.isLoading && <Spinner />}
          {docs.data && <p className="text-2xl font-bold">{docs.data.documents?.length || 0}</p>}
        </Card>
        <Card title="Total Chunks">
          {indexStats && <p className="text-2xl font-bold">{indexStats.knowledge?.index?.total_chunks || 0}</p>}
        </Card>
        <Card title="Content Size">
          {indexStats && (
            <p className="text-2xl font-bold">{((indexStats.knowledge?.content_bytes || 0) / 1024).toFixed(1)} KB</p>
          )}
        </Card>
        <Card title="Embedding Status">
          {indexStats && (
            <p className="text-lg font-bold">{(indexStats.embeddings || []).map((e) => e.provider_id).join(', ') || '—'}</p>
          )}
        </Card>
      </div>

      <Card title="Indexed Documents">
        {docs.isLoading && <Spinner />}
        <div className="space-y-3">
          {((docs.data?.documents as KnowledgeDoc[]) || []).map((doc) => (
            <div key={doc.document_id} className="flex flex-col gap-2 rounded border border-[var(--color-border)] p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="font-medium">{doc.title}</div>
                <div className="text-xs text-[var(--color-muted)]">
                  {doc.document_id} · {doc.doc_type} · {doc.content_length} chars
                </div>
                {doc.tags && doc.tags.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {doc.tags.map((tag) => (
                      <span key={tag} className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Badge variant="success">{doc.chunk_count} chunks</Badge>
              </div>
            </div>
          ))}
          {!docs.isLoading && !(docs.data?.documents as KnowledgeDoc[])?.length && (
            <p className="text-sm text-[var(--color-muted)]">No documents indexed yet.</p>
          )}
        </div>
      </Card>
    </div>
  );
}
