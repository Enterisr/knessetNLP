import { useState, useCallback } from "react";
import type { ReactNode } from "react";
import { resolveServerURI } from "../utils";
import type { MKUtterances } from "../types";
import { SearchContext, type SearchContextType } from "./SearchContext.ts";

interface SearchProviderProps {
  children: ReactNode;
}

export const SearchProvider = ({ children }: SearchProviderProps) => {
  const [searchResults, setSearchResults] = useState<MKUtterances | null>(null);
  const [currentQuery, setCurrentQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFromServer = useCallback(
    async (query: string) => {
      if (!query.trim()) {
        setSearchResults(null);
        setCurrentQuery("");
        return;
      }

      if (currentQuery === query && searchResults) {
        return;
      }

      setLoading(true);
      setError(null);
      setCurrentQuery(query);

      try {
        const response = await fetch(
          resolveServerURI(`/api/query?query=${encodeURIComponent(query)}`),
          {
            headers: {
              "Cache-Control": "max-age=86400",
            },
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        console.log("Backend response:", data.response);
        setSearchResults(data.response as MKUtterances);
      } catch (error) {
        console.error("Error searching:", error);
        setSearchResults(null);
        setError(
          error instanceof Error
            ? error.message
            : "An error occurred while searching"
        );
      } finally {
        setLoading(false);
      }
    },
    [currentQuery, searchResults]
  );

  const clearResults = useCallback(() => {
    setSearchResults(null);
    setCurrentQuery("");
    setError(null);
  }, []);

  const value: SearchContextType = {
    searchResults,
    currentQuery,
    loading,
    error,
    fetchFromServer,
    clearResults,
  };

  return (
    <SearchContext.Provider value={value}>{children}</SearchContext.Provider>
  );
};
