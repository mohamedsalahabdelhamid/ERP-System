import { useState, useEffect } from 'react';
import { getStock, getMovements, getWarehouses, createWarehouse, updateWarehouse, deleteWarehouse, getItems } from '../../api/client';

export default function Inventory() {
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
    if (!window.confirm('Delete this warehouse?')) return;
    try { await deleteWarehouse(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const movementTypeLabel = {
    purchase_in: '📦 Purchase In',
    sale_out: '🛒 Sale Out',
    manufacturing_in: '🏭 Mfg In',
    manufacturing_out: '🏭 Mfg Out',
    transfer: '🔄 Transfer',
  };

  return (
    <div>
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'stock' ? 'active' : ''}`} onClick={() => setTab('stock')}>Stock Balance</button>
        <button className={`tab-btn ${tab === 'movements' ? 'active' : ''}`} onClick={() => setTab('movements')}>Stock Movements</button>
        <button className={`tab-btn ${tab === 'warehouses' ? 'active' : ''}`} onClick={() => setTab('warehouses')}>Warehouses</button>
      </div>

      {tab === 'stock' && (
        <div className="table-container">
          <table>
            <thead><tr><th>Item</th><th>Warehouse</th><th>Qty in Stock</th><th>Avg Cost</th><th>Total Value</th></tr></thead>
            <tbody>
              {stock.length === 0
                ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No stock data</td></tr>
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
            <thead><tr><th>Type</th><th>Item</th><th>Warehouse</th><th>Qty</th><th>Unit Cost</th><th>Total</th><th>Document</th></tr></thead>
            <tbody>
              {movements.length === 0
                ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No movements</td></tr>
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
            <button className="btn btn-primary" onClick={() => { setEditingId(null); resetForm(); setShowForm(!showForm); }}>+ Add Warehouse</button>
          </div>
          {showForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{editingId ? 'Edit Warehouse' : 'New Warehouse'}</h3>
              <form onSubmit={handleSaveWarehouse}>
                <div className="form-grid">
                  <div className="form-group"><label>Name</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                  <div className="form-group"><label>Code</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : 'Save Warehouse'}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => { setShowForm(false); setEditingId(null); }}>Cancel</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>Code</th><th>Name</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {warehouses.length === 0
                  ? <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No warehouses yet</td></tr>
                  : warehouses.map(w => (
                    <tr key={w.id}>
                      <td>{w.code}</td>
                      <td>{w.name}</td>
                      <td><span className={`status-badge ${w.is_active ? 'status-completed' : 'status-pending'}`}>{w.is_active ? 'Active' : 'Inactive'}</span></td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button className="btn" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => startEdit(w)}>Edit</button>
                          <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteWarehouse(w.id)}>Delete</button>
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
