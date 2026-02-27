import React, { useState, useEffect } from 'react';
import { Search, CloudRain, TrendingUp, AlertCircle, Info, Loader2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import ClimateCard from '../components/ClimateCard';
import { climateAPI } from '../api';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { toast } from '../hooks/use-toast';

const ClimateImpact = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [timePeriod, setTimePeriod] = useState('7D');
  const [favorites, setFavorites] = useState([]);
  const [climateMetrics, setClimateMetrics] = useState([]);
  const [filteredMetrics, setFilteredMetrics] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClimateMetrics();
  }, []);

  useEffect(() => {
    let filtered = climateMetrics;

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(m => 
        m.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredMetrics(filtered);
  }, [searchQuery, climateMetrics]);

  const fetchClimateMetrics = async () => {
    setLoading(true);
    try {
      const response = await climateAPI.getAll();
      if (response.success) {
        setClimateMetrics(response.data);
        setFilteredMetrics(response.data);
      }
    } catch (error) {
      console.error('Error loading climate metrics:', error);
      toast({
        title: "Error",
        description: "Failed to load climate data",
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

  // Calculate overall climate health score
  const goodCount = filteredMetrics.filter(m => m.status === 'GOOD').length;
  const moderateCount = filteredMetrics.filter(m => m.status === 'MODERATE').length;
  const warningCount = filteredMetrics.filter(m => m.status === 'WARNING').length;
  const alertCount = filteredMetrics.filter(m => m.status === 'ALERT').length;
  const total = filteredMetrics.length;
  const healthScore = total > 0 ? Math.round((goodCount / total) * 100) : 0;

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-3">
            <CloudRain className="w-8 h-8 text-emerald-400" />
            <h1 className="text-3xl font-bold text-white">Climate Impact Analysis</h1>
          </div>
          <p className="text-gray-400 text-sm">
            Real-time climate monitoring and market impact assessment • Data from PAGASA, DENR, and LGU monitoring stations
          </p>
        </div>

        {/* Climate Health Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-slate-800 border-slate-700 p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-400">Climate Health Score</p>
              <TrendingUp className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-4xl font-bold text-white">{healthScore}</span>
              <span className="text-lg text-gray-400">%</span>
            </div>
            <p className="text-xs text-emerald-400 mt-2">Overall conditions favorable</p>
          </Card>

          <Card className="bg-slate-800 border-slate-700 p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-400">Good Conditions</p>
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-4xl font-bold text-white">{goodCount}</span>
              <span className="text-lg text-gray-400">/ {total}</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">Metrics in optimal range</p>
          </Card>

          <Card className="bg-slate-800 border-slate-700 p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-400">Moderate</p>
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-4xl font-bold text-white">{moderateCount}</span>
              <span className="text-lg text-gray-400">/ {total}</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">Requires monitoring</p>
          </Card>

          <Card className="bg-slate-800 border-slate-700 p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-400">Warnings</p>
              <AlertCircle className="w-5 h-5 text-orange-400" />
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-4xl font-bold text-white">{warningCount + alertCount}</span>
              <span className="text-lg text-gray-400">/ {total}</span>
            </div>
            <p className="text-xs text-orange-400 mt-2">Needs attention</p>
          </Card>
        </div>

        {/* Market Impact Summary */}
        <div className="bg-gradient-to-r from-blue-900/30 to-emerald-900/30 border border-blue-500/30 rounded-lg p-6 mb-8">
          <div className="flex items-start space-x-4">
            <Info className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Key Market Impact Insights</h3>
              <div className="space-y-2 text-sm text-gray-300">
                <p>• <span className="text-emerald-400 font-medium">Lower temperatures</span> are supporting vegetable growth, keeping prices down for lettuce, broccoli, and leafy greens.</p>
                <p>• <span className="text-emerald-400 font-medium">Adequate rainfall</span> has improved soil moisture, stabilizing rice and vegetable supplies across NCR.</p>
                <p>• <span className="text-amber-400 font-medium">Higher humidity</span> may increase disease pressure on crops, monitor for potential price impacts in coming weeks.</p>
                <p>• <span className="text-orange-400 font-medium">Elevated UV levels</span> are affecting livestock, potentially increasing poultry and meat prices if conditions persist.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-2xl">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search climate metrics... (e.g., temperature, rainfall, humidity)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 pr-4 py-6 text-base rounded-lg bg-slate-800 border-slate-700 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Main Content */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <span>🌡️</span>
              <span>Climate Metrics</span>
            </h2>
            <div className="flex items-center space-x-2">
              {['7D', '30D', '90D'].map((period) => (
                <Button
                  key={period}
                  variant={timePeriod === period ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTimePeriod(period)}
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

          {/* Climate Metrics Grid */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
              <span className="ml-3 text-gray-400">Loading climate data...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {filteredMetrics.map((metric) => (
                <ClimateCard
                  key={metric.id}
                  metric={metric}
                  onToggleFavorite={toggleFavorite}
                  isFavorite={favorites.includes(metric.id)}
                />
              ))}
            </div>
          )}

          {filteredMetrics.length === 0 && !loading && (
            <div className="text-center py-12">
              <p className="text-gray-500">No climate metrics found matching your criteria.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-slate-800 text-center">
          <p className="text-sm text-gray-500">
            📊 Climate data sourced from PAGASA, DENR, and LGU monitoring stations. Updated hourly. Not an official government app.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ClimateImpact;