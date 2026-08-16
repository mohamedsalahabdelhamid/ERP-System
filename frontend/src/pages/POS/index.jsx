import { useState, useEffect, useRef } from 'react';
import { getItems, getStock, getPartners, getCategories, getPosSessions, openPosSession, closePosSession, createPosOrder, getPosOrders } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';
import './POS.css';

export default function POS() {
  const { t } = useTranslation();
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
    } catch (err) { alert(err.response?.data?.detail || t('pos.open_session_fail')); }
  };

  const handleCloseSession = async () => {
    const amount = parseFloat(closingCash);
    if (isNaN(amount) || amount < 0) { alert(t('pos.valid_closing')); return; }
    if (!window.confirm(t('pos.confirm_close'))) return;
    setClosing(true);
    try {
      await closePosSession(openSession.id, { closing_cash: amount });
      setOpenSession(null);
      setClosingCash('');
      alert(t('pos.session_closed'));
    } catch (err) { alert(err.response?.data?.detail || t('pos.close_session_fail')); }
    finally { setClosing(false); }
  };

  const handleShowHistory = async () => {
    setShowHistory(!showHistory);
    if (!showHistory) {
      setHistoryLoading(true);
      try { const res = await getPosOrders(); setOrders(res.data || []); }
      catch (err) { alert(err.response?.data?.detail || t('pos.load_orders_fail')); }
      finally { setHistoryLoading(false); }
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [itemsRes, stockRes, partnersRes, catsRes] = await Promise.all([getItems(), getStock(), getPartners(), getCategories()]);
      const stockMap = {};
      (stockRes.data || []).forEach(s => { stockMap[s.item_id] = (stockMap[s.item_id] || 0) + parseFloat(s.quantity || 0); });
      const catMap = {};
      (catsRes.data || []).forEach(c => { catMap[c.id] = c.name; });
      const enriched = (itemsRes.data || []).map(item => ({
        ...item,
        stock: stockMap[item.id] || 0,
        price: parseFloat(item.default_sale_price || 0),
        category: catMap[item.item_category_id] || t('pos.general'),
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
      alert(err.response?.data?.detail || t('pos.sale_fail'));
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
            {openSession ? `● ${t('pos.session_open')}` : `● ${t('pos.no_open_session')}`}
          </span>
          {openSession && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              #{openSession.id} • {t('pos.expected')}: EGP {parseFloat(openSession.expected_cash || 0).toFixed(2)} • {t('pos.variance')}: EGP {parseFloat(openSession.variance || 0).toFixed(2)}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginLeft: 'auto', alignItems: 'center' }}>
          <button className="btn" style={{ background: 'rgba(255,255,255,0.08)', padding: '0.4rem 1rem', fontSize: '0.85rem' }} onClick={handleShowHistory}>
            {showHistory ? t('pos.hide_orders') : `📋 ${t('pos.order_history')}`}
          </button>
          {openSession ? (
            <>
              <input type="number" min="0" step="0.01" placeholder={t('pos.closing_cash')} value={closingCash} onChange={e => setClosingCash(e.target.value)} style={{ width: '130px', fontSize: '0.85rem' }} />
              <button className="btn" style={{ background: 'rgba(239,68,68,0.2)', color: 'var(--danger)', padding: '0.4rem 1rem', fontSize: '0.85rem' }} onClick={handleCloseSession} disabled={closing}>
                {closing ? t('pos.closing_cash') : t('pos.close_session')}
              </button>
            </>
          ) : (
            <button className="btn btn-primary" style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }} onClick={handleOpenSession}>{t('pos.open_session')}</button>
          )}
        </div>
      </div>

      {showHistory && (
        <div className="glass-card" style={{ marginBottom: '1rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>{t('pos.recent_orders')}</h3>
          {historyLoading ? (
            <div style={{ padding: '1rem', color: 'var(--text-secondary)' }}>{t('common.loading')}</div>
          ) : (
            <div className="table-container">
              <table>
                <thead><tr><th>{t('pos.order_no')}</th><th>{t('pos.session')}</th><th>{t('pos.total')}</th><th>{t('pos.status')}</th></tr></thead>
                <tbody>
                  {orders.length === 0
                    ? <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '1.5rem' }}>{t('pos.no_orders')}</td></tr>
                    : orders.map(o => (
                      <tr key={o.id}>
                        <td>{o.order_number}</td>
                        <td>POS-{o.session_id}</td>
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
            placeholder={`🔍  ${t('pos.search_placeholder')}`}
            className="pos-search-input"
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
        {loading ? (
          <div className="pos-loading">{t('pos.loading_products')}</div>
        ) : (
          <div className="pos-grid">
            {filtered.length === 0 ? (
              <div style={{ gridColumn: '1/-1', textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                {t('pos.no_products')}
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
                  {p.stock <= 0 ? `❌ ${t('pos.out_of_stock')}` : p.stock <= 5 ? `⚠️ ${t('pos.low_stock')}: ${p.stock.toFixed(0)}` : `✅ ${p.stock.toFixed(0)} ${t('pos.in_stock')}`}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Cart Panel */}
      <div className="pos-cart-area glass-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 className="pos-cart-title">{t('pos.order')}</h2>
          {cart.length > 0 && (
            <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => setCart([])}>
              {t('pos.clear_all')}
            </button>
          )}
        </div>

        {/* Customer Select */}
        <div className="form-group" style={{ marginBottom: '1rem' }}>
          <label style={{ fontSize: '0.75rem' }}>{t('pos.customer')}</label>
          <select value={selectedPartner} onChange={e => setSelectedPartner(e.target.value)} style={{ fontSize: '0.85rem' }}>
            <option value="">-- {t('pos.walk_in_customer')} --</option>
            {partners.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>

        <div className="pos-cart-items">
          {cart.length === 0 ? (
            <div className="empty-cart">
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🛒</div>
              <p>{t('pos.cart_empty')}</p>
              <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>{t('pos.cart_hint')}</p>
            </div>
          ) : (
            cart.map(item => (
              <div key={item.id} className="pos-cart-item">
                <div className="item-info">
                  <div className="item-name">{item.name}</div>
                  <div className="item-price">EGP {item.price.toFixed(2)} {t('pos.each')}</div>
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
          <div className="summary-row"><span>{t('pos.subtotal')}</span><span>EGP {subtotal.toFixed(2)}</span></div>
          <div className="summary-row total-row"><span>{t('pos.total')}</span><span>EGP {total.toFixed(2)}</span></div>

          {lastSale && (
            <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '8px', padding: '0.75rem', fontSize: '0.8rem', color: 'var(--success)' }}>
              ✅ {t('pos.order_completed', { num: lastSale.orderNumber })} — EGP {lastSale.total.toFixed(2)}
            </div>
          )}

          <button
            className="btn btn-primary pos-pay-btn"
            disabled={cart.length === 0 || paying}
            onClick={handlePay}
          >
            {paying ? `⏳ ${t('pos.processing')}` : `💳 ${t('pos.pay')} EGP ${total.toFixed(2)}`}
          </button>
        </div>
      </div>
    </div>
  );
}
