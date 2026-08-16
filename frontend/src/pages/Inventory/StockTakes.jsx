import { useState, useEffect } from 'react';
import { getStockTakes, getStockTake, createStockTake, postStockTake, getWarehouses, getItems, getStock } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function StockTakes() {
  const { t } = useTranslation();
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
  const [detail, setDetail] = useState(null);

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

  const itemName = (id) => {
    const it = items.find(i => i.id === id);
    return it ? `${it.code} — ${it.name}` : `#${id}`;
  };

  const openDetail = async (id) => {
    try {
      const res = await getStockTake(id);
      setDetail(res.data);
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    const validLines = lines.filter(l => l.item_id);
    if (!warehouseId || validLines.length === 0) { alert(t('stocktakes.validation')); return; }
    setLoading(true);
    try {
      await createStockTake({
        warehouse_id: Number(warehouseId),
        reference: reference || `ST-${Date.now()}`,
        note: note || null,
        lines: validLines.map(l => ({ item_id: Number(l.item_id), counted_qty: parseFloat(l.counted_qty) || 0 })),
      });
      setShowForm(false); setLines([]); setReference(''); setNote(''); setWarehouseId(''); setStock([]);
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
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>{t('stocktakes.new')}</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>{t('stocktakes.warehouse')}</label>
                <select value={warehouseId} onChange={e => { setWarehouseId(e.target.value); loadStockForWarehouse(e.target.value); }} required>
                  <option value="">{t('stocktakes.select_warehouse')}</option>
                  {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>{t('stocktakes.reference')}</label><input value={reference} onChange={e => setReference(e.target.value)} placeholder={t('stocktakes.auto_ref')} /></div>
              <div className="form-group"><label>{t('stocktakes.note')}</label><input value={note} onChange={e => setNote(e.target.value)} /></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '1rem 0' }}>
              <strong>{t('stocktakes.counted_lines')}</strong>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={addLine}>{t('stocktakes.add_item')}</button>
            </div>

            <div className="table-container" style={{ marginBottom: '1rem' }}>
              <table>
                <thead><tr><th>{t('stocktakes.item')}</th><th>{t('stocktakes.book_qty')}</th><th>{t('stocktakes.counted_qty')}</th><th></th></tr></thead>
                <tbody>
                  {lines.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '1.5rem' }}>{t('stocktakes.add_items_hint')}</td></tr>}
                  {lines.map((l, idx) => (
                    <tr key={idx}>
                      <td>
                        <select value={l.item_id} onChange={e => updateLine(idx, 'item_id', e.target.value)} required>
                          <option value="">{t('stocktakes.select_item')}</option>
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
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('stocktakes.create')}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>{t('stocktakes.reference')}</th><th>{t('stocktakes.warehouse')}</th><th>{t('stocktakes.status')}</th><th>{t('stocktakes.posted_at')}</th><th>{t('stocktakes.actions')}</th></tr></thead>
          <tbody>
            {stockTakes.length === 0
              ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('stocktakes.no_takes')}</td></tr>
              : stockTakes.map(st => (
                <tr key={st.id}>
                  <td style={{ fontWeight: 600 }}>{st.reference}</td>
                  <td>{whName(st.warehouse_id)}</td>
                  <td>{statusBadge(st.status)}</td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{st.posted_at || '—'}</td>
                  <td>
                    {st.status === 'draft' && (
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => openDetail(st.id)}>{t('stocktakes.view')}</button>
                        <button className="btn btn-primary" onClick={() => handlePost(st.id)}>{t('stocktakes.post')}</button>
                      </div>
                    )}
                    {st.status === 'posted' && (
                      <button className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => openDetail(st.id)}>{t('stocktakes.view')}</button>
                    )}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {detail && (
        <div className="modal-backdrop" onClick={() => setDetail(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '760px', maxHeight: '80vh', overflow: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <h3 style={{ margin: 0 }}>{detail.reference}</h3>
              <button className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setDetail(null)}>✕</button>
            </div>
            <p style={{ margin: '0 0 1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              {t('stocktakes.warehouse_label', { name: whName(detail.warehouse_id) })} · {t('stocktakes.status_label', { status: '' })}{statusBadge(detail.status)} · {t('stocktakes.posted_label', { date: detail.posted_at || '—' })}
              {detail.note && <> · {t('stocktakes.note_label', { note: detail.note })}</>}
            </p>
            <div className="table-container">
              <table>
                <thead><tr><th>{t('stocktakes.item')}</th><th>{t('stocktakes.book_qty')}</th><th>{t('stocktakes.counted_qty')}</th><th>{t('stocktakes.diff')}</th><th>{t('stocktakes.unit_cost')}</th><th>{t('stocktakes.adjustment')}</th></tr></thead>
                <tbody>
                  {(detail.lines || []).map(l => {
                    const diff = parseFloat(l.diff_qty || 0);
                    return (
                      <tr key={l.id}>
                        <td>{itemName(l.item_id)}</td>
                        <td>{parseFloat(l.book_qty || 0).toFixed(2)}</td>
                        <td>{parseFloat(l.counted_qty || 0).toFixed(2)}</td>
                        <td style={{ color: diff !== 0 ? 'var(--warning)' : 'var(--text-secondary)', fontWeight: 600 }}>{diff >= 0 ? '+' : ''}{diff.toFixed(2)}</td>
                        <td>${parseFloat(l.unit_cost || 0).toFixed(4)}</td>
                        <td style={{ fontWeight: 600 }}>${parseFloat(l.adjustment_value || 0).toFixed(2)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
