import { useState, useEffect } from 'react';
import { getStockTakes, createStockTake, postStockTake, getWarehouses, getItems, getStock } from '../../api/client';

export default function StockTakes() {
  const [stockTakes, setStockTakes] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [items, setItems] = useState([]);
  const [stock, setStock] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [warehouseId, setWarehouseId] = useState('');
  const [reference, setReference] = useState('');
  const [note, setNote] = useState('');
  const [lines, setLines] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [st, w, i] = await Promise.all([getStockTakes(), getWarehouses(), getItems()]);
      setStockTakes(st.data || []);
      setWarehouses(w.data || []);
      setItems(i.data || []);
    } catch {
      setStockTakes([]); setWarehouses([]); setItems([]);
    }
  };

  const loadStockForWarehouse = async (wid) => {
    if (!wid) { setStock([]); return; }
    try {
      const s = await getStock(wid);
      setStock(s.data || []);
    } catch { setStock([]); }
  };

  const addLine = () => setLines([...lines, { item_id: '', counted_qty: 1 }]);

  const updateLine = (idx, field, value) => {
    const next = lines.map((l, i) => (i === idx ? { ...l, [field]: value } : l));
    setLines(next);
  };

  const removeLine = (idx) => setLines(lines.filter((_, i) => i !== idx));

  const bookQty = (itemId) => {
    const row = stock.find(s => s.item_id === Number(itemId));
    return row ? parseFloat(row.quantity || 0) : 0;
  };

  const whName = (id) => (warehouses.find(w => w.id === id) || {}).name || `#${id}`;

  const handleCreate = async (e) => {
    e.preventDefault();
    const validLines = lines.filter(l => l.item_id);
    if (!warehouseId || validLines.length === 0) { alert('Select a warehouse and at least one item'); return; }
    setLoading(true);
    try {
      await createStockTake({
        warehouse_id: Number(warehouseId),
        reference: reference || `ST-${Date.now()}`,
        note: note || null,
        lines: validLines.map(l => ({ item_id: Number(l.item_id), counted_qty: parseFloat(l.counted_qty) || 0 })),
      });
      setShowForm(false); setLines([]); setReference(''); setNote('');
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const handlePost = async (id) => {
    try { await postStockTake(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const statusBadge = (status) => (
    <span className={`status-badge ${status === 'posted' ? 'status-completed' : 'status-pending'}`}>{status}</span>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>+ New Stock Take</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>Warehouse</label>
                <select value={warehouseId} onChange={e => { setWarehouseId(e.target.value); loadStockForWarehouse(e.target.value); }} required>
                  <option value="">Select warehouse</option>
                  {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>Reference</label><input value={reference} onChange={e => setReference(e.target.value)} placeholder="Auto-generated if empty" /></div>
              <div className="form-group"><label>Note</label><input value={note} onChange={e => setNote(e.target.value)} /></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '1rem 0' }}>
              <strong>Counted Lines</strong>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={addLine}>+ Add Item</button>
            </div>

            <div className="table-container" style={{ marginBottom: '1rem' }}>
              <table>
                <thead><tr><th>Item</th><th>Book Qty</th><th>Counted Qty</th><th></th></tr></thead>
                <tbody>
                  {lines.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '1.5rem' }}>Add items to count</td></tr>}
                  {lines.map((l, idx) => (
                    <tr key={idx}>
                      <td>
                        <select value={l.item_id} onChange={e => updateLine(idx, 'item_id', e.target.value)} required>
                          <option value="">Select item</option>
                          {items.map(it => <option key={it.id} value={it.id}>{it.code} — {it.name}</option>)}
                        </select>
                      </td>
                      <td>{l.item_id ? bookQty(l.item_id).toFixed(2) : '—'}</td>
                      <td><input type="number" step="0.01" value={l.counted_qty} onChange={e => updateLine(idx, 'counted_qty', e.target.value)} style={{ width: '110px' }} /></td>
                      <td><button type="button" className="btn" style={{ background: 'rgba(255,0,0,0.15)' }} onClick={() => removeLine(idx)}>✕</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : 'Create Stock Take'}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>Reference</th><th>Warehouse</th><th>Status</th><th>Posted At</th><th>Actions</th></tr></thead>
          <tbody>
            {stockTakes.length === 0
              ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No stock takes yet</td></tr>
              : stockTakes.map(st => (
                <tr key={st.id}>
                  <td style={{ fontWeight: 600 }}>{st.reference}</td>
                  <td>{whName(st.warehouse_id)}</td>
                  <td>{statusBadge(st.status)}</td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{st.posted_at || '—'}</td>
                  <td>
                    {st.status === 'draft' && (
                      <button className="btn btn-primary" onClick={() => handlePost(st.id)}>Post</button>
                    )}
                    {st.status === 'posted' && <span style={{ color: 'var(--success)' }}>✓ Posted</span>}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
