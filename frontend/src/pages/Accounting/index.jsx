import { useState, useEffect } from 'react';
import { getTrialBalance, getIncomeStatement, getBalanceSheet, getJournalEntries, createJournalEntry, getAccounts, createAccount } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Accounting() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('trial-balance');
  const [tb, setTb] = useState(null);
  const [is, setIs] = useState(null);
  const [bs, setBs] = useState(null);
  const [entries, setEntries] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', account_type: 'asset' });
  const [showEntryForm, setShowEntryForm] = useState(false);
  const [entryForm, setEntryForm] = useState({ reference: '', entry_date: new Date().toISOString().split('T')[0], notes: '', lines: [{ account_id: '', description: '', debit: 0, credit: 0 }] });
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState('');

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [tbRes, isRes, bsRes, jeRes, accRes] = await Promise.all([
        getTrialBalance(), getIncomeStatement(), getBalanceSheet(), getJournalEntries(), getAccounts()
      ]);
      setTb(tbRes.data);
      setIs(isRes.data);
      setBs(bsRes.data);
      setEntries(jeRes.data || []);
      setAccounts(accRes.data || []);
      setLoadError('');
    } catch { setLoadError(t('accounting.load_failed')); }
  };

  const handleCreateAccount = async (e) => {
    e.preventDefault(); setLoading(true);
    try { await createAccount(form); setShowForm(false); setForm({ code: '', name: '', account_type: 'asset' }); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const fmt = (n) => `$${parseFloat(n || 0).toFixed(2)}`;

  const addEntryLine = () => setEntryForm(f => ({ ...f, lines: [...f.lines, { account_id: '', description: '', debit: 0, credit: 0 }] }));
  const removeEntryLine = (i) => setEntryForm(f => ({ ...f, lines: f.lines.filter((_, idx) => idx !== i) }));
  const updateEntryLine = (i, field, val) => setEntryForm(f => ({ ...f, lines: f.lines.map((l, idx) => idx === i ? { ...l, [field]: val } : l) }));

  const entryTotalDebit = entryForm.lines.reduce((s, l) => s + parseFloat(l.debit || 0), 0);
  const entryTotalCredit = entryForm.lines.reduce((s, l) => s + parseFloat(l.credit || 0), 0);

  const handleCreateEntry = async (e) => {
    e.preventDefault();
    if (Math.abs(entryTotalDebit - entryTotalCredit) > 0.001) { alert(t('accounting.balance_error')); return; }
    setLoading(true);
    try {
      await createJournalEntry({
        reference: entryForm.reference,
        entry_date: entryForm.entry_date ? `${entryForm.entry_date}T00:00:00Z` : null,
        notes: entryForm.notes || null,
        lines: entryForm.lines.filter(l => l.account_id).map(l => ({ account_id: parseInt(l.account_id), description: l.description || null, debit: parseFloat(l.debit || 0), credit: parseFloat(l.credit || 0) })),
      });
      setShowEntryForm(false);
      setEntryForm({ reference: '', entry_date: new Date().toISOString().split('T')[0], notes: '', lines: [{ account_id: '', description: '', debit: 0, credit: 0 }] });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating entry'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      {loadError && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', padding: '0.75rem 1rem', marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--danger)' }}>
          <span>{loadError}</span>
          <button className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={fetchAll}>{t('accounting.retry')}</button>
        </div>
      )}
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'trial-balance' ? 'active' : ''}`} onClick={() => setTab('trial-balance')}>{t('accounting.tab_trial_balance')}</button>
        <button className={`tab-btn ${tab === 'income' ? 'active' : ''}`} onClick={() => setTab('income')}>{t('accounting.tab_income')}</button>
        <button className={`tab-btn ${tab === 'balance-sheet' ? 'active' : ''}`} onClick={() => setTab('balance-sheet')}>{t('accounting.tab_balance_sheet')}</button>
        <button className={`tab-btn ${tab === 'journal' ? 'active' : ''}`} onClick={() => setTab('journal')}>{t('accounting.tab_journal')}</button>
        <button className={`tab-btn ${tab === 'coa' ? 'active' : ''}`} onClick={() => setTab('coa')}>{t('accounting.tab_coa')}</button>
      </div>

      {tab === 'trial-balance' && tb && (
        <div className="table-container">
          <table>
            <thead><tr><th>{t('accounting.code')}</th><th>{t('accounting.account_name')}</th><th>{t('accounting.type')}</th><th style={{ textAlign:'right' }}>{t('accounting.debit')}</th><th style={{ textAlign:'right' }}>{t('accounting.credit')}</th></tr></thead>
            <tbody>
              {tb.lines?.map(line => (
                <tr key={line.account_id}>
                  <td>{line.account_code}</td>
                  <td>{line.account_name}</td>
                  <td><span className="status-badge status-pending" style={{ fontSize: '0.7rem' }}>{line.account_type}</span></td>
                  <td style={{ textAlign:'right', color: line.debit > 0 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{line.debit > 0 ? fmt(line.debit) : '-'}</td>
                  <td style={{ textAlign:'right', color: line.credit > 0 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{line.credit > 0 ? fmt(line.credit) : '-'}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr style={{ fontWeight: 700 }}>
                <td colSpan={3}>{t('accounting.totals')}</td>
                <td style={{ textAlign:'right', color: 'var(--success)' }}>{fmt(tb.total_debit)}</td>
                <td style={{ textAlign:'right', color: 'var(--danger)' }}>{fmt(tb.total_credit)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      {tab === 'income' && is && (
        <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr', marginBottom: '1.5rem' }}>
          <div className="glass-card"><div className="kpi-title">{t('accounting.total_revenue')}</div><div className="kpi-value" style={{ color: 'var(--success)' }}>{fmt(is.revenue)}</div></div>
          <div className="glass-card"><div className="kpi-title">{t('accounting.cogs')}</div><div className="kpi-value" style={{ color: 'var(--danger)' }}>{fmt(is.cogs)}</div></div>
          <div className="glass-card"><div className="kpi-title">{t('accounting.gross_profit')}</div><div className="kpi-value">{fmt(is.gross_profit)}</div></div>
          <div className="glass-card"><div className="kpi-title">{t('accounting.operating_expenses')}</div><div className="kpi-value" style={{ color: 'var(--warning)' }}>{fmt(is.expenses)}</div></div>
          <div className="glass-card" style={{ gridColumn: '1/-1', borderColor: 'var(--primary-color)' }}>
            <div className="kpi-title">{t('accounting.net_income')}</div>
            <div className="kpi-value" style={{ color: parseFloat(is.net_income) >= 0 ? 'var(--success)' : 'var(--danger)' }}>{fmt(is.net_income)}</div>
          </div>
        </div>
      )}

      {tab === 'balance-sheet' && bs && (
        <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
          <div className="glass-card"><div className="kpi-title">{t('accounting.total_assets')}</div><div className="kpi-value" style={{ color: 'var(--success)' }}>{fmt(bs.assets)}</div></div>
          <div className="glass-card"><div className="kpi-title">{t('accounting.total_liabilities')}</div><div className="kpi-value" style={{ color: 'var(--danger)' }}>{fmt(bs.liabilities)}</div></div>
          <div className="glass-card"><div className="kpi-title">{t('accounting.total_equity')}</div><div className="kpi-value">{fmt(bs.equity)}</div></div>
        </div>
      )}

      {tab === 'journal' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowEntryForm(!showEntryForm)}>{t('accounting.new_entry')}</button>
          </div>

          {showEntryForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{t('accounting.new_entry_title')}</h3>
              <form onSubmit={handleCreateEntry}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('accounting.reference')}</label><input value={entryForm.reference} onChange={e => setEntryForm({...entryForm, reference: e.target.value})} placeholder={t('common.auto_code_hint')} /></div>
                  <div className="form-group"><label>{t('accounting.date')}</label><input type="date" value={entryForm.entry_date} onChange={e => setEntryForm({...entryForm, entry_date: e.target.value})} /></div>
                  <div className="form-group" style={{ gridColumn: '1/-1' }}><label>{t('accounting.notes')}</label><input value={entryForm.notes} onChange={e => setEntryForm({...entryForm, notes: e.target.value})} /></div>
                </div>

                {entryForm.lines.map((line, i) => (
                  <div key={i} className="invoice-line">
                    <div className="form-group" style={{ flex: 2 }}>
                      <label>{t('accounting.account')}</label>
                      <select value={line.account_id} onChange={e => updateEntryLine(i, 'account_id', e.target.value)} required>
                        <option value="">{t('common.select')}</option>
                        {accounts.map(a => <option key={a.id} value={a.id}>{a.code} — {a.name}</option>)}
                      </select>
                    </div>
                    <div className="form-group" style={{ flex: 2 }}>
                      <label>{t('accounting.description')}</label>
                      <input value={line.description} onChange={e => updateEntryLine(i, 'description', e.target.value)} />
                    </div>
                    <div className="form-group" style={{ flex: 1 }}>
                      <label>{t('accounting.debit')}</label>
                      <input type="number" min="0" step="0.01" value={line.debit} onChange={e => updateEntryLine(i, 'debit', e.target.value)} />
                    </div>
                    <div className="form-group" style={{ flex: 1 }}>
                      <label>{t('accounting.credit')}</label>
                      <input type="number" min="0" step="0.01" value={line.credit} onChange={e => updateEntryLine(i, 'credit', e.target.value)} />
                    </div>
                    {entryForm.lines.length > 1 && <button type="button" className="remove-btn" style={{ marginTop: '1.5rem' }} onClick={() => removeEntryLine(i)}>×</button>}
                  </div>
                ))}
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', alignItems: 'center' }}>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.08)' }} onClick={addEntryLine}>{t('accounting.add_line')}</button>
                  <div style={{ marginLeft: 'auto', fontWeight: 700 }}>
                    {t('accounting.dr')}: {fmt(entryTotalDebit)} &nbsp;|&nbsp; {t('accounting.cr')}: {fmt(entryTotalCredit)}
                    <span style={{ marginLeft: '0.75rem', color: Math.abs(entryTotalDebit - entryTotalCredit) < 0.001 ? 'var(--success)' : 'var(--danger)' }}>
                      {Math.abs(entryTotalDebit - entryTotalCredit) < 0.001 ? t('accounting.balanced') : t('accounting.diff', { amount: fmt(entryTotalDebit - entryTotalCredit) })}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('accounting.post_entry')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowEntryForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}

          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>{t('accounting.reference')}</th><th>{t('accounting.date')}</th><th>{t('accounting.notes')}</th><th>{t('accounting.lines')}</th></tr></thead>
              <tbody>
                {entries.length === 0
                  ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('accounting.no_entries')}</td></tr>
                  : entries.map((e, i) => <tr key={e.id}><td>{i+1}</td><td>{e.reference}</td><td>{e.entry_date || '-'}</td><td>{e.notes || '-'}</td><td>{(e.lines || []).length}</td></tr>)}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'coa' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>{t('accounting.new_account')}</button>
          </div>
          {showForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <form onSubmit={handleCreateAccount}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('accounting.account_code')}</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('accounting.account_name_col')}</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                  <div className="form-group">
                    <label>{t('accounting.account_type')}</label>
                    <select value={form.account_type} onChange={e => setForm({...form, account_type: e.target.value})}>
                      <option value="asset">{t('accounting.asset')}</option>
                      <option value="liability">{t('accounting.liability')}</option>
                      <option value="equity">{t('accounting.equity')}</option>
                      <option value="revenue">{t('accounting.revenue')}</option>
                      <option value="cogs">{t('accounting.cogs_type')}</option>
                      <option value="expense">{t('accounting.expense')}</option>
                      <option value="receivable">{t('accounting.receivable')}</option>
                      <option value="payable">{t('accounting.payable')}</option>
                      <option value="inventory">{t('accounting.inventory')}</option>
                      <option value="cash">{t('accounting.cash_bank')}</option>
                    </select>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('accounting.save_account')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>{t('accounting.code')}</th><th>{t('accounting.name')}</th><th>{t('accounting.type_col')}</th></tr></thead>
              <tbody>
                {accounts.map(a => <tr key={a.id}><td>{a.code}</td><td>{a.name}</td><td><span className="status-badge status-pending" style={{ fontSize: '0.7rem' }}>{a.account_type}</span></td></tr>)}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
