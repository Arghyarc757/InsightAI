import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Loader2, BarChart2, CheckCircle, XCircle, Star, ChevronDown, ChevronUp } from 'lucide-react';


const API_BASE = 'http://localhost:8000/api';

function App() {
  const [categories, setCategories] = useState(['All']);
  const [manufacturers, setManufacturers] = useState(['All']);
  
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedManufacturer, setSelectedManufacturer] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [selectedStarRating, setSelectedStarRating] = useState(null);

  // Fetch Dropdowns
  useEffect(() => {
    const fetchDropdowns = async () => {
      try {
        const catRes = await axios.get(`${API_BASE}/categories`);
        if(catRes.data.categories) setCategories(catRes.data.categories);
        
        const mfgRes = await axios.get(`${API_BASE}/manufacturers`);
        if(mfgRes.data.manufacturers) setManufacturers(mfgRes.data.manufacturers);
      } catch (err) {
        console.error("Failed to fetch dropdowns", err);
      }
    };
    fetchDropdowns();
  }, []);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!searchQuery && selectedCategory === 'All' && selectedManufacturer === 'All') {
      setError("Please provide a search keyword or select a filter.");
      return;
    }
    
    setError('');
    setLoading(true);
    setResults(null);
    setSelectedStarRating(null);
    
    try {
      const response = await axios.post(`${API_BASE}/analyze`, {
        query: searchQuery || "Summarize reviews generally",
        product_category: selectedCategory,
        manufacturer: selectedManufacturer
      });
      setResults(response.data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch analysis. Ensure backend is running and Gemini API key is valid.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Insight<span style={{color: 'var(--accent-primary)'}}>AI</span></h1>
      
      <div className="glass-panel header-controls">
        <form className="search-bar" onSubmit={handleSearch} style={{ flexGrow: 1, maxWidth: '500px' }}>
          <Search size={20} color="var(--text-secondary)" />
          <input 
            type="text" 
            className="search-input" 
            placeholder="Search keyword (e.g. Samsung TV 60 LED)..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </form>

        <div className="filter-group">
          <select 
            className="dropdown" 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <select 
            className="dropdown" 
            value={selectedManufacturer} 
            onChange={(e) => setSelectedManufacturer(e.target.value)}
          >
            {manufacturers.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          
          <button className="btn" onClick={handleSearch} disabled={loading}>
            {loading ? <Loader2 className="loader" size={20}/> : "Go"}
          </button>
        </div>
      </div>

      {error && (
        <div className="glass-panel" style={{ borderColor: 'var(--accent-danger)', marginBottom: '1.5rem' }}>
          <p style={{ color: 'var(--accent-danger)' }}>{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex-center" style={{ height: '300px' }}>
          <div style={{ textAlign: 'center' }}>
             <Loader2 size={48} className="loader" style={{margin: '0 auto', marginBottom: '1rem', borderTopColor: 'var(--accent-primary)'}} />
             <p style={{color: 'var(--text-secondary)'}}>Agents are analyzing reviews...</p>
          </div>
        </div>
      )}

      {results && !loading && (
        <div className="dashboard">
          
          {/* AMAZON STYLE ANALYTICS PANEL */}
          {results.statistics && Object.keys(results.statistics).length > 0 && results.statistics.distribution && (
          <div className="glass-panel" style={{marginBottom: '1.5rem', borderLeft: '4px solid orange'}}>
              <h2 style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                Customer Reviews Distribution
              </h2>
              
              <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '1rem 0'}}>
                 {[1,2,3,4,5].map(s => (
                    <Star 
                      key={s} 
                      fill={s <= Math.round(results.statistics.average_rating) ? 'orange' : 'transparent'} 
                      color="orange" 
                      size={28} 
                    />
                 ))}
                 <span style={{fontSize: '1.4rem', fontWeight: 'bold'}}>{results.statistics.average_rating} out of 5</span>
              </div>
              <p style={{color: 'var(--text-secondary)', marginBottom: '1.5rem'}}>{results.statistics.total_reviews} global ratings matched from Vector Database</p>
              
              <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem', maxWidth: '600px'}}>
                 {[5,4,3,2,1].map(star => {
                     let rawDist = results.statistics.distribution[star.toString()] || 0;
                     let pct = results.statistics.total_reviews > 0 ? Math.round((rawDist / results.statistics.total_reviews) * 100) : 0;
                     let isSelected = selectedStarRating === star;
                     
                     return (
                         <div key={star} 
                              onClick={() => setSelectedStarRating(isSelected ? null : star)}
                              style={{
                                display: 'flex', alignItems: 'center', gap: '1rem', 
                                cursor: 'pointer', padding: '0.5rem', borderRadius: '6px', 
                                backgroundColor: isSelected ? 'rgba(255, 165, 0, 0.15)' : 'transparent',
                                transition: 'all 0.2s ease'
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = isSelected ? 'rgba(255, 165, 0, 0.2)' : 'rgba(255, 255, 255, 0.05)'}
                              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = isSelected ? 'rgba(255, 165, 0, 0.15)' : 'transparent'}
                          >
                             <span style={{minWidth: '55px', color: 'var(--text-primary)', fontWeight: '500'}}>{star} star</span>
                             <div style={{flexGrow: 1, backgroundColor: 'rgba(255, 255, 255, 0.1)', height: '22px', borderRadius: '4px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)'}}>
                                 <div style={{backgroundColor: '#ff9900', height: '100%', width: `${pct}%`, transition: 'width 1s ease-out'}}></div>
                             </div>
                             <span style={{minWidth: '45px', textAlign: 'right', color: 'var(--text-primary)'}}>{pct}%</span>
                             {isSelected ? <ChevronUp size={18} color="orange"/> : <ChevronDown size={18} color="var(--text-secondary)"/>}
                         </div>
                     );
                 })}
              </div>
              
              {/* Expandable Click-To-Filter Raw Reviews Modal Effect */}
              {selectedStarRating && (
                  <div style={{marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)', animation: 'fadeIn 0.3s ease'}}>
                      <h3 style={{marginBottom: '1rem', color: '#ff9900', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                        <Star fill="#ff9900" color="#ff9900" size={18} />
                        Filtered: {selectedStarRating}-Star Reviews
                      </h3>
                      
                      {results.statistics.reviews_by_star[selectedStarRating.toString()]?.length === 0 ? (
                        <p style={{color: 'var(--text-secondary)'}}>No reviews found for this rating.</p>
                      ) : (
                        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '400px', overflowY: 'auto', paddingRight: '0.5rem'}}>
                            {results.statistics.reviews_by_star[selectedStarRating.toString()]?.map((rev, i) => (
                                <div key={i} style={{padding: '1.25rem', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)'}}>
                                    <div style={{display: 'flex', gap: '0.25rem', marginBottom: '0.5rem'}}>
                                      {[...Array(selectedStarRating)].map((_, i) => <Star key={i} size={14} fill="#ff9900" color="#ff9900"/>)}
                                    </div>
                                    <p style={{fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', fontWeight: 'bold'}}>{rev.product}</p>
                                    <p style={{lineHeight: '1.6', color: 'var(--text-primary)'}}>"{rev.text}"</p>
                                </div>
                            ))}
                        </div>
                      )}
                  </div>
              )}
          </div>
          )}

          {/* AI GENERAL OVERVIEW */}
          <div className="glass-panel" style={{marginBottom: '1.5rem'}}>
            <h2 style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
              <BarChart2 color="var(--accent-primary)" />
              AI Synthesized Overview
              
              {results.analysis?.sentiment_label && (
                <span style={{
                    marginLeft: 'auto', 
                    fontSize: '0.9rem', 
                    padding: '0.35rem 1rem', 
                    borderRadius: '20px', 
                    fontWeight: 'bold',
                    backgroundColor: results.analysis.sentiment_label === 'Positive' ? 'rgba(0, 255, 100, 0.15)' : results.analysis.sentiment_label === 'Negative' ? 'rgba(255, 50, 50, 0.15)' : 'rgba(255, 200, 0, 0.15)',
                    color: results.analysis.sentiment_label === 'Positive' ? '#4ade80' : results.analysis.sentiment_label === 'Negative' ? '#f87171' : '#facc15',
                    border: `1px solid ${results.analysis.sentiment_label === 'Positive' ? 'rgba(74, 222, 128, 0.3)' : results.analysis.sentiment_label === 'Negative' ? 'rgba(248, 113, 113, 0.3)' : 'rgba(250, 204, 21, 0.3)'}`
                }}>
                    Sentiment: {results.analysis.sentiment_label}
                </span>
              )}
            </h2>
            <div className="rating-overview" style={{fontSize: '1.1rem', lineHeight: '1.7', marginTop: '1rem'}}>
              {results.analysis?.rating_overview}
            </div>
          </div>

          <div className="grid grid-cols-2">
            <div className="glass-panel">
               <h3 style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-success)'}}>
                 <CheckCircle size={20} /> Strengths
               </h3>
               <div className="pill-list">
                 {results.analysis?.strengths?.map((s, i) => s && s.trim() !== "" ? (
                   <div key={i} className="pill strength">{s}</div>
                 ) : null)}
               </div>
            </div>

            <div className="glass-panel">
               <h3 style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-danger)'}}>
                 <XCircle size={20} /> Weaknesses
               </h3>
               <div className="pill-list">
                 {results.analysis?.weaknesses?.map((w, i) => w && w.trim() !== "" ? (
                   <div key={i} className="pill weakness">{w}</div>
                 ) : null)}
               </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
