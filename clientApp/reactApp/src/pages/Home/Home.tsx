import { useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import SearchBar from "../../components/SearchBar/SearchBar";
import MKList from "../../components/MKList/MKList";
import { useSearch } from "../../hooks/useSearch";

const Home = () => {
  const { query } = useParams<{ query?: string }>();
  const navigate = useNavigate();
  const { searchResults, currentQuery, loading, search } = useSearch();

  const handleSearch = useCallback(
    async (searchQuery: string) => {
      // Update URL without triggering a page reload
      if (searchQuery !== query) {
        navigate(`/search/${encodeURIComponent(searchQuery)}`, {
          replace: false,
        });
      }

      // Use context search method
      await search(searchQuery);
    },
    [navigate, query, search]
  );

  useEffect(() => {
    if (query) {
      handleSearch(query);
    }
  }, [query, handleSearch]);

  const handleMKSelect = (mkName: string) => {
    // Navigate to the MK page with the selected MK name and current query
    navigate(
      `/mk/${encodeURIComponent(mkName)}/${encodeURIComponent(currentQuery)}`
    );
  };

  return (
    <main className="app-main">
      <SearchBar onSearch={handleSearch} initialValue={currentQuery} />
      <MKList
        mks={searchResults}
        onMKSelect={handleMKSelect}
        loading={loading}
      />
    </main>
  );
};

export default Home;
