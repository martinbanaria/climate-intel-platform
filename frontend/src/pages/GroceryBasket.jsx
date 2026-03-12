import React, { useState, useEffect } from 'react';
import { ShoppingCart, Loader2, Search, Plus, X, TrendingDown } from 'lucide-react';
import Navbar from '../components/Navbar';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from '../hooks/use-toast';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GroceryBasket = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [customItems, setCustomItems] = useState('');
  const [customBasket, setCustomBasket] = useState(null);
  const [customLoading, setCustomLoading] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/basket/templates`);
      if (response.data.success) {
        setTemplates(response.data.data);
      }
    } catch (error) {
      console.error('Error loading basket templates:', error);
      toast({
        title: "Error",
        description: "Failed to load basket templates",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomBasket = async () => {
    if (!customItems.trim()) return;
    setCustomLoading(true);
    try {
      const response = await axios.get(`${API}/basket/cheapest`, {
        params: { items: customItems }
      });
      if (response.data.success) {
        setCustomBasket(response.data);
      }
    } catch (error) {
      console.error('Error building custom basket:', error);
      toast({
        title: "Error",
        description: "Failed to build basket. Try different item names.",
        variant: "destructive"
      });
    } finally {
      setCustomLoading(false);
    }
  };

  const BasketCard = ({ template }) => (
    <Card className="bg-slate-800 border-slate-700 p-6 hover:border-emerald-500/50 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{template.name}</h3>
          <p className="text-sm text-gray-400 mt-1">{template.description}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-white">₱{template.total_cost}</p>
          <p className="text-xs text-gray-500">{template.item_count} items</p>
        </div>
      </div>

      <div className="space-y-2">
        {template.basket.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
            <div className="flex items-center space-x-2">
              <span className="text-lg">{item.icon || '📦'}</span>
              <div>
                <p className="text-sm text-white">{item.name}</p>
                <p className="text-xs text-gray-500">{item.category}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-white">₱{item.currentPrice}/{item.unit}</p>
              {item.savings > 0 && (
                <p className="text-xs text-emerald-400 flex items-center justify-end space-x-1">
                  <TrendingDown className="w-3 h-3" />
                  <span>Save ₱{item.savings.toFixed(2)}</span>
                </p>
              )}
            </div>
          </div>
        ))}
        {template.not_found && template.not_found.length > 0 && (
          <p className="text-xs text-gray-600 mt-2">
            Not found: {template.not_found.join(', ')}
          </p>
        )}
      </div>
    </Card>
  );

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-3">
            <ShoppingCart className="w-8 h-8 text-emerald-400" />
            <h1 className="text-3xl font-bold text-white">Cheapest Grocery Basket</h1>
          </div>
          <p className="text-gray-400 text-sm">
            Find the lowest-cost combination of groceries from DA Bantay Presyo prices (NCR)
          </p>
        </div>

        {/* Custom Basket Builder */}
        <Card className="bg-gradient-to-r from-emerald-900/30 to-blue-900/30 border-emerald-500/30 p-6 mb-8">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center space-x-2">
            <Plus className="w-5 h-5 text-emerald-400" />
            <span>Build Your Own Basket</span>
          </h2>
          <p className="text-sm text-gray-400 mb-4">
            Enter comma-separated items (e.g., rice, chicken, tomato, onion, garlic)
          </p>
          <div className="flex space-x-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="rice, chicken, tomato, onion..."
                value={customItems}
                onChange={(e) => setCustomItems(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchCustomBasket()}
                className="pl-10 bg-slate-800 border-slate-700 text-white placeholder:text-gray-500"
              />
            </div>
            <Button
              onClick={fetchCustomBasket}
              disabled={customLoading || !customItems.trim()}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-6"
            >
              {customLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Find Cheapest'}
            </Button>
          </div>

          {/* Custom basket result */}
          {customBasket && (
            <div className="mt-6 bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold">Your Basket</h3>
                <div className="flex items-center space-x-4">
                  <p className="text-2xl font-bold text-emerald-400">₱{customBasket.total_cost}</p>
                  <button onClick={() => setCustomBasket(null)} className="p-1 hover:bg-slate-700 rounded">
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
              <div className="space-y-2">
                {customBasket.basket.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                    <div className="flex items-center space-x-2">
                      <span>{item.icon || '📦'}</span>
                      <span className="text-sm text-white">{item.name}</span>
                    </div>
                    <span className="text-sm text-white font-medium">₱{item.currentPrice}/{item.unit}</span>
                  </div>
                ))}
              </div>
              {customBasket.not_found && customBasket.not_found.length > 0 && (
                <p className="text-xs text-amber-400 mt-3">
                  Not found in market data: {customBasket.not_found.join(', ')}
                </p>
              )}
            </div>
          )}
        </Card>

        {/* Template Baskets */}
        <h2 className="text-xl font-bold text-white mb-4">Preset Baskets</h2>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
            <span className="ml-3 text-gray-400">Loading basket templates...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {templates.map((template) => (
              <BasketCard key={template.id} template={template} />
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-slate-800 text-center">
          <p className="text-sm text-gray-500">
            Prices from DA Bantay Presyo (NCR). Shows cheapest match per item from tracked commodities.
          </p>
        </div>
      </div>
    </div>
  );
};

export default GroceryBasket;
