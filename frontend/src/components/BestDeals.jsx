import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, TrendingDown, Loader2 } from 'lucide-react';
import { marketAPI } from '../api';

const BestDeals = () => {
  const scrollRef = React.useRef(null);
  const [bestDeals, setBestDeals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBestDeals();
  }, []);

  const fetchBestDeals = async () => {
    try {
      const response = await marketAPI.getBestDeals(8);
      if (response.success) {
        setBestDeals(response.data);
      }
    } catch (error) {
      console.error('Error loading best deals:', error);
    } finally {
      setLoading(false);
    }
  };

  const scroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = 300;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  if (loading) {
    return (
      <div className="mb-8 flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
        <span className="ml-3 text-gray-400">Loading best deals...</span>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <TrendingDown className="w-6 h-6 text-emerald-400" />
          <span>Best Deals Right Now</span>
          <span className="text-sm font-normal text-gray-400 ml-2">Lowest prices in NCR</span>
        </h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => scroll('left')}
            className="p-2 hover:bg-slate-700 rounded-full transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-gray-400" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="p-2 hover:bg-slate-700 rounded-full transition-colors"
          >
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex space-x-4 overflow-x-auto scrollbar-hide pb-2"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {bestDeals.map((deal) => (
          <div
            key={deal.id}
            className="flex-shrink-0 w-64 bg-gradient-to-br from-emerald-900/40 to-emerald-800/20 rounded-lg p-4 border border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/20 transition-all"
          >
            <div className="flex items-start justify-between mb-2">
              <span className="text-3xl">{deal.icon}</span>
              <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-500/30 text-emerald-300 border border-emerald-500/50">
                MURA
              </span>
            </div>
            <h3 className="font-semibold text-white text-sm mb-1">{deal.name}</h3>
            <p className="text-xs text-gray-400 mb-2">{deal.location}</p>
            <div className="mb-2">
              <span className="text-2xl font-bold text-white">₱{deal.currentPrice}</span>
              <span className="text-sm text-gray-400 ml-1">/{deal.unit}</span>
            </div>
            <div className="flex items-center space-x-1 text-xs font-medium text-emerald-400 bg-emerald-500/20 px-2.5 py-1.5 rounded-md">
              <TrendingDown className="w-3 h-3" />
              <span>Save ₱{deal.savings}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BestDeals;
