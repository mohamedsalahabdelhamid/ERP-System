import { useState, useEffect } from 'react';
import api from '../../api/client';
import { getItems, getWarehouses } from '../../api/client';

const getWorkOrders = () => api.get('/manufacturing/work-orders');
const createWorkOrderApi = (data) => api.post('/manufacturing/work-orders', data);
const finishWorkOrderApi = (id, data) => api.post(`/manufacturing/work-orders/${id}/finish`, data);
const getBomsApi = () => api.get('/manufacturing/boms');
const createBomApi = (data) => api.post('/manufacturing/boms', data);

export default function Manufacturing() {
  const [tab, setTab] = useState('work-orders');
  const [workOrders, setWorkOrders] = useState([]);
  const [boms, setBoms] = useState([]);
  const [items, setItems] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [showWOForm, setShowWOForm] = useState(false);
  const [showBOMForm, setShowBOMForm] = useState(false);
  const [showFinishForm, setShowFinishForm] = useState(null); // work order being finished
  const [loading, setLoading] = useState(false);

  const [woForm, setWoForm] = useState({ number: '', bom_id: '', item_id: '', warehouse_id: '', planned_quantity: 1 });
  const [bomForm, setBomForm] = useState({ name: '', item_id: '', quantity: 1, lines: [{ item_id: '', quantity: 1 }] });
  const [finishData, setFinishData] = useState({ labor: [{ description: '', hours: 1, hourly_rate: 0 }], overheads: [] });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [wo, b, itm, wh] = await Promise.all([getWorkOrders(), getBomsApi(), getItems(), getWarehouses()]);
      setWorkOrders(wo.data || []);
      setBoms(b.data || []);
      setItems(itm.data || []);
      setWarehouses(wh.data || []);
    } catch { setWorkOrders([]); setBoms([]); }
  };

  const handleCreateWO = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
      await createWorkOrderApi({
        number: woForm.number,
        bom_id: woForm.bom_id ? parseInt(woForm.bom_id) : null,
        item_id: parseInt(woForm.item_id),
        warehouse_id: parseInt(woForm.warehouse_id),
        planned_quantity: parseFloat(woForm.planned_quantity)
      });
      setShowWOForm(false); setWoForm({ number: '', bom_id: '', item_id: '', warehouse_id: '', planned_quantity: 1 }); fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const handleCreateBOM = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
      await createBomApi({
        name: bomForm.name,
        item_id: parseInt(bomForm.item_id),
        quantity: parseFloat(bomForm.quantity),
        lines: bomForm.lines.map(l => ({ item_id: parseInt(l.item_id), quantity: parseFloat(l.quantity) }))
      });
      setShowBOMForm(false); setBomForm({ name: '', item_id: '', quantity: 1, lines: [{ item_id: '', quantity: 1 }] }); fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const handleFinish = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
      await finishWorkOrderApi(showFinishForm.id, {
        labor: finishData.labor.map(l => ({ description: l.description, hours: parseFloat(l.hours), hourly_rate: parseFloat(l.hourly_rate) })),
        overheads: finishData.overheads.map(o => ({ description: o.description, total_cost: parseFloat(o.total_cost) }))
      });
      setShowFinishForm(null); setFinishData({ labor: [{ description: '', hours: 1, hourly_rate: 0 }], overheads: [] }); fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const addBomLine = () => setBomForm(f => ({ ...f, lines: [...f.lines, { item_id: '', quantity: 1 }] }));
  const removeBomLine = (i) => setBomForm(f => ({ ...f, lines: f.lines.filter((_, idx) => idx !== i) }));
  const updateBomLine = (i, field, val) => setBomForm(f => ({ ...f, lines: f.lines.map((l, idx) => idx === i ? { ...l, [field]: val } : l) }));

  const statusColor = { draft: 'status-pending', in_progress: 'status-pending', completed: 'status-completed' };

  const getItemName = (id) => {
    const itm = items.find(i => i.id === id);
    return itm ? itm.name : `Item #${id}`;
  };

  return (
    <div>
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'work-orders' ? 'active' : ''}`} onClick={() => setTab('work-orders')}>🏭 Work Orders</button>
        <button className={`tab-btn ${tab === 'boms' ? 'active' : ''}`} onClick={() => setTab('boms')}>📋 Bill of Materials</button>
      </div>

      {/* ---- WORK ORDERS ---- */}
      {tab === 'work-orders' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowWOForm(!showWOForm)}>+ New Work Order</button>
          </div>

          {showWOForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>New Work Order</h3>
              <form onSubmit={handleCreateWO}>
                <div className="form-grid">
                  <div className="form-group"><label>WO Number</label><input value={woForm.number} onChange={e => setWoForm({...woForm, number: e.target.value})} required placeholder="WO-2026-001" /></div>
                  <div className="form-group">
                    <label>Finished Product (Item)</label>
                    <select value={woForm.item_id} onChange={e => setWoForm({...woForm, item_id: e.target.value})} required>
                      <option value="">-- Select Item --</option>
                      {items.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>BOM (optional)</label>
                    <select value={woForm.bom_id} onChange={e => setWoForm({...woForm, bom_id: e.target.value})}>
                      <option value="">-- No BOM --</option>
                      {boms.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Warehouse</label>
                    <select value={woForm.warehouse_id} onChange={e => setWoForm({...woForm, warehouse_id: e.target.value})} required>
                      <option value="">-- Select Warehouse --</option>
                      {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>Planned Quantity</label><input type="number" step="0.01" min="0.01" value={woForm.planned_quantity} onChange={e => setWoForm({...woForm, planned_quantity: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Creating...' : 'Create Work Order'}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowWOForm(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}

          {showFinishForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem', borderColor: 'var(--success)' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>✅ Finish Work Order: {showFinishForm.number}</h3>
              <form onSubmit={handleFinish}>
                <h4 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Labor Costs</h4>
                {finishData.labor.map((l, i) => (
                  <div key={i} className="invoice-line">
                    <div className="form-group" style={{ flex: 2 }}><label>Description</label><input value={l.description} onChange={e => setFinishData(fd => ({ ...fd, labor: fd.labor.map((x, idx) => idx === i ? { ...x, description: e.target.value } : x) }))} /></div>
                    <div className="form-group" style={{ flex: 1 }}><label>Hours</label><input type="number" step="0.5" value={l.hours} onChange={e => setFinishData(fd => ({ ...fd, labor: fd.labor.map((x, idx) => idx === i ? { ...x, hours: e.target.value } : x) }))} /></div>
                    <div className="form-group" style={{ flex: 1 }}><label>Hourly Rate</label><input type="number" step="0.01" value={l.hourly_rate} onChange={e => setFinishData(fd => ({ ...fd, labor: fd.labor.map((x, idx) => idx === i ? { ...x, hourly_rate: e.target.value } : x) }))} /></div>
                    <div className="form-group" style={{ flex: 1 }}><label>Total</label><div style={{ padding: '0.625rem 0', fontWeight: 600 }}>${(parseFloat(l.hours||0)*parseFloat(l.hourly_rate||0)).toFixed(2)}</div></div>
                  </div>
                ))}
                <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.08)', marginBottom: '1.5rem' }} onClick={() => setFinishData(fd => ({ ...fd, labor: [...fd.labor, { description: '', hours: 1, hourly_rate: 0 }] }))}>+ Add Labor Row</button>

                <h4 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Overhead Costs</h4>
                {finishData.overheads.map((o, i) => (
                  <div key={i} className="invoice-line">
                    <div className="form-group" style={{ flex: 3 }}><label>Description</label><input value={o.description} onChange={e => setFinishData(fd => ({ ...fd, overheads: fd.overheads.map((x, idx) => idx === i ? { ...x, description: e.target.value } : x) }))} /></div>
                    <div className="form-group" style={{ flex: 1 }}><label>Amount</label><input type="number" step="0.01" value={o.total_cost} onChange={e => setFinishData(fd => ({ ...fd, overheads: fd.overheads.map((x, idx) => idx === i ? { ...x, total_cost: e.target.value } : x) }))} /></div>
                  </div>
                ))}
                <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.08)', marginBottom: '1.5rem' }} onClick={() => setFinishData(fd => ({ ...fd, overheads: [...fd.overheads, { description: '', total_cost: 0 }] }))}>+ Add Overhead</button>

                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Processing...' : '✅ Complete & Stock In'}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowFinishForm(null)}>Cancel</button>
                </div>
              </form>
            </div>
          )}

          <div className="table-container">
            <table>
              <thead><tr><th>WO Number</th><th>Item</th><th>Planned Qty</th><th>Material Cost</th><th>Labor Cost</th><th>Total Cost</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {workOrders.length === 0
                  ? <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No work orders</td></tr>
                  : workOrders.map(wo => (
                    <tr key={wo.id}>
                      <td style={{ fontWeight: 600 }}>{wo.number}</td>
                      <td style={{ fontWeight: 500 }}>{getItemName(wo.item_id)}</td>
                      <td>{parseFloat(wo.planned_quantity).toFixed(2)}</td>
                      <td>${parseFloat(wo.total_material_cost).toFixed(2)}</td>
                      <td>${parseFloat(wo.total_labor_cost).toFixed(2)}</td>
                      <td style={{ fontWeight: 600 }}>${parseFloat(wo.total_cost).toFixed(2)}</td>
                      <td><span className={`status-badge ${statusColor[wo.status] || 'status-pending'}`}>{wo.status}</span></td>
                      <td>
                        {wo.status !== 'completed' && (
                          <button className="btn btn-primary" style={{ padding: '0.25rem 0.625rem', fontSize: '0.75rem' }} onClick={() => setShowFinishForm(wo)}>Finish</button>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* ---- BOMs ---- */}
      {tab === 'boms' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowBOMForm(!showBOMForm)}>+ New BOM</button>
          </div>

          {showBOMForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>New Bill of Materials</h3>
              <form onSubmit={handleCreateBOM}>
                <div className="form-grid">
                  <div className="form-group"><label>BOM Name</label><input value={bomForm.name} onChange={e => setBomForm({...bomForm, name: e.target.value})} required /></div>
                  <div className="form-group">
                    <label>Finished Product (Item)</label>
                    <select value={bomForm.item_id} onChange={e => setBomForm({...bomForm, item_id: e.target.value})} required>
                      <option value="">-- Select --</option>
                      {items.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>Output Quantity</label><input type="number" step="0.01" value={bomForm.quantity} onChange={e => setBomForm({...bomForm, quantity: e.target.value})} /></div>
                </div>

                <h4 style={{ margin: '1.5rem 0 1rem', color: 'var(--text-secondary)' }}>Raw Material Components</h4>
                {bomForm.lines.map((line, i) => (
                  <div key={i} className="invoice-line">
                    <div className="form-group" style={{ flex: 3 }}>
                      <label>Component Item</label>
                      <select value={line.item_id} onChange={e => updateBomLine(i, 'item_id', e.target.value)} required>
                        <option value="">-- Select --</option>
                        {items.map(itm => <option key={itm.id} value={itm.id}>{itm.name}</option>)}
                      </select>
                    </div>
                    <div className="form-group" style={{ flex: 1 }}>
                      <label>Required Qty</label>
                      <input type="number" step="0.01" min="0.01" value={line.quantity} onChange={e => updateBomLine(i, 'quantity', e.target.value)} />
                    </div>
                    {bomForm.lines.length > 1 && <button type="button" className="remove-btn" style={{ marginTop: '1.5rem' }} onClick={() => removeBomLine(i)}>×</button>}
                  </div>
                ))}
                <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.08)', marginBottom: '1rem' }} onClick={addBomLine}>+ Add Component</button>

                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : 'Save BOM'}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowBOMForm(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}

          <div className="table-container">
            <table>
              <thead><tr><th>BOM Name</th><th>Finished Product</th><th>Output Qty</th><th>Components</th></tr></thead>
              <tbody>
                {boms.length === 0
                  ? <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No BOMs defined</td></tr>
                  : boms.map(bom => (
                    <tr key={bom.id}>
                      <td style={{ fontWeight: 600 }}>{bom.name}</td>
                      <td style={{ fontWeight: 500 }}>{getItemName(bom.item_id)}</td>
                      <td>{parseFloat(bom.quantity).toFixed(2)}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{(bom.lines || []).length} component(s)</td>
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
