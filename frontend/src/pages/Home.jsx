import React, { useState, useEffect } from 'react';
import { Search, BarChart3, Loader2, TrendingUp, TrendingDown, AlertTriangle, ShoppingCart, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import Navbar from '../components/Navbar';
import BestDeals from '../components/BestDeals';
import MarketCard from '../components/MarketCard';
import { marketAPI, categoryAPI, analyticsAPI } from '../api';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { toast } from '../hooks/use-toast';

const Home = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('best');
  const [searchQuery, setSearchQuery] = useState('');
  const [timePeriod, setTimePeriod] = useState('7D');
  const [favorites, setFavorites] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  // Fetch categories on mount
  useEffect(() => {
    fetchCategories();
    fetchAnalytics();
  }, []);

  // Fetch market items when filters change
  useEffect(() => {
    fetchMarketItems();
  }, [selectedCategory, searchQuery, sortBy]);

  const fetchCategories = async () => {
    try {
      const response = await categoryAPI.getAll();
      if (response.success) {
        const marketCategories = response.data.filter(cat => cat.id !== 'climate');
        setCategories(marketCategories);
      }
    } catch (error) {
      console.error('Error loading categories:', error);
      toast({
        title: "Error",
        description: "Failed to load categories",
        variant: "destructive"
      });
    }
  };

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const response = await analyticsAPI.getMarketAnalytics();
      if (response.success) {
        setAnalytics(response.data);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const fetchMarketItems = async () => {
    setLoading(true);
    try {
      const params = {
        category: selectedCategory !== 'all' ? selectedCategory : undefined,
        search: searchQuery || undefined,
        sort: sortBy,
        limit: 100
      };

      const response = await marketAPI.getAll(params);
      
      if (response.success) {
        setFilteredItems(response.data);
        if (response.data.length > 0 && response.data[0].lastUpdated) {
          setLastUpdate(new Date(response.data[0].lastUpdated));
        }
      }
    } catch (error) {
      console.error('Error loading market items:', error);
      toast({
        title: "Error",
        description: "Failed to load market data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = (id) => {
    setFavorites(prev => 
      prev.includes(id) ? prev.filter(fav => fav !== id) : [...prev, id]
    );
  };

  const getTrendIcon = (direction) => {
    if (direction === 'up') return <ArrowUpRight className="w-4 h-4 text-red-400" />;
    if (direction === 'down') return <ArrowDownRight className="w-4 h-4 text-emerald-400" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-3">
            <BarChart3 className="w-8 h-8 text-emerald-400" />
            <h1 className="text-3xl font-bold text-white">Climate-Smart Market Intelligence</h1>
          </div>
          <p className="text-gray-400 text-sm">
            Real-time price monitoring with climate impact analysis • Data from DA Bantay Presyo
          </p>
        </div>

        {/* Analytics Dashboard */}
        {!analyticsLoading && analytics && (
          <div className="mb-8" data-testid="analytics-section">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center space-x-2">
              <TrendingUp className="w-6 h-6 text-emerald-400" />
              <span>Market Analytics</span>
            </h2>
            
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <Card className="bg-gradient-to-br from-emerald-900/40 to-emerald-800/20 border-emerald-500/30 p-4" data-testid="mura-card">
                <p className="text-sm text-emerald-300 mb-1">MURA Items</p>
                <p className="text-3xl font-bold text-white">{analytics.price_summary.mura_count}</p>
                <p className="text-xs text-emerald-400 mt-1">Below average price</p>
              </Card>
              
              <Card className="bg-gradient-to-br from-red-900/40 to-red-800/20 border-red-500/30 p-4" data-testid="mahal-card">
                <p className="text-sm text-red-300 mb-1">MAHAL Items</p>
                <p className="text-3xl font-bold text-white">{analytics.price_summary.mahal_count}</p>
                <p className="text-xs text-red-400 mt-1">Above average price</p>
              </Card>
              
              <Card className="bg-slate-800 border-slate-700 p-4" data-testid="stability-card">
                <p className="text-sm text-gray-400 mb-1">Price Stability</p>
                <p className="text-3xl font-bold text-white">{analytics.price_summary.price_stability_index}%</p>
                <p className="text-xs text-gray-400 mt-1">of items stable</p>
              </Card>
              
              <Card className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border-blue-500/30 p-4" data-testid="savings-card">
                <p className="text-sm text-blue-300 mb-1">Potential Savings</p>
                <p className="text-3xl font-bold text-white">₱{analytics.price_summary.total_potential_savings.toLocaleString()}</p>
                <p className="text-xs text-blue-400 mt-1">across MURA items</p>
              </Card>
            </div>

            {/* Supply/Demand Insights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <Card className="bg-slate-800 border-slate-700 p-5" data-testid="supply-demand-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <ShoppingCart className="w-5 h-5 text-emerald-400" />
                  <span>Supply & Demand</span>
                </h3>
                <div className="space-y-3">
                  {analytics.supply_demand.slice(0, 5).map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <div>
                        <p className="text-white font-medium capitalize">{item.category}</p>
                        <p className="text-xs text-gray-400">{item.item_count} items tracked</p>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          item.supply_status === 'surplus' ? 'bg-emerald-500/20 text-emerald-400' :
                          item.supply_status === 'tight' ? 'bg-red-500/20 text-red-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {item.supply_status.toUpperCase()}
                        </span>
                        <p className="text-xs text-gray-400 mt-1">{item.mura_percentage}% mura</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="bg-slate-800 border-slate-700 p-5" data-testid="category-insights-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5 text-emerald-400" />
                  <span>Category Trends</span>
                </h3>
                <div className="space-y-3">
                  {analytics.category_insights.slice(0, 5).map((cat, idx) => (
                    <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <div className="flex items-center space-x-3">
                        {getTrendIcon(cat.trend_direction)}
                        <div>
                          <p className="text-white font-medium capitalize">{cat.category}</p>
                          <p className="text-xs text-gray-400">Avg ₱{cat.average_price}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-medium ${
                          cat.weekly_change_pct > 0 ? 'text-red-400' : 
                          cat.weekly_change_pct < 0 ? 'text-emerald-400' : 'text-gray-400'
                        }`}>
                          {cat.weekly_change_pct > 0 ? '+' : ''}{cat.weekly_change_pct}%
                        </p>
                        <p className="text-xs text-gray-400">weekly</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Price Alerts */}
            {analytics.price_alerts && analytics.price_alerts.length > 0 && (
              <Card className="bg-slate-800 border-slate-700 p-5 mb-6" data-testid="price-alerts-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  <span>Price Alerts</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {analytics.price_alerts.slice(0, 6).map((alert, idx) => (
                    <div key={idx} className={`p-3 rounded-lg border ${
                      alert.severity === 'high' ? 'bg-red-900/20 border-red-500/30' : 'bg-amber-900/20 border-amber-500/30'
                    }`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-white font-medium text-sm">{alert.item}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          alert.change_pct > 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {alert.change_pct > 0 ? '+' : ''}{alert.change_pct}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-400">{alert.message}</p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Top Movers */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="bg-slate-800 border-slate-700 p-5" data-testid="top-gainers-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-red-400" />
                  <span>Price Increases</span>
                </h3>
                <div className="space-y-2">
                  {analytics.top_movers.top_gainers.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <span className="text-white text-sm">{item.name}</span>
                      <span className="text-red-400 font-medium text-sm">+{item.change_pct}%</span>
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="bg-slate-800 border-slate-700 p-5" data-testid="top-losers-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <TrendingDown className="w-5 h-5 text-emerald-400" />
                  <span>Price Decreases</span>
                </h3>
                <div className="space-y-2">
                  {analytics.top_movers.top_losers.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <span className="text-white text-sm">{item.name}</span>
                      <span className="text-emerald-400 font-medium text-sm">{item.change_pct}%</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        {analyticsLoading && (
          <div className="mb-8">
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
              <span className="ml-3 text-gray-400">Loading analytics...</span>
            </div>
          </div>
        )}

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-2xl">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search items... (e.g., lettuce, chicken, diesel)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 pr-4 py-6 text-base rounded-lg bg-slate-800 border-slate-700 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              data-testid="search-input"
            />
          </div>
        </div>

        {/* Best Deals Section */}
        <BestDeals />

        {/* Main Content */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <span>NCR Market Prices</span>
            </h2>
            <div className="text-sm text-gray-400">
              {lastUpdate ? `Updated ${lastUpdate.toLocaleDateString()}` : 'Loading...'}
            </div>
          </div>

          {/* Category Tabs */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
              <span className="ml-3 text-gray-400">Loading real market data...</span>
            </div>
          ) : (
            <>
              <div className="flex items-center space-x-2 overflow-x-auto pb-4 mb-4">
                {categories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    data-testid={`category-${category.id}`}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                      selectedCategory === category.id
                        ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/30'
                        : 'bg-slate-800 text-gray-300 hover:bg-slate-700 border border-slate-700'
                    }`}
                  >
                    <span>{category.icon}</span>
                    <span>{category.name}</span>
                  </button>
                ))}
              </div>

          {/* Sort and Filter Options */}
          <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">Sort:</span>
              <div className="flex items-center space-x-1">
                <Button
                  variant={sortBy === 'best' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSortBy('best')}
                  data-testid="sort-best"
                  className={`${
                    sortBy === 'best' 
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white' 
                      : 'bg-slate-800 text-gray-300 hover:bg-slate-700 border-slate-700'
                  }`}
                >
                  Best Deals
                </Button>
                <Button
                  variant={sortBy === 'price-low' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSortBy('price-low')}
                  data-testid="sort-price-low"
                  className={`${
                    sortBy === 'price-low' 
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white' 
                      : 'bg-slate-800 text-gray-300 hover:bg-slate-700 border-slate-700'
                  }`}
                >
                  Price ↓
                </Button>
                <Button
                  variant={sortBy === 'price-high' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSortBy('price-high')}
                  data-testid="sort-price-high"
                  className={`${
                    sortBy === 'price-high' 
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white' 
                      : 'bg-slate-800 text-gray-300 hover:bg-slate-700 border-slate-700'
                  }`}
                >
                  Price ↑
                </Button>
                <Button
                  variant={sortBy === 'name' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSortBy('name')}
                  data-testid="sort-name"
                  className={`${
                    sortBy === 'name' 
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white' 
                      : 'bg-slate-800 text-gray-300 hover:bg-slate-700 border-slate-700'
                  }`}
                >
                  Name
                </Button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {['7D', '30D', '90D'].map((period) => (
                <Button
                  key={period}
                  variant={timePeriod === period ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTimePeriod(period)}
                  data-testid={`period-${period}`}
                  className={`${
                    timePeriod === period 
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white' 
                      : 'bg-slate-800 text-gray-300 hover:bg-slate-700 border-slate-700'
                  }`}
                >
                  {period}
                </Button>
              ))}
            </div>
          </div>

          {/* Market Items Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="market-items-grid">
            {filteredItems.map((item) => (
              <MarketCard
                key={item.id}
                item={item}
                onToggleFavorite={toggleFavorite}
                isFavorite={favorites.includes(item.id)}
              />
            ))}
          </div>

          {filteredItems.length === 0 && !loading && (
            <div className="text-center py-12">
              <p className="text-gray-500">No items found matching your criteria.</p>
            </div>
          )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-slate-800 text-center">
          <p className="text-sm text-gray-500">
            Data sourced from DA Bantay Presyo. Climate analysis powered by PAGASA and DENR. Not an official government app.
          </p>
          <div className="mt-4 flex items-center justify-center space-x-4">
            <a href="#" className="text-sm text-emerald-500 hover:text-emerald-400 font-medium">
              Support ClimateWatch
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
