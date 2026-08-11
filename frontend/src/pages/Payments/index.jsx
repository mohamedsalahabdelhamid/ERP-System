import { useState, useEffect } from 'react';
import { getPayments, createPayment, getPartners } from '../../api/client';

export default function Payments() {
  const [payments, setPayments] = useState([]);
  const [partners, setPartners] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    partner_id: '', reference: '', amount: '', currency_code: 'EGP', payment_method: 'cash', payment_date: new Date().toISOString().split('T')[0], notes: '',
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [p, pr] = await Promise.all([getPayments(), getPartners()]);
      setPayments(p.data || []);
      setPartners(pr.data || []);
    } catch { setPayments([]); setPartners([]); }
  };

  const partnerName = (id) => (partners.find(x => x.id === id) || {}).name || `#${id}`;
  const fmt = (p, n) => `${p.currency_code || 'EGP'} ${parseFloat(n || 0).toFixed(2)}`;

  const handleCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createPayment({
        partner_id: parseInt(form.partner_id),
        reference: form.reference,
        amount: parseFloat(form.amount),
        currency_code: form.currency_code,
        payment_method: form.payment_method,
        payment_date: form.payment_date || null,
        notes: form.notes || null,
      });
      setShowForm(false);
      setForm({ partner_id: '', reference: '', amount: '', currency_code: 'EGP', payment_method: 'cash', payment_date: new Date().toISOString().split('T')[0], notes: '' });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating payment'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>+ New Payment</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>New Payment</h3>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>Partner</label>
                <select value={form.partner_id} onChange={e => setForm({...form, partner_id: e.target.value})} required>
                  <option value="">-- Select --</option>
                  {partners.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>Reference</label><input value={form.reference} onChange={e => setForm({...form, reference: e.target.value})} required /></div>
              <div className="form-group"><label>Amount</label><input type="number" min="0" step="0.01" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} required /></div>
              <div className="form-group"><label>Currency</label><input value={form.currency_code} onChange={e => setForm({...form, currency_code: e.target.value})} /></div>
              <div className="form-group">
                <label>Method</label>
                <select value={form.payment_method} onChange={e => setForm({...form, payment_method: e.target.value})}>
                  <option value="cash">Cash</option>
                  <option value="card">Card</option>
                  <option value="bank_transfer">Bank Transfer</option>
                  <option value="cheque">Cheque</option>
                </select>
              </div>
              <div className="form-group"><label>Date</label><input type="date" value={form.payment_date} onChange={e => setForm({...form, payment_date: e.target.value})} /></div>
              <div className="form-group" style={{ gridColumn: '1/-1' }}><label>Notes</label><input value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} /></div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : 'Save Payment'}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>Reference</th><th>Partner</th><th>Date</th><th>Amount</th><th>Base Amount</th><th>Method</th><th>FX G/L</th></tr></thead>
          <tbody>
            {payments.length === 0
              ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No payments found</td></tr>
              : payments.map(p => (
                <tr key={p.id}>
                  <td>{p.reference}</td>
                  <td>{partnerName(p.partner_id)}</td>
                  <td>{p.payment_date || '-'}</td>
                  <td>{fmt(p, p.amount)}</td>
                  <td>{fmt(p, p.base_amount)}</td>
                  <td><span className="status-badge status-pending" style={{ fontSize: '0.7rem' }}>{p.payment_method}</span></td>
                  <td style={{ color: parseFloat(p.fx_gain_loss || 0) >= 0 ? 'var(--success)' : 'var(--danger)' }}>{fmt(p, p.fx_gain_loss)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
