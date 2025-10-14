import { useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import SearchBar from "../../components/SearchBar/SearchBar";
import PartyDistributionBar from "../../components/PartyDistributionBar/PartyDistributionBar";
import MKList from "../../components/MKList/MKList";
import { useSearch } from "../../hooks/useSearch";
import "./Home.css";
const Home = () => {
  const { query: queryFromURI } = useParams<{ query?: string }>();
  const navigate = useNavigate();
  const {
    searchResults,
    currentQuery,
    loading: isLoading,
    fetchFromServer,
    error,
  } = useSearch();
  const handleSearch = useCallback(
    async (searchQuery: string) => {
      if (searchQuery !== queryFromURI) {
        navigate(`/search/${encodeURIComponent(searchQuery)}`, {
          replace: false,
        });
      }

      await fetchFromServer(searchQuery);
    },
    [navigate, queryFromURI, fetchFromServer]
  );

  useEffect(() => {
    //kinda hacky BUT i dont care honostly
    if (queryFromURI && window.location.pathname !== "/") {
      handleSearch(queryFromURI);
    }
  }, [queryFromURI, handleSearch]);

  const handleMKSelect = (mkName: string) => {
    // Navigate to the MK page with the selected MK name and current query
    navigate(
      `/mk/${encodeURIComponent(mkName)}/${encodeURIComponent(currentQuery)}`
    );
  };

  return (
    <main className="app-main">
      <SearchBar onSearch={handleSearch} initialValue={queryFromURI} />
      {searchResults && <PartyDistributionBar mks={searchResults} />}
      <MKList
        isError={error}
        mks={searchResults}
        onMKSelect={handleMKSelect}
        isLoading={isLoading}
      />
    </main>
  );
};

export default Home;
