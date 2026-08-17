import { useState, useEffect } from 'react';
import { getSalesInvoices, createSalesInvoice, confirmSalesInvoice, deleteSalesInvoice, getPartners, getItems } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Sales() {
  const { t } = useTranslation();
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
    } catch (err) { alert(err.response?.data?.detail || t('sales.create_fail')); }
    finally { setLoading(false); }
  };

  const handleConfirm = async (id) => {
    try { await confirmSalesInvoice(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || t('sales.confirm_fail')); }
  };

  const handleDelete = async (id, number) => {
    if (!window.confirm(t('sales.delete_draft', { number }))) return;
    try { await deleteSalesInvoice(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || t('sales.delete_fail')); }
  };

  const fmt = (inv) => `${parseFloat(inv.total_amount || 0).toFixed(2)} ${inv.currency_code || 'USD'}`;
  const fmtBase = (inv) => `($${parseFloat(inv.total_amount_base || 0).toFixed(2)})`;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>+ {t('sales.new_invoice')}</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>{t('sales.new_invoice')}</h3>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group"><label>{t('sales.invoice_no')}</label><input value={form.number} onChange={e => setForm({...form, number: e.target.value})} placeholder={t('common.auto_code_hint')} /></div>
              <div className="form-group"><label>{t('sales.date')}</label><input type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} required /></div>
              <div className="form-group">
                <label>{t('sales.customer')}</label>
                <select value={form.partner_id} onChange={e => setForm({...form, partner_id: e.target.value})} required>
                  <option value="">{t('sales.select_customer')}</option>
                  {partners.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>{t('sales.currency')}</label><input value={form.currency_code} onChange={e => setForm({...form, currency_code: e.target.value})} /></div>
              <div className="form-group"><label>{t('sales.fx_rate')}</label><input type="number" step="0.0001" value={form.fx_rate} onChange={e => setForm({...form, fx_rate: e.target.value})} /></div>
            </div>

            <h4 style={{ margin: '1.5rem 0 1rem' }}>{t('sales.invoice_lines')}</h4>
            {form.lines.map((line, i) => (
              <div key={i} className="invoice-line">
                <div className="form-group" style={{ flex: 2 }}>
                  <label>{t('sales.item')}</label>
                  <select value={line.item_id} onChange={e => updateLine(i, 'item_id', e.target.value)} required>
                    <option value="">-- {t('sales.item')} --</option>
                    {items.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>{t('sales.description')}</label>
                  <input value={line.description} onChange={e => updateLine(i, 'description', e.target.value)} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>{t('sales.qty')}</label>
                  <input type="number" min="0.01" step="0.01" value={line.quantity} onChange={e => updateLine(i, 'quantity', e.target.value)} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>{t('sales.price')}</label>
                  <input type="number" min="0" step="0.01" value={line.unit_price} onChange={e => updateLine(i, 'unit_price', e.target.value)} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>{t('sales.total')}</label>
                  <div style={{ padding: '0.75rem 0', fontWeight: 600 }}>${(parseFloat(line.quantity||0)*parseFloat(line.unit_price||0)).toFixed(2)}</div>
                </div>
                {form.lines.length > 1 && <button type="button" className="remove-btn" style={{ marginTop: '1.5rem' }} onClick={() => removeLine(i)}>×</button>}
              </div>
            ))}
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', alignItems: 'center' }}>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.08)' }} onClick={addLine}>{t('sales.add_line')}</button>
              <div style={{ marginLeft: 'auto', fontWeight: 700, fontSize: '1.25rem' }}>{t('sales.total_label', { amount: `$${total.toFixed(2)}` })}</div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('sales.create_invoice')}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>{t('sales.invoice_no_col')}</th><th>{t('sales.date')}</th><th>{t('sales.customer_col')}</th><th>{t('sales.currency')}</th><th>{t('sales.total')}</th><th>{t('sales.status')}</th><th>{t('sales.action')}</th></tr></thead>
          <tbody>
            {invoices.length === 0
              ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('sales.no_invoices')}</td></tr>
              : invoices.map(inv => (
                <tr key={inv.id}>
                  <td>{inv.number}</td>
                  <td>{inv.date}</td>
                  <td>{partners.find(p => p.id === inv.partner_id)?.name || t('sales.customer_id', { id: inv.partner_id })}</td>
                  <td>{inv.currency_code || 'USD'} (fx {parseFloat(inv.fx_rate || 1).toFixed(4)})</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{fmt(inv)}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{fmtBase(inv)}</div>
                  </td>
                  <td><span className={`status-badge ${inv.is_confirmed ? 'status-completed' : 'status-pending'}`}>{inv.is_confirmed ? t('sales.confirmed') : t('sales.draft')}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {!inv.is_confirmed && (
                        <>
                          <button className="btn btn-primary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleConfirm(inv.id)}>{t('sales.confirm')}</button>
                          <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDelete(inv.id, inv.number)}>{t('sales.delete')}</button>
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
