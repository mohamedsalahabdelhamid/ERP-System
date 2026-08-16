import { useState, useEffect } from 'react';
import { getSalesSummary, getStockValue, getLowStock, getProjectCosts } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Reports() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('sales');
  const [sales, setSales] = useState(null);
  const [stockValue, setStockValue] = useState(null);
  const [lowStock, setLowStock] = useState([]);
  const [projectCosts, setProjectCosts] = useState([]);
  const [projectCostTotal, setProjectCostTotal] = useState(0);
  const [threshold, setThreshold] = useState(10);

  useEffect(() => {
    (async () => {
      try {
        const [s, v] = await Promise.all([getSalesSummary(), getStockValue()]);
        setSales(s.data);
        setStockValue(v.data);
      } catch { /* ignore */ }
    })();
  }, []);

  const loadLowStock = async () => {
    const t = parseFloat(threshold);
    if (Number.isNaN(t) || t < 0) return;
    try { const r = await getLowStock(t); setLowStock(r.data || []); } catch { setLowStock([]); }
  };

  const loadProjectCosts = async () => {
    try {
      const r = await getProjectCosts();
      setProjectCosts(r.data?.projects || []);
      setProjectCostTotal(r.data?.total_cost || 0);
    } catch { setProjectCosts([]); setProjectCostTotal(0); }
  };

  useEffect(() => { if (tab === 'low-stock') loadLowStock(); }, [tab]);
  useEffect(() => { if (tab === 'projects') loadProjectCosts(); }, [tab]);

  const currency = (n) => `${parseFloat(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <div>
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'sales' ? 'active' : ''}`} onClick={() => setTab('sales')}>{t('reports.tab_sales')}</button>
        <button className={`tab-btn ${tab === 'stock' ? 'active' : ''}`} onClick={() => setTab('stock')}>{t('reports.tab_stock')}</button>
        <button className={`tab-btn ${tab === 'low-stock' ? 'active' : ''}`} onClick={() => setTab('low-stock')}>{t('reports.tab_low_stock')}</button>
        <button className={`tab-btn ${tab === 'projects' ? 'active' : ''}`} onClick={() => setTab('projects')}>{t('reports.tab_projects')}</button>
      </div>

      {tab === 'sales' && sales && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
          <div className="glass-card">
            <div className="stat-label">{t('reports.total_invoices')}</div>
            <div className="stat-value">{sales.total_invoices}</div>
          </div>
          <div className="glass-card">
            <div className="stat-label">{t('reports.grand_total')}</div>
            <div className="stat-value">{currency(sales.grand_total)}</div>
          </div>
          {(sales.by_status?.confirmed || sales.by_status?.draft) && (
            <div className="glass-card" style={{ gridColumn: '1 / -1' }}>
              <div className="stat-label">{t('reports.by_status')}</div>
              <div style={{ display: 'flex', gap: '2rem', marginTop: '0.5rem' }}>
                {Object.entries(sales.by_status).map(([k, v]) => (
                  <span key={k} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className="status-badge" style={{ background: 'var(--accent)' }}>{k}</span>
                    <strong>{v.count}</strong>
                    <span style={{ color: 'var(--text-secondary)' }}>{currency(v.total)}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'stock' && stockValue && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="glass-card">
            <div className="stat-label">{t('reports.total_stock_value')}</div>
            <div className="stat-value">{currency(stockValue.total_value)}</div>
          </div>
            <div className="glass-card">
              <div className="stat-label">{t('reports.item_count')}</div>
              <div className="stat-value">{stockValue.item_count}</div>
            </div>
          </div>
          <div className="table-container">
            <table>
              <thead><tr><th>{t('reports.warehouse')}</th><th>{t('reports.value')}</th></tr></thead>
              <tbody>
                {Object.entries(stockValue.by_warehouse || {}).map(([name, val]) => (
                  <tr key={name}><td>{name}</td><td>{currency(val)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'low-stock' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1rem', marginBottom: '1rem' }}>
            <div className="form-group">
              <label>{t('reports.threshold')}</label>
              <input type="number" value={threshold} onChange={e => setThreshold(e.target.value)} style={{ width: '120px' }} />
            </div>
            <button className="btn btn-primary" onClick={loadLowStock}>{t('reports.refresh')}</button>
          </div>
          <div className="table-container">
            <table>
              <thead><tr><th>{t('reports.code')}</th><th>{t('reports.item')}</th><th>{t('reports.on_hand')}</th></tr></thead>
              <tbody>
                {lowStock.length === 0
                  ? <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('reports.all_above')}</td></tr>
                  : lowStock.map(s => (
                    <tr key={s.item_id}>
                      <td>{s.code}</td>
                      <td>{s.name}</td>
                      <td style={{ color: 'var(--danger)', fontWeight: 600 }}>{parseFloat(s.quantity || 0).toFixed(2)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'projects' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="glass-card">
            <div className="stat-label">{t('reports.total_project_cost')}</div>
            <div className="stat-value">{currency(projectCostTotal)}</div>
          </div>
            <div className="glass-card">
              <div className="stat-label">{t('reports.projects')}</div>
              <div className="stat-value">{projectCosts.length}</div>
            </div>
          </div>
          <div className="table-container">
            <table>
              <thead><tr><th>{t('reports.project')}</th><th>{t('reports.status')}</th><th>{t('reports.total_cost')}</th></tr></thead>
              <tbody>
                {projectCosts.length === 0
                  ? <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('reports.no_projects')}</td></tr>
                  : projectCosts.map((p, i) => (
                    <tr key={i}>
                      <td>{p.name}</td>
                      <td><span className={`status-badge ${p.status === 'completed' ? 'status-completed' : 'status-pending'}`}>{p.status}</span></td>
                      <td>{currency(p.cost)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
