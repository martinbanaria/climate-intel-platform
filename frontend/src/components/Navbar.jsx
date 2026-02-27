import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Settings, Bell, TrendingUp } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { name: 'Market Prices', path: '/' },
    { name: 'Climate Impact', path: '/climate' },
    { name: 'Energy Intelligence', path: '/energy' },
    { name: 'Forecasts', path: '/forecasts' },
    { name: 'Watchlist', path: '/watchlist' }
  ];

  return (
    <nav className="bg-slate-900 border-b border-slate-700 sticky top-0 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-emerald-400" />
            <div>
              <span className="text-xl font-bold text-white">ClimateWatch</span>
              <span className="block text-xs text-emerald-400">Market Intelligence</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === item.path
                    ? 'bg-emerald-600 text-white'
                    : 'text-gray-300 hover:bg-slate-800 hover:text-emerald-400'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>

          {/* Right side icons */}
          <div className="flex items-center space-x-4">
            <button className="p-2 hover:bg-slate-800 rounded-full transition-colors relative">
              <Bell className="w-5 h-5 text-gray-300" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
            </button>
            <button className="p-2 hover:bg-slate-800 rounded-full transition-colors">
              <Settings className="w-5 h-5 text-gray-300" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
