
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchBar.css';

function SearchBar() {
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();

    const merchantId = searchTerm.trim();

    if (!merchantId) {
      setError('Please enter a Merchant ID.');
      return;
    }

    // Accept IDs such as M_0, M_1, M_12345
    if (!/^M_\d+$/i.test(merchantId)) {
      setError('Invalid Merchant ID. Example: M_0');
      return;
    }

    setError('');

    navigate(`/merchant/${encodeURIComponent(merchantId)}`);
    setSearchTerm('');
  };

  return (
    <div>
      <form className="search-bar" onSubmit={handleSearch}>
        <input
          type="text"
          className="search-input"
          placeholder="Search Merchant ID (e.g., M_0)"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setError('');
          }}
          aria-label="Merchant ID"
        />

        <button type="submit" className="search-button">
          🔍 Search
        </button>
      </form>

      {error && (
        <p style={{ color: 'red', marginTop: '8px' }}>
          {error}
        </p>
      )}
    </div>
  );
}

export default SearchBar;
