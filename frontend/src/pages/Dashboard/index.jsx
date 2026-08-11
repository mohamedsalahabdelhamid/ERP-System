import { useState, useEffect, useCallback } from 'react';
import { getSalesInvoices, getPurchaseInvoices, getStock, getIncomeStatement, getProjects, getItems } from '../../api/client';

function KPICard({ title, value, trend, trendDir, icon }) {
  return (
    <div className="glass-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="kpi-title">{title}</div>
          <div className="kpi-value" style={{ marginTop: '0.5rem' }}>{value}</div>
          {trend && <div className={`kpi-trend ${trendDir === 'up' ? 'trend-up' : 'trend-down'}`}>{trendDir === 'up' ? '↑' : '↓'} {trend}</div>}
        </div>
        <div style={{ fontSize: '2rem', opacity: 0.7 }}>{icon}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [salesInvoices, setSalesInvoices] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [stockItems, setStockItems] = useState([]);
  const [incomeStatement, setIncomeStatement] = useState(null);
  const [projects, setProjects] = useState([]);
  const [items, setItems] = useState({});
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState([]);
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setErrors([]);
    const errs = [];
    const safe = async (fn, setter, label) => {
      try {
        const res = await fn();
        setter(res.data);
        return true;
      } catch {
        errs.push(label);
        return false;
      }
    };
    await Promise.all([
      safe(getSalesInvoices, setSalesInvoices, 'sales'),
      safe(getPurchaseInvoices, setPurchases, 'purchases'),
      safe(getStock, setStockItems, 'inventory'),
      safe(getIncomeStatement, (d) => setIncomeStatement(d.data), 'accounting'),
      safe(getProjects, setProjects, 'projects'),
    ]);
    try {
      const res = await getItems();
      const itemMap = {};
      (res.data || []).forEach(item => { itemMap[item.id] = item.name; });
      setItems(itemMap);
    } catch { errs.push('items'); }
    setErrors(errs);
    setLoading(false);
    setLastRefresh(new Date());
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const totalRevenue = incomeStatement ? parseFloat(incomeStatement.revenue || 0) : 0;
  const netProfit = incomeStatement ? parseFloat(incomeStatement.net_income || 0) : 0;
  const totalStockValue = stockItems.reduce((s, item) => s + (parseFloat(item.quantity || 0) * parseFloat(item.average_cost || 0)), 0);
  const confirmedSales = salesInvoices.filter(i => i.is_confirmed).length;
  const pendingSales = salesInvoices.filter(i => !i.is_confirmed).length;
  const activeProjects = projects.filter(p => p.status === 'active').length;

  const fmt = (n) => {
    if (Math.abs(n) >= 1000000) return `$${(n/1000000).toFixed(1)}M`;
    if (Math.abs(n) >= 1000) return `$${(n/1000).toFixed(1)}K`;
    return `$${n.toFixed(2)}`;
  };

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        {lastRefresh && (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Last updated: {lastRefresh.toLocaleTimeString()}
          </div>
        )}
        <button className="btn" style={{ background: 'rgba(255,255,255,0.08)', padding: '0.4rem 1rem', fontSize: '0.85rem', marginLeft: 'auto' }} onClick={fetchAll} disabled={loading}>
          {loading ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>

      {errors.length > 0 && (
        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', padding: '0.75rem 1rem', marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--danger)' }}>
          Couldn't load: {errors.join(', ')}
        </div>
      )}

      {loading && <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>Loading dashboard...</div>}

      {!loading && (
        <>
          {/* KPI Grid */}
          <div className="dashboard-grid">
            <KPICard title="Total Revenue" value={fmt(totalRevenue)} trend={`${confirmedSales} confirmed · ${pendingSales} draft`} trendDir="up" icon="💰" />
            <KPICard title="Net Profit" value={fmt(netProfit)} trend={netProfit >= 0 ? 'Profitable' : 'Loss'} trendDir={netProfit >= 0 ? 'up' : 'down'} icon="📈" />
            <KPICard title="Inventory Value" value={fmt(totalStockValue)} trend={`${stockItems.length} items tracked`} trendDir="up" icon="🏪" />
            <KPICard title="Active Projects" value={activeProjects} trend={`${projects.length} total`} trendDir="up" icon="📐" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            {/* Recent Sales */}
            <div>
              <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Recent Sales</h3>
              <div className="table-container">
                <table>
                  <thead><tr><th>Invoice</th><th>Amount</th><th>Status</th></tr></thead>
                  <tbody>
                    {salesInvoices.length === 0
                      ? <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '1.5rem' }}>No sales yet</td></tr>
                      : salesInvoices.slice(0, 6).map(inv => (
                        <tr key={inv.id}>
                          <td style={{ fontWeight: 500 }}>{inv.number}</td>
                          <td>{parseFloat(inv.total_amount || 0).toFixed(2)} {inv.currency_code || 'USD'}</td>
                          <td><span className={`status-badge ${inv.is_confirmed ? 'status-completed' : 'status-pending'}`}>{inv.is_confirmed ? 'Confirmed' : 'Draft'}</span></td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recent Purchases */}
            <div>
              <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Recent Purchases</h3>
              <div className="table-container">
                <table>
                  <thead><tr><th>Invoice</th><th>Amount</th><th>Status</th></tr></thead>
                  <tbody>
                    {purchases.length === 0
                      ? <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '1.5rem' }}>No purchases yet</td></tr>
                      : purchases.slice(0, 6).map(inv => (
                        <tr key={inv.id}>
                          <td style={{ fontWeight: 500 }}>{inv.number}</td>
                          <td>{parseFloat(inv.total_amount || 0).toFixed(2)} {inv.currency_code || 'USD'}</td>
                          <td><span className={`status-badge ${inv.is_confirmed ? 'status-completed' : 'status-pending'}`}>{inv.is_confirmed ? 'Received' : 'Draft'}</span></td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Stock Overview */}
          {stockItems.length > 0 && (
            <>
              <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Inventory Snapshot</h3>
              <div className="table-container">
                <table>
                  <thead><tr><th>Item</th><th>Qty</th><th>Avg Cost</th><th>Total Value</th></tr></thead>
                  <tbody>
                    {stockItems.slice(0, 8).map(s => (
                      <tr key={s.id}>
                        <td style={{ fontWeight: 500 }}>{items[s.item_id] || `Item #${s.item_id}`}</td>
                        <td style={{ color: parseFloat(s.quantity) > 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>{parseFloat(s.quantity || 0).toFixed(2)}</td>
                        <td>${parseFloat(s.average_cost || 0).toFixed(4)}</td>
                        <td style={{ fontWeight: 600 }}>${(parseFloat(s.quantity || 0) * parseFloat(s.average_cost || 0)).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </>
  );
}
