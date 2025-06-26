import create from 'zustand';

interface PaginationState {
  currentPage: number;
  setPage: (page: number) => void;
  resetPage: () => void;
  itemsPerPage: number;
}

export const usePaginationStore = create<PaginationState>((set) => ({
  currentPage: 1,
  itemsPerPage: 6,
  setPage: (page) => set({ currentPage: page }),
  resetPage: () => set({ currentPage: 1 }),
}));
