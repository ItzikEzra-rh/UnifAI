import { api } from '@/lib/queryClient';
import type { Document } from '@/types';

export async function fetchDocuments(): Promise<Document[]> {
  const response = await api.get<any>("docs/available.docs.get");
  return response.data.docs;
};

export async function uploadDocs(files: {name: string, content: string}[]): Promise<any> {
    const uploaded = await api.post<any>(
        'docs/upload',
        { files: files }
      );
}

export async function embedDocs(docs: {source_name: string}[]): Promise<any> {
    const embedded = await api.post<any>(
        'docs/embed.docs',
        { docs: docs }
      );
}

export async function deleteDoc(pipelineId: string): Promise<any> {
    const deleted = await api.post<any>(
        'docs/delete',
        { pipelineId: pipelineId }
      );
}