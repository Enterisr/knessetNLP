import React, { useState, useEffect } from "react";
import styles from "./SearchBar.module.css";
import { useLocation } from "react-router-dom";

interface SearchBarProps {
  onSearch: (query: string) => void;
  initialValue?: string;
}

const SearchBar = ({ onSearch, initialValue = "" }: SearchBarProps) => {
  const [query, setQuery] = useState(initialValue);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const loc = useLocation();
  useEffect(() => {
    setQuery(initialValue);
  }, [initialValue]);

  useEffect(() => {
    // Focus the input field when component mounts
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };
  return (
    <form onSubmit={handleSubmit} className={styles["search-form"]}>
      {loc.pathname === "/" && (
        <div className={styles["home-search-description"]}>
          {" "}
          חפש נושא או ארגון, ותוכל לגלות אילו חברי כנסת עסקו בהם
        </div>
      )}
      <div className={styles["search-input-container"]}>
        {" "}
        <input
          ref={inputRef}
          type="text"
          className={styles["search-input"]}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="חיפוש..."
        />
        <button type="submit" className={styles["search-button"]}>
          חפש
        </button>
      </div>
    </form>
  );
};

export default SearchBar;
