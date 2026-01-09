
import React, { useState, useMemo } from 'react';
import { Search, ShoppingCart, Plus, Minus, Trash2, CreditCard, Calculator, X, Store, ScanLine } from 'lucide-react';
import { MOCK_PRODUCTS } from '../constants';
import { Product } from '../types';

interface CartItem extends Product {
  qty: number;
}

export const PosView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [cart, setCart] = useState<CartItem[]>([]);
  const [activeCategory, setActiveCategory] = useState('All');

  const categories = ['All', 'Electronics', 'Computers', 'Mobile', 'Audio', 'Electrical'];

  // Filter products
  const filteredProducts = useMemo(() => {
    return MOCK_PRODUCTS.filter(p => {
      const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (p.id && p.id.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesCategory = activeCategory === 'All' || p.category.includes(activeCategory);
      return matchesSearch && matchesCategory;
    });
  }, [searchTerm, activeCategory]);

  // Cart Calculations
  const subtotal = cart.reduce((sum, item) => sum + (item.b2cPrice * item.qty), 0);
  const tax = subtotal * 0.18; // Assuming 18% GST
  const total = subtotal + tax;

  const addToCart = (product: Product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item =>
          item.id === product.id ? { ...item, qty: item.qty + 1 } : item
        );
      }
      return [...prev, { ...product, qty: 1 }];
    });
  };

  const removeFromCart = (id: string) => {
    setCart(prev => prev.filter(item => item.id !== id));
  };

  const updateQty = (id: string, delta: number) => {
    setCart(prev => prev.map(item => {
      if (item.id === id) {
        const newQty = Math.max(1, item.qty + delta);
        return { ...item, qty: newQty };
      }
      return item;
    }));
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] -m-4 sm:-m-6 lg:-m-8 overflow-hidden font-sans">
      {/* LEFT SIDE: Product Catalog */}
      <div className="flex-1 flex flex-col bg-gray-50 border-r border-gray-200 min-w-0">
        {/* Search & Filter Header */}
        <div className="p-4 bg-white border-b border-gray-200 space-y-4 shrink-0">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Search products by name or SKU..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none shadow-sm text-gray-900"
              />
            </div>
            <button className="p-2.5 bg-gray-100 text-gray-600 rounded-lg border border-gray-200 hover:bg-gray-200">
              <ScanLine size={20} />
            </button>
          </div>

          <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-4 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-colors ${activeCategory === cat
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                  }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Product Grid */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredProducts.map(product => (
              <div
                key={product.id}
                onClick={() => addToCart(product)}
                className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer overflow-hidden group flex flex-col h-full"
              >
                <div className="aspect-[4/3] bg-gray-100 relative">
                  <img src={product.image} alt={product.name} className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                  {product.stock < 10 && (
                    <span className="absolute top-2 right-2 bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                      Only {product.stock} left
                    </span>
                  )}
                </div>
                <div className="p-3 flex flex-col flex-1">
                  <h3 className="font-medium text-gray-900 text-sm line-clamp-2 leading-tight mb-1">{product.name}</h3>
                  <p className="text-xs text-gray-500 mb-2">{product.brand}</p>
                  <div className="mt-auto flex justify-between items-center">
                    <span className="font-bold text-indigo-600">₹{product.b2cPrice.toLocaleString()}</span>
                    <button className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-600 hover:text-white transition-colors">
                      <Plus size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {filteredProducts.length === 0 && (
              <div className="col-span-full flex flex-col items-center justify-center h-64 text-gray-400">
                <Search size={48} className="mb-4 opacity-20" />
                <p>No products found</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT SIDE: Cart & Checkout */}
      <div className="w-[400px] bg-white flex flex-col shadow-2xl z-10 shrink-0">
        {/* Cart Header */}
        <div className="h-16 px-6 border-b border-gray-100 flex items-center justify-between shrink-0 bg-gray-50/50">
          <div className="flex items-center gap-2 text-gray-900">
            <ShoppingCart className="text-indigo-600" size={20} />
            <span className="font-bold text-lg">Current Order</span>
          </div>
          <span className="bg-indigo-100 text-indigo-800 text-xs font-bold px-2.5 py-1 rounded-full">
            {cart.length} Items
          </span>
        </div>

        {/* Cart Items */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {cart.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
              <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center">
                <ShoppingCart size={32} className="opacity-20" />
              </div>
              <p className="text-sm">Cart is empty. Select products to begin.</p>
            </div>
          ) : (
            cart.map(item => (
              <div key={item.id} className="flex gap-3 bg-white border border-gray-100 rounded-lg p-2 shadow-sm group hover:border-gray-200 transition-colors">
                <img src={item.image} alt="" className="w-16 h-16 rounded-md object-cover bg-gray-50 border border-gray-100" />
                <div className="flex-1 flex flex-col justify-between">
                  <h4 className="text-sm font-semibold text-gray-900 line-clamp-1" title={item.name}>{item.name}</h4>
                  <div className="flex items-center justify-between mt-1">
                    <div className="text-sm font-bold text-indigo-600">₹{(item.b2cPrice * item.qty).toLocaleString()}</div>
                    <div className="flex items-center bg-gray-50 rounded-lg border border-gray-200 h-7">
                      <button
                        onClick={() => updateQty(item.id, -1)}
                        className="w-7 h-full flex items-center justify-center text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-l-lg transition-colors"
                      >
                        <Minus size={12} />
                      </button>
                      <span className="w-8 text-center text-xs font-bold text-gray-900">{item.qty}</span>
                      <button
                        onClick={() => updateQty(item.id, 1)}
                        className="w-7 h-full flex items-center justify-center text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-r-lg transition-colors"
                      >
                        <Plus size={12} />
                      </button>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => removeFromCart(item.id)}
                  className="text-gray-300 hover:text-red-500 p-1 self-start -mr-1"
                >
                  <X size={16} />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Bill Summary Section */}
        <div className="bg-gray-50 border-t border-gray-200 p-6 space-y-3 shrink-0">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Subtotal</span>
            <span className="font-medium">₹{subtotal.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            <span>Tax (18% GST)</span>
            <span className="font-medium">₹{tax.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-600 border-b border-gray-200 pb-3">
            <span>Discount</span>
            <span className="font-medium text-green-600">- ₹0.00</span>
          </div>
          <div className="flex justify-between items-end pt-1">
            <span className="text-gray-900 font-bold text-lg">Total</span>
            <span className="text-2xl font-bold text-indigo-600">₹{total.toLocaleString()}</span>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-4">
            <button className="flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 bg-white text-gray-700 font-bold rounded-xl hover:bg-gray-50 transition-colors shadow-sm">
              <Calculator size={18} /> Hold
            </button>
            <button
              className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800 shadow-lg transition-all disabled:opacity-50 disabled:shadow-none"
              disabled={cart.length === 0}
            >
              <CreditCard size={18} /> Pay Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
