import { useState, useEffect } from 'react';
import { getPayments, createPayment, getPartners, getCurrentCompany } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Payments() {
  const { t } = useTranslation();
  const [payments, setPayments] = useState([]);
  const [partners, setPartners] = useState([]);
  const [baseCurrency, setBaseCurrency] = useState('EGP');
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    partner_id: '', reference: '', amount: '', currency_code: 'EGP', payment_method: 'cash', payment_date: new Date().toISOString().split('T')[0], notes: '',
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [p, pr, cc] = await Promise.all([getPayments(), getPartners(), getCurrentCompany()]);
      setPayments(p.data || []);
      setPartners(pr.data || []);
      if (cc.data && cc.data.base_currency) setBaseCurrency(cc.data.base_currency);
    } catch { setPayments([]); setPartners([]); }
  };

  const partnerName = (id) => (partners.find(x => x.id === id) || {}).name || `#${id}`;
  const fmtCur = (code, n) => `${code || baseCurrency} ${parseFloat(n || 0).toFixed(2)}`;
  const fmtBase = (n) => `${baseCurrency} ${parseFloat(n || 0).toFixed(2)}`;

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
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>{t('payments.new_payment')}</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>{t('payments.new_payment_title')}</h3>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>{t('payments.partner')}</label>
                <select value={form.partner_id} onChange={e => setForm({...form, partner_id: e.target.value})} required>
                  <option value="">{t('common.select')}</option>
                  {partners.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>{t('payments.reference')}</label><input value={form.reference} onChange={e => setForm({...form, reference: e.target.value})} required /></div>
              <div className="form-group"><label>{t('payments.amount')}</label><input type="number" min="0" step="0.01" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} required /></div>
              <div className="form-group"><label>{t('payments.currency')}</label><input value={form.currency_code} onChange={e => setForm({...form, currency_code: e.target.value})} /></div>
              <div className="form-group">
                <label>{t('payments.method')}</label>
                <select value={form.payment_method} onChange={e => setForm({...form, payment_method: e.target.value})}>
                  <option value="cash">{t('payments.cash')}</option>
                  <option value="card">{t('payments.card')}</option>
                  <option value="bank_transfer">{t('payments.bank_transfer')}</option>
                  <option value="cheque">{t('payments.cheque')}</option>
                </select>
              </div>
              <div className="form-group"><label>{t('payments.date')}</label><input type="date" value={form.payment_date} onChange={e => setForm({...form, payment_date: e.target.value})} /></div>
              <div className="form-group" style={{ gridColumn: '1/-1' }}><label>{t('payments.notes')}</label><input value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} /></div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('payments.save_payment')}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>{t('payments.reference_col')}</th><th>{t('payments.partner_col')}</th><th>{t('payments.date')}</th><th>{t('payments.amount')}</th><th>{t('payments.base_amount')}</th><th>{t('payments.method_col')}</th><th>{t('payments.fx_gl')}</th></tr></thead>
          <tbody>
            {payments.length === 0
              ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('payments.no_payments')}</td></tr>
              : payments.map(p => (
                <tr key={p.id}>
                  <td>{p.reference}</td>
                  <td>{partnerName(p.partner_id)}</td>
                  <td>{p.payment_date || '-'}</td>
                  <td>{fmtCur(p.currency_code, p.amount)}</td>
                  <td>{fmtBase(p.base_amount)}</td>
                  <td><span className="status-badge status-pending" style={{ fontSize: '0.7rem' }}>{p.payment_method}</span></td>
                  <td style={{ color: parseFloat(p.fx_gain_loss || 0) >= 0 ? 'var(--success)' : 'var(--danger)' }}>{fmtBase(p.fx_gain_loss)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
