import { useState, useEffect } from 'react';
import { getCurrencies, createCurrency, deleteCurrency, getCurrencyRates, createCurrencyRate, deleteCurrencyRate } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Currencies() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('currencies');
  const [currencies, setCurrencies] = useState([]);
  const [rates, setRates] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', is_active: true });
  const [rateForm, setRateForm] = useState({ currency_code: '', rate_to_base: '', valid_from: new Date().toISOString().slice(0, 10) });
  const [showRateForm, setShowRateForm] = useState(false);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [c, r] = await Promise.all([getCurrencies(), getCurrencyRates()]);
      setCurrencies(c.data || []);
      setRates(r.data || []);
    } catch { setCurrencies([]); setRates([]); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createCurrency({ ...form, code: form.code.toUpperCase() });
      setShowForm(false);
      setForm({ code: '', name: '', is_active: true });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating currency'); }
    finally { setLoading(false); }
  };

  const handleDeleteCurrency = async (id) => {
    if (!window.confirm(t('currencies.delete_currency'))) return;
    try { await deleteCurrency(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const handleCreateRate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createCurrencyRate({ currency_code: rateForm.currency_code, rate_to_base: parseFloat(rateForm.rate_to_base), valid_from: rateForm.valid_from ? `${rateForm.valid_from}T00:00:00` : null });
      setShowRateForm(false);
      setRateForm({ currency_code: '', rate_to_base: '', valid_from: new Date().toISOString().slice(0, 10) });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating rate'); }
    finally { setLoading(false); }
  };

  const handleDeleteRate = async (id) => {
    if (!window.confirm(t('currencies.delete_rate'))) return;
    try { await deleteCurrencyRate(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  return (
    <div>
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'currencies' ? 'active' : ''}`} onClick={() => setTab('currencies')}>{t('currencies.tab_currencies')}</button>
        <button className={`tab-btn ${tab === 'rates' ? 'active' : ''}`} onClick={() => setTab('rates')}>{t('currencies.tab_rates')}</button>
      </div>

      {tab === 'currencies' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>{t('currencies.add_currency')}</button>
          </div>
          {showForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{t('currencies.new_currency')}</h3>
              <form onSubmit={handleCreate}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('currencies.code')}</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('currencies.name')}</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('currencies.save_currency')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>{t('currencies.code')}</th><th>{t('currencies.name')}</th><th>{t('currencies.status')}</th><th></th></tr></thead>
              <tbody>
                {currencies.length === 0
                  ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('currencies.no_currencies')}</td></tr>
                  : currencies.map((c, i) => (
                    <tr key={c.id}>
                      <td>{i + 1}</td>
                      <td style={{ fontWeight: 600 }}>{c.code}</td>
                      <td>{c.name}</td>
                      <td><span className={`status-badge ${c.is_active ? 'status-completed' : 'status-pending'}`}>{c.is_active ? t('currencies.active') : t('currencies.inactive')}</span></td>
                      <td><button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteCurrency(c.id)}>{t('currencies.delete')}</button></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'rates' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowRateForm(!showRateForm)}>{t('currencies.add_rate')}</button>
          </div>
          {showRateForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{t('currencies.new_rate')}</h3>
              <form onSubmit={handleCreateRate}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>{t('currencies.currency')}</label>
                    <select value={rateForm.currency_code} onChange={e => setRateForm({...rateForm, currency_code: e.target.value})} required>
                      <option value="">{t('common.select')}</option>
                      {currencies.filter(c => c.is_active).map(c => <option key={c.id} value={c.code}>{c.code} — {c.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>{t('currencies.rate_to_base', { code: rateForm.currency_code || t('currencies.currency') })}</label><input type="number" min="0" step="0.0001" value={rateForm.rate_to_base} onChange={e => setRateForm({...rateForm, rate_to_base: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('currencies.valid_from')}</label><input type="date" value={rateForm.valid_from} onChange={e => setRateForm({...rateForm, valid_from: e.target.value})} /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('currencies.save_rate')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowRateForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>{t('currencies.currency')}</th><th>{t('currencies.rate_col')}</th><th>{t('currencies.valid_from')}</th><th></th></tr></thead>
              <tbody>
                {rates.length === 0
                  ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('currencies.no_rates')}</td></tr>
                  : rates.map((r, i) => (
                    <tr key={r.id}>
                      <td>{i + 1}</td>
                      <td style={{ fontWeight: 600 }}>{r.currency_code}</td>
                      <td>{parseFloat(r.rate_to_base || 0).toFixed(4)}</td>
                      <td>{r.valid_from || '-'}</td>
                      <td><button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteRate(r.id)}>{t('currencies.delete')}</button></td>
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
