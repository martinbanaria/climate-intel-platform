import React, { useState } from 'react';
import { Heart, Info, AlertTriangle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';

const ClimateCard = ({ metric, onToggleFavorite, isFavorite }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getStatusColor = (status) => {
    switch (status) {
      case 'GOOD':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
      case 'MODERATE':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      case 'WARNING':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
      case 'ALERT':
        return 'bg-red-500/20 text-red-400 border-red-500/50';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const isBetter = metric.currentValue < metric.averageValue || 
                   (metric.status === 'GOOD' && metric.currentValue !== metric.averageValue);

  const renderSparkline = () => {
    const maxValue = Math.max(...metric.trend);
    const minValue = Math.min(...metric.trend);
    const range = maxValue - minValue || 1;
    const width = 100;
    const height = 40;
    const points = metric.trend.map((value, index) => {
      const x = (index / (metric.trend.length - 1)) * width;
      const y = height - ((value - minValue) / range) * height;
      return `${x},${y}`;
    });

    const lineColor = metric.status === 'GOOD' ? '#10b981' : 
                      metric.status === 'MODERATE' ? '#f59e0b' :
                      metric.status === 'WARNING' ? '#f97316' : '#ef4444';

    return (
      <svg width="100%" height="40" viewBox="0 0 100 40" preserveAspectRatio="none" className="mt-3">
        <defs>
          <linearGradient id={`gradient-${metric.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.3" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon
          points={`0,40 ${points.join(' ')} 100,40`}
          fill={`url(#gradient-${metric.id})`}
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
            <span className="text-3xl">{metric.icon}</span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onToggleFavorite(metric.id)}
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
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${getStatusColor(metric.status)}`}>
            {metric.status}
          </span>
        </div>

        {/* Metric name */}
        <h3 className="font-semibold text-white text-sm mb-1">{metric.name}</h3>
        <p className="text-xs text-gray-400 mb-3">NCR Region</p>

        {/* Current value */}
        <div className="mb-2">
          <span className="text-3xl font-bold text-white">{metric.currentValue}</span>
          <span className="text-sm text-gray-400 ml-1">{metric.unit}</span>
        </div>

        {/* Comparison */}
        <div className="text-xs text-gray-500 mb-3">
          Avg: {metric.averageValue}{metric.unit}
        </div>

        {/* Trend chart */}
        {renderSparkline()}

        {/* Climate impact indicator */}
        {metric.impact && (
          <div className="mt-3 pt-3 border-t border-slate-700">
            <div className="flex items-start space-x-2">
              <AlertTriangle className={`w-3 h-3 mt-0.5 flex-shrink-0 text-emerald-400`} />
              <p className="text-xs text-gray-400 leading-relaxed">
                {metric.impact}
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
              <span className="text-3xl">{metric.icon}</span>
              <span>{metric.name}</span>
            </DialogTitle>
            <DialogDescription className="text-gray-400">NCR Climate Monitoring</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                <p className="text-sm text-gray-400 mb-1">Current Reading</p>
                <p className="text-2xl font-bold text-white">
                  {metric.currentValue} <span className="text-sm text-gray-400">{metric.unit}</span>
                </p>
              </div>
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                <p className="text-sm text-gray-400 mb-1">Average Reading</p>
                <p className="text-2xl font-bold text-white">
                  {metric.averageValue} <span className="text-sm text-gray-400">{metric.unit}</span>
                </p>
              </div>
            </div>
            
            <div className="bg-slate-900 border-l-4 border-emerald-500 p-4 rounded">
              <p className="text-sm font-semibold text-emerald-400 mb-2">Climate Advisory</p>
              <p className="text-sm text-gray-300">{metric.recommendation}</p>
            </div>

            <div className="bg-slate-900 border-l-4 border-blue-500 p-4 rounded">
              <p className="text-sm font-semibold text-blue-400 mb-2">Market Impact</p>
              <p className="text-sm text-gray-300">{metric.impact}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-300 mb-2">7-Day Trend</p>
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                {renderSparkline()}
              </div>
            </div>

            <div className="text-xs text-gray-500">
              Last updated: {new Date(metric.lastUpdated).toLocaleString()}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ClimateCard;
