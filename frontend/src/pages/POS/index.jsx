import { useState, useEffect, useRef } from 'react';
import { getItems, getStock, getPartners, getCategories, getPosSessions, openPosSession, closePosSession, createPosOrder, getPosOrders } from '../../api/client';
import './POS.css';

export default function POS() {
  const [cart, setCart] = useState([]);
  const [products, setProducts] = useState([]);
  const [stock, setStock] = useState([]);
  const [categories, setCategories] = useState([]);
  const [partners, setPartners] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedPartner, setSelectedPartner] = useState('');
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [lastSale, setLastSale] = useState(null);
  const [openSession, setOpenSession] = useState(null);
  const [closingCash, setClosingCash] = useState('');
  const [closing, setClosing] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [orders, setOrders] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const searchRef = useRef(null);

  useEffect(() => {
    fetchData();
    loadSessions();
    if (searchRef.current) searchRef.current.focus();
  }, []);

  const loadSessions = async () => {
    try {
      const res = await getPosSessions();
      const open = (res.data || []).find(s => s.status === 'open');
      setOpenSession(open || null);
    } catch { setOpenSession(null); }
  };

  const handleOpenSession = async () => {
    try {
      await openPosSession({ opening_cash: 0 });
      await loadSessions();
      await fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Error opening session'); }
  };

  const handleCloseSession = async () => {
    const amount = parseFloat(closingCash);
    if (isNaN(amount) || amount < 0) { alert('Enter a valid closing cash amount'); return; }
    if (!window.confirm('Close this POS session?')) return;
    setClosing(true);
    try {
      await closePosSession(openSession.id, { closing_cash: amount });
      setOpenSession(null);
      setClosingCash('');
      alert('Session closed');
    } catch (err) { alert(err.response?.data?.detail || 'Error closing session'); }
    finally { setClosing(false); }
  };

  const handleShowHistory = async () => {
    setShowHistory(!showHistory);
    if (!showHistory) {
      setHistoryLoading(true);
      try { const res = await getPosOrders(); setOrders(res.data || []); }
      catch (err) { alert(err.response?.data?.detail || 'Error loading orders'); }
      finally { setHistoryLoading(false); }
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [itemsRes, stockRes, partnersRes, catsRes] = await Promise.all([getItems(), getStock(), getPartners(), getCategories()]);
      const stockMap = {};
      (stockRes.data || []).forEach(s => { stockMap[s.item_id] = parseFloat(s.quantity || 0); });
      const catMap = {};
      (catsRes.data || []).forEach(c => { catMap[c.id] = c.name; });
      const enriched = (itemsRes.data || []).map(item => ({
        ...item,
        stock: stockMap[item.id] || 0,
        price: parseFloat(item.default_sale_price || 0),
        category: catMap[item.item_category_id] || 'General',
      }));
      setProducts(enriched);
      setPartners((partnersRes.data || []).filter(p => ['customer', 'both'].includes(p.type)));
    } catch { setProducts([]); }
    setLoading(false);
  };

  const filtered = products.filter(p =>
    p.name?.toLowerCase().includes(search.toLowerCase()) ||
    p.code?.toLowerCase().includes(search.toLowerCase())
  );

  const addToCart = (product) => {
    if (product.stock <= 0) return;
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        if (existing.qty >= product.stock) return prev;
        return prev.map(item => item.id === product.id ? { ...item, qty: item.qty + 1 } : item);
      }
      return [...prev, { ...product, qty: 1 }];
    });
    if (searchRef.current) searchRef.current.focus();
  };

  const updateQty = (id, delta) => setCart(prev =>
    prev.map(item => item.id === id ? { ...item, qty: Math.max(1, Math.min(item.qty + delta, item.stock)) } : item)
  );
  const removeFromCart = (id) => setCart(prev => prev.filter(item => item.id !== id));

  const subtotal = cart.reduce((s, i) => s + (i.price * i.qty), 0);
  const total = subtotal;

  const handlePay = async () => {
    if (cart.length === 0) return;
    setPaying(true);
    try {
      let session = openSession || (await getPosSessions()).data.find(s => s.status === 'open');
      if (!session) {
        session = (await openPosSession({ opening_cash: 0 })).data;
        setOpenSession(session);
      }
      const order = await createPosOrder({
        session_id: session.id,
        partner_id: selectedPartner ? parseInt(selectedPartner) : null,
        lines: cart.map(item => ({
          item_id: item.id,
          quantity: item.qty,
          unit_price: item.price,
        })),
      });
      setLastSale({ orderNumber: order.data.order_number, total, items: cart.length });
      setCart([]);
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error processing sale');
    } finally {
      setPaying(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && filtered.length === 1) addToCart(filtered[0]);
  };

  return (
    <div className="pos-container">
      {/* Session Status Bar */}
      <div className="pos-session-bar glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1.25rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className={`status-badge ${openSession ? 'status-completed' : 'status-pending'}`}>
            {openSession ? '● Session Open' : '● No Open Session'}
          </span>
          {openSession && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              #{openSession.id} • Expected: EGP {parseFloat(openSession.expected_cash || 0).toFixed(2)} • Variance: EGP {parseFloat(openSession.variance || 0).toFixed(2)}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginLeft: 'auto', alignItems: 'center' }}>
          <button className="btn" style={{ background: 'rgba(255,255,255,0.08)', padding: '0.4rem 1rem', fontSize: '0.85rem' }} onClick={handleShowHistory}>
            {showHistory ? 'Hide Orders' : '📋 Order History'}
          </button>
          {openSession ? (
            <>
              <input type="number" min="0" step="0.01" placeholder="Closing cash" value={closingCash} onChange={e => setClosingCash(e.target.value)} style={{ width: '130px', fontSize: '0.85rem' }} />
              <button className="btn" style={{ background: 'rgba(239,68,68,0.2)', color: 'var(--danger)', padding: '0.4rem 1rem', fontSize: '0.85rem' }} onClick={handleCloseSession} disabled={closing}>
                {closing ? 'Closing...' : 'Close Session'}
              </button>
            </>
          ) : (
            <button className="btn btn-primary" style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }} onClick={handleOpenSession}>Open Session</button>
          )}
        </div>
      </div>

      {showHistory && (
        <div className="glass-card" style={{ marginBottom: '1rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>Recent Orders</h3>
          {historyLoading ? (
            <div style={{ padding: '1rem', color: 'var(--text-secondary)' }}>Loading...</div>
          ) : (
            <div className="table-container">
              <table>
                <thead><tr><th>Order No</th><th>Session</th><th>Total</th><th>Status</th></tr></thead>
                <tbody>
                  {orders.length === 0
                    ? <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '1.5rem' }}>No orders yet</td></tr>
                    : orders.map(o => (
                      <tr key={o.id}>
                        <td>{o.order_number}</td>
                        <td>#{o.session_id}</td>
                        <td>EGP {parseFloat(o.total || 0).toFixed(2)}</td>
                        <td><span className={`status-badge ${o.status === 'completed' ? 'status-completed' : 'status-pending'}`}>{o.status}</span></td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Products Panel */}
      <div className="pos-products-area">
        <div className="pos-search">
          <input
            ref={searchRef}
            type="text"
            placeholder="🔍  Search by name or scan barcode..."
            className="pos-search-input"
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
        {loading ? (
          <div className="pos-loading">Loading products...</div>
        ) : (
          <div className="pos-grid">
            {filtered.length === 0 ? (
              <div style={{ gridColumn: '1/-1', textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                No products found
              </div>
            ) : filtered.map(p => (
              <div
                key={p.id}
                className={`pos-product-card glass-card ${p.stock <= 0 ? 'out-of-stock' : ''}`}
                onClick={() => addToCart(p)}
              >
                <div className="pos-product-cat">{p.category}</div>
                <div className="pos-product-name">{p.name}</div>
                <div className="pos-product-price">EGP {p.price.toFixed(2)}</div>
                <div className={`pos-product-stock ${p.stock <= 5 && p.stock > 0 ? 'low-stock' : ''} ${p.stock <= 0 ? 'no-stock' : ''}`}>
                  {p.stock <= 0 ? '❌ Out of Stock' : p.stock <= 5 ? `⚠️ Low: ${p.stock.toFixed(0)}` : `✅ ${p.stock.toFixed(0)} in stock`}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Cart Panel */}
      <div className="pos-cart-area glass-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 className="pos-cart-title">Order</h2>
          {cart.length > 0 && (
            <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => setCart([])}>
              Clear All
            </button>
          )}
        </div>

        {/* Customer Select */}
        <div className="form-group" style={{ marginBottom: '1rem' }}>
          <label style={{ fontSize: '0.75rem' }}>Customer</label>
          <select value={selectedPartner} onChange={e => setSelectedPartner(e.target.value)} style={{ fontSize: '0.85rem' }}>
            <option value="">-- Walk-in Customer --</option>
            {partners.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>

        <div className="pos-cart-items">
          {cart.length === 0 ? (
            <div className="empty-cart">
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🛒</div>
              <p>Cart is empty</p>
              <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Click on a product to add it</p>
            </div>
          ) : (
            cart.map(item => (
              <div key={item.id} className="pos-cart-item">
                <div className="item-info">
                  <div className="item-name">{item.name}</div>
                  <div className="item-price">EGP {item.price.toFixed(2)} each</div>
                </div>
                <div className="item-controls">
                  <button className="qty-btn" onClick={() => updateQty(item.id, -1)}>−</button>
                  <span className="qty-value">{item.qty}</span>
                  <button className="qty-btn" onClick={() => updateQty(item.id, 1)}>+</button>
                  <div className="item-total">EGP {(item.price * item.qty).toFixed(2)}</div>
                  <button className="remove-btn" onClick={() => removeFromCart(item.id)}>×</button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="pos-cart-summary">
          <div className="summary-row"><span>Subtotal</span><span>EGP {subtotal.toFixed(2)}</span></div>
          <div className="summary-row total-row"><span>Total</span><span>EGP {total.toFixed(2)}</span></div>

          {lastSale && (
            <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '8px', padding: '0.75rem', fontSize: '0.8rem', color: 'var(--success)' }}>
              ✅ Order #{lastSale.orderNumber} completed — EGP {lastSale.total.toFixed(2)}
            </div>
          )}

          <button
            className="btn btn-primary pos-pay-btn"
            disabled={cart.length === 0 || paying}
            onClick={handlePay}
          >
            {paying ? '⏳ Processing...' : `💳 Pay EGP ${total.toFixed(2)}`}
          </button>
        </div>
      </div>
    </div>
  );
}
