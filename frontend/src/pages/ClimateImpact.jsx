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

  // Compute market impact insights from real metric values
  const computeInsights = (metrics) => {
    const get = (name) => metrics.find(m => m.metric_name === name || m.name === name) || {};
    const temp = parseFloat(get('Temperature').value) || 28;
    const rainfall = parseFloat(get('Rainfall').value) || 0;
    const humidity = parseFloat(get('Humidity').value) || 70;
    const droughtIdx = parseFloat(get('Drought Index').value) || 3;
    const uv = parseFloat(get('UV Index').value) || 7;

    const insights = [];

    // Temperature insight
    if (temp > 33) {
      insights.push({ color: 'text-red-400', label: `Extreme heat (${temp}°C)`, body: 'causing heat stress in livestock — poultry and meat prices may rise.' });
    } else if (temp > 30) {
      insights.push({ color: 'text-amber-400', label: `High temperature (${temp}°C)`, body: 'may stress poultry production. Monitor meat and egg prices.' });
    } else {
      insights.push({ color: 'text-emerald-400', label: `Favorable temperature (${temp}°C)`, body: 'supporting vegetable and crop growth, keeping leafy green prices stable.' });
    }

    // Rainfall / drought insight
    if (droughtIdx > 5) {
      insights.push({ color: 'text-red-400', label: `Drought index ${droughtIdx.toFixed(1)} (elevated)`, body: 'soil moisture below optimal — spice and vegetable yields may be constrained.' });
    } else if (rainfall > 20) {
      insights.push({ color: 'text-amber-400', label: `Heavy rainfall (${rainfall}mm)`, body: 'may damage leafy vegetables; flood risk in low-lying farms.' });
    } else if (rainfall > 0) {
      insights.push({ color: 'text-emerald-400', label: `Moderate rainfall (${rainfall}mm)`, body: 'maintaining soil moisture for rice and vegetable production.' });
    } else {
      insights.push({ color: 'text-amber-400', label: 'No rainfall today', body: `dry conditions (drought index ${droughtIdx.toFixed(1)}) — irrigation costs elevated for rice and spice farms.` });
    }

    // Humidity insight
    if (humidity > 85) {
      insights.push({ color: 'text-amber-400', label: `High humidity (${humidity}%)`, body: 'increases disease pressure on leafy vegetables; monitor for supply disruptions.' });
    } else if (humidity < 50) {
      insights.push({ color: 'text-amber-400', label: `Low humidity (${humidity}%)`, body: 'may stress crops and reduce yields.' });
    } else {
      insights.push({ color: 'text-emerald-400', label: `Optimal humidity (${humidity}%)`, body: 'supporting healthy crop development with low disease risk.' });
    }

    // UV insight
    if (uv > 10) {
      insights.push({ color: 'text-orange-400', label: `Very high UV index (${uv})`, body: 'intensifying heat on livestock; watch for price impact on poultry and eggs.' });
    } else if (uv < 4) {
      insights.push({ color: 'text-blue-400', label: `Low UV index (${uv})`, body: 'reduced sunlight may slow crop maturation — minor supply effect.' });
    } else {
      insights.push({ color: 'text-emerald-400', label: `Normal UV index (${uv})`, body: 'supporting photosynthesis without crop stress.' });
    }

    return insights;
  };

  const marketInsights = climateMetrics.length > 0 ? computeInsights(climateMetrics) : [];

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
            Real-time climate monitoring and market impact assessment • Data from WeatherAPI.com (Manila, NCR)
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

        {/* Market Impact Summary — computed from live WeatherAPI metrics */}
        {marketInsights.length > 0 && (
          <div className="bg-gradient-to-r from-blue-900/30 to-emerald-900/30 border border-blue-500/30 rounded-lg p-6 mb-8">
            <div className="flex items-start space-x-4">
              <Info className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-white mb-1">Key Market Impact Insights</h3>
                <p className="text-xs text-gray-500 mb-3">Computed from live WeatherAPI.com metrics (Manila, NCR).</p>
                <div className="space-y-2 text-sm text-gray-300">
                  {marketInsights.map((ins, i) => (
                    <p key={i}>• <span className={`${ins.color} font-medium`}>{ins.label}</span> {ins.body}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

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
            Live weather data sourced from WeatherAPI.com (Manila, NCR). Soil moisture and drought index are derived estimates. Updated daily. Not an official government app.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ClimateImpact;