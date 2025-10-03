import React, { useState, useEffect } from "react";
import styles from "./SearchBar.module.css";

interface SearchBarProps {
  onSearch: (query: string) => void;
  initialValue?: string;
}

const SearchBar = ({ onSearch, initialValue = "" }: SearchBarProps) => {
  const [query, setQuery] = useState(initialValue);

  useEffect(() => {
    setQuery(initialValue);
  }, [initialValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles["search-form"]}>
      <div className={styles["search-input-container"]}>
        <input
          type="text"
          className={styles["search-input"]}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="חיפוש..."
        />
        <button type="submit" className={styles["search-button"]}>
          חיפוש
        </button>
      </div>
    </form>
  );
};

export default SearchBar;
