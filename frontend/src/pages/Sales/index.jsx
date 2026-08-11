import { useState, useEffect } from 'react';
import { getSalesInvoices, createSalesInvoice, confirmSalesInvoice, deleteSalesInvoice, getPartners, getItems } from '../../api/client';

export default function Sales() {
  const [invoices, setInvoices] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [partners, setPartners] = useState([]);
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ partner_id: '', number: '', date: new Date().toISOString().split('T')[0], currency_code: 'USD', fx_rate: 1, lines: [{ item_id: '', quantity: 1, unit_price: 0, description: '' }] });
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [inv, par, itm] = await Promise.all([getSalesInvoices(), getPartners(), getItems()]);
      setInvoices(inv.data || []);
      setPartners((par.data || []).filter(p => ['customer', 'both'].includes(p.type)));
      setItems(itm.data || []);
    } catch { setInvoices([]); }
  };

  const addLine = () => setForm(f => ({ ...f, lines: [...f.lines, { item_id: '', quantity: 1, unit_price: 0, description: '' }] }));
  const removeLine = (i) => setForm(f => ({ ...f, lines: f.lines.filter((_, idx) => idx !== i) }));
  const updateLine = (i, field, val) => setForm(f => ({ ...f, lines: f.lines.map((l, idx) => idx === i ? { ...l, [field]: val } : l) }));

  const total = form.lines.reduce((s, l) => s + (parseFloat(l.quantity || 0) * parseFloat(l.unit_price || 0)), 0);

  const handleCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createSalesInvoice({
        ...form,
        partner_id: parseInt(form.partner_id),
        date: form.date ? `${form.date}T00:00:00Z` : undefined,
        fx_rate: parseFloat(form.fx_rate),
        lines: form.lines.map(l => ({ ...l, item_id: parseInt(l.item_id), quantity: parseFloat(l.quantity), unit_price: parseFloat(l.unit_price) })),
      });
      setShowForm(false);
      setForm({ partner_id: '', number: '', date: new Date().toISOString().split('T')[0], currency_code: 'USD', fx_rate: 1, lines: [{ item_id: '', quantity: 1, unit_price: 0, description: '' }] });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating invoice'); }
    finally { setLoading(false); }
  };

  const handleConfirm = async (id) => {
    try { await confirmSalesInvoice(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error confirming invoice'); }
  };

  const handleDelete = async (id, number) => {
    if (!window.confirm(`Delete draft invoice ${number}?`)) return;
    try { await deleteSalesInvoice(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error deleting invoice'); }
  };

  const fmt = (inv) => `${parseFloat(inv.total_amount || 0).toFixed(2)} ${inv.currency_code || 'USD'}`;
  const fmtBase = (inv) => `($${parseFloat(inv.total_amount_base || 0).toFixed(2)})`;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>+ New Sales Invoice</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>New Sales Invoice</h3>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group"><label>Invoice No</label><input value={form.number} onChange={e => setForm({...form, number: e.target.value})} required /></div>
              <div className="form-group"><label>Date</label><input type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} required /></div>
              <div className="form-group">
                <label>Customer</label>
                <select value={form.partner_id} onChange={e => setForm({...form, partner_id: e.target.value})} required>
                  <option value="">-- Select Customer --</option>
                  {partners.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>Currency</label><input value={form.currency_code} onChange={e => setForm({...form, currency_code: e.target.value})} /></div>
              <div className="form-group"><label>FX Rate</label><input type="number" step="0.0001" value={form.fx_rate} onChange={e => setForm({...form, fx_rate: e.target.value})} /></div>
            </div>

            <h4 style={{ margin: '1.5rem 0 1rem' }}>Invoice Lines</h4>
            {form.lines.map((line, i) => (
              <div key={i} className="invoice-line">
                <div className="form-group" style={{ flex: 2 }}>
                  <label>Item</label>
                  <select value={line.item_id} onChange={e => updateLine(i, 'item_id', e.target.value)} required>
                    <option value="">-- Item --</option>
                    {items.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Description</label>
                  <input value={line.description} onChange={e => updateLine(i, 'description', e.target.value)} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Qty</label>
                  <input type="number" min="0.01" step="0.01" value={line.quantity} onChange={e => updateLine(i, 'quantity', e.target.value)} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Price</label>
                  <input type="number" min="0" step="0.01" value={line.unit_price} onChange={e => updateLine(i, 'unit_price', e.target.value)} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Total</label>
                  <div style={{ padding: '0.75rem 0', fontWeight: 600 }}>${(parseFloat(line.quantity||0)*parseFloat(line.unit_price||0)).toFixed(2)}</div>
                </div>
                {form.lines.length > 1 && <button type="button" className="remove-btn" style={{ marginTop: '1.5rem' }} onClick={() => removeLine(i)}>×</button>}
              </div>
            ))}
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', alignItems: 'center' }}>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.08)' }} onClick={addLine}>+ Add Line</button>
              <div style={{ marginLeft: 'auto', fontWeight: 700, fontSize: '1.25rem' }}>Total: ${total.toFixed(2)}</div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : 'Create Invoice'}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>Invoice No</th><th>Date</th><th>Customer</th><th>Currency</th><th>Total</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
            {invoices.length === 0
              ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No invoices found</td></tr>
              : invoices.map(inv => (
                <tr key={inv.id}>
                  <td>{inv.number}</td>
                  <td>{inv.date}</td>
                  <td>{partners.find(p => p.id === inv.partner_id)?.name || `Customer #${inv.partner_id}`}</td>
                  <td>{inv.currency_code || 'USD'} (fx {parseFloat(inv.fx_rate || 1).toFixed(4)})</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{fmt(inv)}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{fmtBase(inv)}</div>
                  </td>
                  <td><span className={`status-badge ${inv.is_confirmed ? 'status-completed' : 'status-pending'}`}>{inv.is_confirmed ? 'Confirmed' : 'Draft'}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {!inv.is_confirmed && (
                        <>
                          <button className="btn btn-primary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleConfirm(inv.id)}>Confirm</button>
                          <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDelete(inv.id, inv.number)}>Delete</button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
