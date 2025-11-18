/**
 * Memory browser for exploring the 3-tier memory system
 */

import React, { useState, useEffect } from 'react';
import apiClient, { Memory } from '../api/client';
import './MemoryBrowser.css';

const MemoryBrowser: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [selectedTier, setSelectedTier] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Memory[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [loading, setLoading] = useState(false);

  const [newMemory, setNewMemory] = useState({
    text: '',
    tier: 'ember',
    tags: '',
  });

  useEffect(() => {
    loadMemories();
  }, [selectedTier]);

  const loadMemories = async () => {
    setLoading(true);
    try {
      const tier = selectedTier === 'all' ? undefined : selectedTier;
      const data = await apiClient.getMemories(tier);
      setMemories(data);
    } catch (error) {
      console.error('Error loading memories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const results = await apiClient.searchMemories(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Error searching memories:', error);
    }
  };

  const handleAddMemory = async () => {
    if (!newMemory.text.trim()) return;

    try {
      const tags = newMemory.tags
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t);

      await apiClient.addMemory(newMemory.text, newMemory.tier, tags);

      setNewMemory({ text: '', tier: 'ember', tags: '' });
      loadMemories();
    } catch (error) {
      console.error('Error adding memory:', error);
    }
  };

  const displayMemories = isSearching ? searchResults : memories;

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'ember':
        return '#FF5722';
      case 'rune':
        return '#2196F3';
      case 'glyph':
        return '#4CAF50';
      default:
        return '#757575';
    }
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'ember':
        return '🔥';
      case 'rune':
        return '📜';
      case 'glyph':
        return '💎';
      default:
        return '📄';
    }
  };

  return (
    <div className="memory-browser">
      <div className="memory-header">
        <h2>Memory Vault</h2>
        <p className="memory-subtitle">Explore the 3-tier memory system</p>
      </div>

      {/* Search */}
      <div className="memory-search">
        <input
          type="text"
          className="search-input"
          placeholder="Search memories (semantic + keyword)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button className="search-button" onClick={handleSearch}>
          Search
        </button>
        {isSearching && (
          <button
            className="clear-search-button"
            onClick={() => {
              setIsSearching(false);
              setSearchQuery('');
              setSearchResults([]);
            }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Tier Filter */}
      <div className="tier-filter">
        {['all', 'ember', 'rune', 'glyph'].map((tier) => (
          <button
            key={tier}
            className={`tier-button ${selectedTier === tier ? 'active' : ''}`}
            onClick={() => setSelectedTier(tier)}
            style={{
              borderColor: selectedTier === tier ? getTierColor(tier) : '#ddd',
            }}
          >
            {tier !== 'all' && getTierIcon(tier)} {tier.charAt(0).toUpperCase() + tier.slice(1)}
          </button>
        ))}
      </div>

      {/* Add Memory */}
      <div className="add-memory">
        <h3>Add New Memory</h3>
        <textarea
          className="memory-input"
          placeholder="Enter memory text..."
          value={newMemory.text}
          onChange={(e) => setNewMemory({ ...newMemory, text: e.target.value })}
          rows={3}
        />
        <div className="memory-controls">
          <select
            className="tier-select"
            value={newMemory.tier}
            onChange={(e) => setNewMemory({ ...newMemory, tier: e.target.value })}
          >
            <option value="ember">🔥 Ember (Short-term)</option>
            <option value="rune">📜 Rune (Mid-term)</option>
            <option value="glyph">💎 Glyph (Long-term)</option>
          </select>
          <input
            type="text"
            className="tags-input"
            placeholder="Tags (comma-separated)"
            value={newMemory.tags}
            onChange={(e) => setNewMemory({ ...newMemory, tags: e.target.value })}
          />
          <button className="add-button" onClick={handleAddMemory}>
            Add Memory
          </button>
        </div>
      </div>

      {/* Memory List */}
      <div className="memory-list">
        {loading && <div className="loading">Loading memories...</div>}

        {!loading && displayMemories.length === 0 && (
          <div className="empty-state">
            {isSearching ? 'No memories found' : 'No memories yet'}
          </div>
        )}

        {!loading &&
          displayMemories.map((memory, idx) => (
            <div key={idx} className="memory-item">
              <div className="memory-tier-badge" style={{ background: getTierColor(memory.tier) }}>
                {getTierIcon(memory.tier)} {memory.tier}
              </div>
              <div className="memory-text">{memory.text}</div>
              <div className="memory-meta">
                <span className="memory-timestamp">
                  {new Date(memory.timestamp).toLocaleString()}
                </span>
                {memory.tags.length > 0 && (
                  <div className="memory-tags">
                    {memory.tags.map((tag, tagIdx) => (
                      <span key={tagIdx} className="tag">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                {memory.references !== undefined && (
                  <span className="memory-references">📌 {memory.references} refs</span>
                )}
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};

export default MemoryBrowser;
