import React, { useState } from 'react';
import { Heart, TrendingDown, TrendingUp, Info, AlertTriangle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';

const MarketCard = ({ item, onToggleFavorite, isFavorite }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getStatusColor = (status) => {
    switch (status) {
      case 'MURA':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
      case 'STABLE':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      case 'MAHAL':
        return 'bg-red-500/20 text-red-400 border-red-500/50';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const getClimateImpactColor = (level) => {
    switch (level) {
      case 'low':
        return 'text-emerald-400';
      case 'medium':
        return 'text-amber-400';
      case 'high':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const isCheaper = item.currentPrice < item.averagePrice;

  const renderSparkline = () => {
    const maxValue = Math.max(...item.trend);
    const minValue = Math.min(...item.trend);
    const range = maxValue - minValue || 1;
    const width = 100;
    const height = 40;
    const points = item.trend.map((value, index) => {
      const x = (index / (item.trend.length - 1)) * width;
      const y = height - ((value - minValue) / range) * height;
      return `${x},${y}`;
    });

    const lineColor = item.status === 'MURA' ? '#10b981' : 
                      item.status === 'STABLE' ? '#f59e0b' : '#ef4444';

    return (
      <svg width="100%" height="40" viewBox="0 0 100 40" preserveAspectRatio="none" className="mt-3">
        <defs>
          <linearGradient id={`gradient-${item.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.3" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon
          points={`0,40 ${points.join(' ')} 100,40`}
          fill={`url(#gradient-${item.id})`}
        />
        <polyline
          points={points.join(' ')}
          fill="none"
          stroke={lineColor}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  return (
    <>
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 hover:shadow-xl hover:shadow-emerald-500/10 hover:border-slate-600 transition-all duration-300 group">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-3xl">{item.icon}</span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onToggleFavorite(item.id)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <Heart
                  className={`w-4 h-4 ${
                    isFavorite ? 'fill-emerald-500 text-emerald-500' : 'text-gray-400'
                  }`}
                />
              </button>
              <button
                onClick={() => setShowDetails(true)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <Info className="w-4 h-4 text-gray-400 hover:text-emerald-400" />
              </button>
            </div>
          </div>
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${getStatusColor(item.status)}`}>
            {item.status}
          </span>
        </div>

        {/* Item name */}
        <h3 className="font-semibold text-white text-sm mb-1">{item.name}</h3>
        <p className="text-xs text-gray-400 mb-3">{item.location}</p>

        {/* Current price */}
        <div className="mb-2">
          <span className="text-3xl font-bold text-white">₱{item.currentPrice}</span>
          <span className="text-sm text-gray-400 ml-1">/{item.unit}</span>
        </div>

        {/* Comparison */}
        <div className="flex items-center space-x-2 mb-2">
          <div className="flex-1">
            <div className={`text-xs px-2.5 py-1 rounded-md flex items-center space-x-1 ${
              isCheaper ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
            }`}>
              {isCheaper ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
              <span className="font-medium">
                {isCheaper ? 'Save' : '+'} ₱{Math.abs(item.savings).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Average price */}
        <div className="text-xs text-gray-500 mb-3">
          Avg: ₱{item.averagePrice}/{item.unit}
        </div>

        {/* Trend chart */}
        {renderSparkline()}

        {/* Climate impact indicator */}
        {item.climateImpact && (
          <div className="mt-3 pt-3 border-t border-slate-700">
            <div className="flex items-start space-x-2">
              <AlertTriangle className={`w-3 h-3 mt-0.5 flex-shrink-0 ${getClimateImpactColor(item.climateImpact.level)}`} />
              <p className="text-xs text-gray-400 leading-relaxed">
                {item.climateImpact.forecast}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Details Dialog */}
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="max-w-2xl bg-slate-800 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2 text-white">
              <span className="text-3xl">{item.icon}</span>
              <span>{item.name}</span>
            </DialogTitle>
            <DialogDescription className="text-gray-400">{item.location}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                <p className="text-sm text-gray-400 mb-1">Current Price</p>
                <p className="text-2xl font-bold text-white">
                  ₱{item.currentPrice} <span className="text-sm text-gray-400">/{item.unit}</span>
                </p>
              </div>
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                <p className="text-sm text-gray-400 mb-1">Average Price</p>
                <p className="text-2xl font-bold text-white">
                  ₱{item.averagePrice} <span className="text-sm text-gray-400">/{item.unit}</span>
                </p>
              </div>
            </div>
            
            {item.climateImpact && (
              <div className="bg-slate-900 border-l-4 border-emerald-500 p-4 rounded">
                <p className="text-sm font-semibold text-emerald-400 mb-2">Climate Impact Analysis</p>
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Impact Level</p>
                    <p className={`text-sm font-medium ${getClimateImpactColor(item.climateImpact.level)}`}>
                      {item.climateImpact.level.toUpperCase()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Factors</p>
                    <ul className="text-sm text-gray-300 space-y-1">
                      {item.climateImpact.factors.map((factor, idx) => (
                        <li key={idx}>• {factor}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Forecast</p>
                    <p className="text-sm text-gray-300">{item.climateImpact.forecast}</p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <p className="text-sm font-medium text-gray-300 mb-2">7-Day Price Trend</p>
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                {renderSparkline()}
              </div>
            </div>

            <div className="text-xs text-gray-500">
              Last updated: {new Date(item.lastUpdated).toLocaleString()}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default MarketCard;
