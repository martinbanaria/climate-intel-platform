import React, { useState, useEffect } from 'react';
import { Zap, TrendingUp, TrendingDown, Activity, FileText, Loader2, Sun, Wind, Droplet, Flame, BarChart3, AlertCircle, ExternalLink, RefreshCw } from 'lucide-react';
import Navbar from '../components/Navbar';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { energyAPI } from '../api';

const EnergyIntelligence = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [gridStatus, setGridStatus] = useState(null);
  const [ppaList, setPpaList] = useState([]);
  const [news, setNews] = useState([]);
  const [circulars, setCirculars] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchEnergyData();
  }, []);

  const fetchEnergyData = async () => {
    setLoading(true);
    try {
      const [gridRes, ppaRes, newsRes, circularRes, analyticsRes] = await Promise.all([
        energyAPI.getGridStatus(),
        energyAPI.getPPAStatuses(),
        energyAPI.getNews(),
        energyAPI.getDOECirculars(),
        energyAPI.getAnalytics()
      ]);

      if (gridRes.success) setGridStatus(gridRes.data);
      if (ppaRes.success) setPpaList(ppaRes.data);
      if (newsRes.success) setNews(newsRes.data);
      if (circularRes.success) setCirculars(circularRes.data);
      if (analyticsRes.success) setAnalytics(analyticsRes.data);
    } catch (error) {
      console.error('Error fetching energy data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchEnergyData();
    setRefreshing(false);
  };

  const getTechIcon = (tech) => {
    switch (tech?.toLowerCase()) {
      case 'solar pv':
      case 'solar':
        return <Sun className="w-5 h-5 text-amber-400" />;
      case 'wind':
        return <Wind className="w-5 h-5 text-blue-400" />;
      case 'hydro':
      case 'hydroelectric':
        return <Droplet className="w-5 h-5 text-cyan-400" />;
      case 'geothermal':
        return <Flame className="w-5 h-5 text-orange-400" />;
      default:
        return <Zap className="w-5 h-5 text-emerald-400" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950">
        <Navbar />
        <div className="flex items-center justify-center h-[calc(100vh-80px)]">
          <Loader2 className="w-12 h-12 animate-spin text-emerald-400" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-3 mb-3">
              <Zap className="w-8 h-8 text-emerald-400" />
              <h1 className="text-3xl font-bold text-white">Energy Intelligence</h1>
            </div>
            <p className="text-gray-400 text-sm">
              Real-time WESM prices, PPA tracking, and energy market analytics
            </p>
          </div>
          <Button 
            onClick={handleRefresh} 
            disabled={refreshing}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center space-x-2 mb-6 overflow-x-auto pb-2">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'prices', label: 'Prices', icon: TrendingUp },
            { id: 'contracts', label: 'PPAs & Contracts', icon: FileText },
            { id: 'news', label: 'News & Circulars', icon: ExternalLink }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              data-testid={`tab-${tab.id}`}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/30'
                  : 'bg-slate-800 text-gray-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div data-testid="overview-section">
            {/* Grid Status */}
            {gridStatus && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <Card className="bg-gradient-to-br from-emerald-900/40 to-emerald-800/20 border-emerald-500/30 p-6" data-testid="grid-status-card">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-emerald-300">Grid Status</p>
                    <Activity className="w-5 h-5 text-emerald-400" />
                  </div>
                  <span className="text-3xl font-bold text-white">{gridStatus.status}</span>
                  <p className="text-xs text-emerald-400 mt-2">All systems operational</p>
                </Card>

                <Card className="bg-slate-800 border-slate-700 p-6" data-testid="demand-card">
                  <p className="text-sm text-gray-400 mb-2">Total Demand</p>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-3xl font-bold text-white">{gridStatus.total_demand?.toLocaleString()}</span>
                    <span className="text-lg text-gray-400">MW</span>
                  </div>
                </Card>

                <Card className="bg-slate-800 border-slate-700 p-6" data-testid="supply-card">
                  <p className="text-sm text-gray-400 mb-2">Total Supply</p>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-3xl font-bold text-white">{gridStatus.total_supply?.toLocaleString()}</span>
                    <span className="text-lg text-gray-400">MW</span>
                  </div>
                </Card>

                <Card className="bg-slate-800 border-slate-700 p-6" data-testid="reserves-card">
                  <p className="text-sm text-gray-400 mb-2">Reserves</p>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-3xl font-bold text-white">{gridStatus.reserves}</span>
                    <span className="text-lg text-gray-400">MW</span>
                  </div>
                </Card>
              </div>
            )}

            {/* Analytics Summary */}
            {analytics && (
              <>
                {/* PPA Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <Card className="bg-slate-800 border-slate-700 p-6" data-testid="total-capacity-card">
                    <p className="text-sm text-gray-400 mb-2">Total PPA Capacity</p>
                    <span className="text-4xl font-bold text-white">{analytics.ppa_summary.total_capacity_mw}</span>
                    <span className="text-lg text-gray-400 ml-2">MW</span>
                    <p className="text-xs text-gray-500 mt-2">{analytics.ppa_summary.total_projects} projects tracked</p>
                  </Card>

                  <Card className="bg-gradient-to-br from-emerald-900/40 to-emerald-800/20 border-emerald-500/30 p-6" data-testid="operational-card">
                    <p className="text-sm text-emerald-300 mb-2">Operational</p>
                    <span className="text-4xl font-bold text-white">{analytics.ppa_summary.operational_capacity}</span>
                    <span className="text-lg text-gray-400 ml-2">MW</span>
                    <p className="text-xs text-emerald-400 mt-2">{analytics.ppa_summary.operational_count} projects online</p>
                  </Card>

                  <Card className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border-amber-500/30 p-6" data-testid="construction-card">
                    <p className="text-sm text-amber-300 mb-2">Under Construction</p>
                    <span className="text-4xl font-bold text-white">{analytics.ppa_summary.under_construction_capacity}</span>
                    <span className="text-lg text-gray-400 ml-2">MW</span>
                    <p className="text-xs text-amber-400 mt-2">{analytics.ppa_summary.under_construction_count} projects building</p>
                  </Card>
                </div>

                {/* Technology Breakdown */}
                <Card className="bg-slate-800 border-slate-700 p-6 mb-8" data-testid="tech-breakdown-card">
                  <h3 className="text-lg font-semibold text-white mb-4">Technology Mix</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(analytics.technology_breakdown).map(([tech, data]) => (
                      <div key={tech} className="flex items-center space-x-3 p-3 bg-slate-700/50 rounded-lg">
                        {getTechIcon(tech)}
                        <div>
                          <p className="text-white font-medium">{tech}</p>
                          <p className="text-sm text-gray-400">{data.capacity_mw} MW</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Alerts */}
                {analytics.alerts && analytics.alerts.length > 0 && (
                  <Card className="bg-slate-800 border-slate-700 p-6 mb-8" data-testid="alerts-card">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                      <AlertCircle className="w-5 h-5 text-amber-400" />
                      <span>Market Alerts</span>
                    </h3>
                    <div className="space-y-3">
                      {analytics.alerts.map((alert, idx) => (
                        <div key={idx} className={`p-4 rounded-lg border ${
                          alert.severity === 'high' ? 'bg-red-900/20 border-red-500/30' :
                          alert.severity === 'medium' ? 'bg-amber-900/20 border-amber-500/30' :
                          'bg-blue-900/20 border-blue-500/30'
                        }`}>
                          <div className="flex items-center justify-between">
                            <span className="text-white font-medium">{alert.message}</span>
                            <span className={`text-xs px-2 py-1 rounded ${
                              alert.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                              alert.severity === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                              'bg-blue-500/20 text-blue-400'
                            }`}>
                              {alert.type.toUpperCase()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </>
            )}
          </div>
        )}

        {/* Prices Tab */}
        {activeTab === 'prices' && analytics && (
          <div data-testid="prices-section">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              {Object.entries(analytics.price_trends).map(([region, data]) => (
                <Card key={region} className="bg-slate-800 border-slate-700 p-6" data-testid={`price-${region}`}>
                  <h3 className="text-lg font-bold text-white mb-1 capitalize">
                    {region.replace('wesm_', 'WESM ')}
                  </h3>
                  <div className="flex items-baseline space-x-2 mb-2">
                    <span className="text-4xl font-bold text-white">₱{data.current.toLocaleString()}</span>
                    <span className="text-lg text-gray-400">/MWh</span>
                  </div>
                  <div className="flex items-center space-x-2 mb-4">
                    {data.change_pct > 0 ? (
                      <TrendingUp className="w-4 h-4 text-red-400" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-emerald-400" />
                    )}
                    <span className={`text-sm ${data.change_pct > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {data.change_pct > 0 ? '+' : ''}{data.change_pct}% vs last week
                    </span>
                  </div>
                  
                  {/* Mini Trend Chart */}
                  <div className="h-16 flex items-end space-x-1">
                    {data.trend.map((val, idx) => {
                      const max = Math.max(...data.trend);
                      const min = Math.min(...data.trend);
                      const height = ((val - min) / (max - min)) * 100 || 50;
                      return (
                        <div
                          key={idx}
                          className="flex-1 bg-emerald-500/50 rounded-t"
                          style={{ height: `${Math.max(height, 10)}%` }}
                        />
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-2">
                    <span>6 weeks ago</span>
                    <span>Now</span>
                  </div>
                </Card>
              ))}
            </div>

            {/* Market Outlook */}
            <Card className="bg-slate-800 border-slate-700 p-6" data-testid="outlook-card">
              <h3 className="text-lg font-semibold text-white mb-4">Market Outlook</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="p-4 bg-slate-700/50 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Short-term</p>
                  <p className="text-lg font-medium text-white capitalize">{analytics.market_outlook.short_term}</p>
                </div>
                <div className="p-4 bg-slate-700/50 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Supply Adequacy</p>
                  <p className="text-lg font-medium text-white capitalize">{analytics.market_outlook.supply_adequacy}</p>
                </div>
                <div className="p-4 bg-slate-700/50 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Price Forecast</p>
                  <p className="text-lg font-medium text-white capitalize">{analytics.market_outlook.price_forecast.replace('_', ' ')}</p>
                </div>
              </div>
              
              <h4 className="text-sm font-medium text-gray-400 mb-2">Key Drivers</h4>
              <ul className="space-y-2">
                {analytics.market_outlook.key_drivers.map((driver, idx) => (
                  <li key={idx} className="flex items-center space-x-2 text-gray-300 text-sm">
                    <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
                    <span>{driver}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        )}

        {/* Contracts Tab */}
        {activeTab === 'contracts' && (
          <div data-testid="contracts-section">
            <Card className="bg-slate-800 border-slate-700">
              <div className="p-4 border-b border-slate-700">
                <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                  <FileText className="w-5 h-5 text-emerald-400" />
                  <span>Power Purchase Agreements Portfolio</span>
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left p-4 text-sm font-medium text-gray-400">Project</th>
                      <th className="text-left p-4 text-sm font-medium text-gray-400">Technology</th>
                      <th className="text-left p-4 text-sm font-medium text-gray-400">Capacity</th>
                      <th className="text-left p-4 text-sm font-medium text-gray-400">Status</th>
                      <th className="text-left p-4 text-sm font-medium text-gray-400">Off-taker</th>
                      <th className="text-left p-4 text-sm font-medium text-gray-400">Term</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ppaList.map((ppa, idx) => (
                      <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/50" data-testid={`ppa-row-${idx}`}>
                        <td className="p-4">
                          <div className="flex items-center space-x-3">
                            {getTechIcon(ppa.technology)}
                            <span className="text-white font-medium">{ppa.project}</span>
                          </div>
                        </td>
                        <td className="p-4 text-gray-300">{ppa.technology}</td>
                        <td className="p-4">
                          <span className="text-white font-medium">{ppa.capacity_mw}</span>
                          <span className="text-gray-400 ml-1">MW</span>
                        </td>
                        <td className="p-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            ppa.status === 'Operational' ? 'bg-emerald-500/20 text-emerald-400' :
                            ppa.status === 'Under Construction' ? 'bg-amber-500/20 text-amber-400' :
                            'bg-blue-500/20 text-blue-400'
                          }`}>
                            {ppa.status}
                          </span>
                        </td>
                        <td className="p-4 text-gray-300">{ppa.off_taker}</td>
                        <td className="p-4 text-gray-300">{ppa.term_years} years</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* News Tab */}
        {activeTab === 'news' && (
          <div data-testid="news-section">
            {/* Energy News */}
            <div className="mb-8">
              <h2 className="text-xl font-bold text-white mb-4">Latest Energy News</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {news.map((article, idx) => (
                  <Card key={idx} className="bg-slate-800 border-slate-700 p-6 hover:border-emerald-500/50 transition-colors" data-testid={`news-${idx}`}>
                    <h3 className="text-white font-semibold mb-2 line-clamp-2">{article.title}</h3>
                    <p className="text-sm text-gray-400 mb-4 line-clamp-3">{article.description}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-emerald-400">{article.source}</span>
                      <span className="text-gray-500">
                        {article.published ? new Date(article.published).toLocaleDateString() : 'Recent'}
                      </span>
                    </div>
                    {article.url && article.url !== '#' && (
                      <a 
                        href={article.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="mt-3 inline-flex items-center text-sm text-emerald-400 hover:text-emerald-300"
                      >
                        Read more <ExternalLink className="w-3 h-3 ml-1" />
                      </a>
                    )}
                  </Card>
                ))}
              </div>
            </div>

            {/* DOE Circulars */}
            <div>
              <h2 className="text-xl font-bold text-white mb-4">DOE Circulars & Orders</h2>
              <div className="space-y-3">
                {circulars.map((circular, idx) => (
                  <Card key={idx} className="bg-slate-800 border-slate-700 p-5 hover:border-emerald-500/50 transition-colors" data-testid={`circular-${idx}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <FileText className="w-4 h-4 text-emerald-400" />
                          <span className="text-xs text-emerald-400 font-medium">{circular.document_number}</span>
                        </div>
                        <h3 className="text-white font-medium mb-2">{circular.title}</h3>
                        <p className="text-sm text-gray-400">{circular.summary}</p>
                        {circular.effective_date && (
                          <p className="text-xs text-gray-500 mt-2">Effective: {circular.effective_date}</p>
                        )}
                      </div>
                      <span className="text-xs text-gray-500 whitespace-nowrap ml-4">{circular.date}</span>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnergyIntelligence;
