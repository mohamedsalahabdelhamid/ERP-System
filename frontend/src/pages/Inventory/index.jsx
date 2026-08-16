import { useState, useEffect } from 'react';
import { getStock, getMovements, getWarehouses, createWarehouse, updateWarehouse, deleteWarehouse, getItems } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Inventory() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('stock');
  const [stock, setStock] = useState([]);
  const [movements, setMovements] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [items, setItems] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ name: '', code: '', is_active: true });
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [s, m, w, i] = await Promise.all([getStock(), getMovements(), getWarehouses(), getItems()]);
      setStock(s.data || []);
      setMovements(m.data || []);
      setWarehouses(w.data || []);
      setItems(i.data || []);
    } catch { setStock([]); setMovements([]); setWarehouses([]); setItems([]); }
  };

  const itemName = (id) => (items.find(x => x.id === id) || {}).name || `#${id}`;
  const whName = (id) => (warehouses.find(x => x.id === id) || {}).name || `#${id}`;

  const resetForm = () => setForm({ name: '', code: '', is_active: true });

  const handleSaveWarehouse = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editingId) await updateWarehouse(editingId, form);
      else await createWarehouse(form);
      setShowForm(false);
      setEditingId(null);
      resetForm();
      fetchAll();
    }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const startEdit = (w) => {
    setEditingId(w.id);
    setForm({ name: w.name, code: w.code, is_active: w.is_active });
    setShowForm(true);
  };

  const handleDeleteWarehouse = async (id) => {
    if (!window.confirm(t('inventory.delete_confirm'))) return;
    try { await deleteWarehouse(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const movementTypeLabel = {
    purchase_in: `📦 ${t('inventory.m_purchase_in')}`,
    sale_out: `🛒 ${t('inventory.m_sale_out')}`,
    manufacturing_in: `🏭 ${t('inventory.m_manufacturing_in')}`,
    manufacturing_out: `🏭 ${t('inventory.m_manufacturing_out')}`,
    transfer: `🔄 ${t('inventory.m_transfer')}`,
  };

  return (
    <div>
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'stock' ? 'active' : ''}`} onClick={() => setTab('stock')}>{t('inventory.tab_stock')}</button>
        <button className={`tab-btn ${tab === 'movements' ? 'active' : ''}`} onClick={() => setTab('movements')}>{t('inventory.tab_movements')}</button>
        <button className={`tab-btn ${tab === 'warehouses' ? 'active' : ''}`} onClick={() => setTab('warehouses')}>{t('inventory.tab_warehouses')}</button>
      </div>

      {tab === 'stock' && (
        <div className="table-container">
          <table>
            <thead><tr><th>{t('inventory.item')}</th><th>{t('inventory.warehouse')}</th><th>{t('inventory.qty_in_stock')}</th><th>{t('inventory.avg_cost')}</th><th>{t('inventory.total_value')}</th></tr></thead>
            <tbody>
              {stock.length === 0
                ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('inventory.no_stock')}</td></tr>
                : stock.map(s => (
                  <tr key={s.id}>
                    <td>{itemName(s.item_id)}</td>
                    <td>{whName(s.warehouse_id)}</td>
                    <td style={{ fontWeight: 600, color: parseFloat(s.quantity) > 0 ? 'var(--success)' : 'var(--danger)' }}>{parseFloat(s.quantity || 0).toFixed(2)}</td>
                    <td>${parseFloat(s.average_cost || 0).toFixed(4)}</td>
                    <td>${(parseFloat(s.quantity || 0) * parseFloat(s.average_cost || 0)).toFixed(2)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'movements' && (
        <div className="table-container">
          <table>
            <thead><tr><th>{t('inventory.type')}</th><th>{t('inventory.item')}</th><th>{t('inventory.warehouse')}</th><th>{t('inventory.qty')}</th><th>{t('inventory.unit_cost')}</th><th>{t('inventory.total')}</th><th>{t('inventory.document')}</th></tr></thead>
            <tbody>
              {movements.length === 0
                ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('inventory.no_movements')}</td></tr>
                : movements.map(m => (
                  <tr key={m.id}>
                    <td>{movementTypeLabel[m.movement_type] || m.movement_type}</td>
                    <td>{itemName(m.item_id)}</td>
                    <td>{m.warehouse_id ? whName(m.warehouse_id) : '-'}</td>
                    <td>{parseFloat(m.quantity || 0).toFixed(2)}</td>
                    <td>${parseFloat(m.unit_cost || 0).toFixed(4)}</td>
                    <td>${parseFloat(m.total_cost || 0).toFixed(2)}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{m.document_type} #{m.document_id}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'warehouses' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => { setEditingId(null); resetForm(); setShowForm(!showForm); }}>+ {t('inventory.add_warehouse')}</button>
          </div>
          {showForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{editingId ? t('inventory.edit_warehouse') : t('inventory.new_warehouse')}</h3>
              <form onSubmit={handleSaveWarehouse}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('inventory.name')}</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('inventory.code')}</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('inventory.save_warehouse')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => { setShowForm(false); setEditingId(null); }}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>{t('inventory.code')}</th><th>{t('inventory.name')}</th><th>{t('inventory.status')}</th><th></th></tr></thead>
              <tbody>
                {warehouses.length === 0
                  ? <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('inventory.no_warehouses')}</td></tr>
                  : warehouses.map(w => (
                    <tr key={w.id}>
                      <td>{w.code}</td>
                      <td>{w.name}</td>
                      <td><span className={`status-badge ${w.is_active ? 'status-completed' : 'status-pending'}`}>{w.is_active ? t('inventory.active') : t('inventory.inactive')}</span></td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button className="btn" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => startEdit(w)}>{t('inventory.edit')}</button>
                          <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteWarehouse(w.id)}>{t('inventory.delete')}</button>
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
