import { api } from '@/lib/queryClient';
import type { Channel, Document, EmbedChannel } from '@/types';

export async function fetchDocuments(): Promise<Document[]> {
  const response = await api.get<Document[]>("docs/available.docs.get");
  console.log(response)
  return response.data.docs;
};