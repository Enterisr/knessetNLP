import { createContext } from "react";
import type { MKUtterances } from "../types";

export interface SearchContextType {
  searchResults: MKUtterances | null;
  currentQuery: string;
  loading: boolean;
  error: string | null;
  fetchFromServer: (query: string) => Promise<void>;
  clearResults: () => void;
}

export const SearchContext = createContext<SearchContextType | undefined>(
  undefined
);
