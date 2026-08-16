import { useState, useEffect } from 'react';
import api from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

const getSettings = () => api.get('/companies/settings');
const updateSettings = (data) => api.patch('/companies/settings', data);

export default function CompanySettings() {
  const { t } = useTranslation();
  const [settings, setSettings] = useState(null);
  const [form, setForm] = useState({
    low_stock_threshold: 0,
    alert_emails: '',
    block_negative_stock: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await getSettings();
      setSettings(res.data);
      setForm({
        low_stock_threshold: res.data.low_stock_threshold ?? 0,
        alert_emails: res.data.alert_emails ?? '',
        block_negative_stock: res.data.block_negative_stock ?? true,
      });
    } catch (err) {
      showToast(t('companysettings.load_failed'), 'error');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        low_stock_threshold: parseFloat(form.low_stock_threshold) || 0,
        alert_emails: form.alert_emails.trim() || null,
        block_negative_stock: form.block_negative_stock,
      };
      const res = await updateSettings(payload);
      setSettings(res.data);
      showToast(`✅ ${t('companysettings.save_success')}`, 'success');
    } catch (err) {
      showToast(err.response?.data?.detail || t('companysettings.save_failed'), 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>{t('companysettings.loading')}</div>;
  }

  return (
    <div>
      {/* Toast notification */}
      {toast && (
        <div style={{
          position: 'fixed', top: '1.5rem', right: '1.5rem', zIndex: 9999,
          padding: '0.875rem 1.5rem', borderRadius: '10px', fontWeight: 600,
          fontSize: '0.9rem',
          background: toast.type === 'success' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
          border: `1px solid ${toast.type === 'success' ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)'}`,
          color: toast.type === 'success' ? 'var(--success)' : 'var(--danger)',
          backdropFilter: 'blur(16px)',
          animation: 'fadeIn 0.3s ease',
        }}>
          {toast.msg}
        </div>
      )}

      <div style={{ maxWidth: '720px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

        {/* Current Settings Info */}
        {settings && (
          <div className="glass-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem' }}>
            <div>
              <div className="kpi-title">{t('companysettings.modules_enabled')}</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: '0.25rem' }}>
                {(settings.enabled_modules || []).length || 'All'}
              </div>
            </div>
            <div>
              <div className="kpi-title">{t('companysettings.cost_method')}</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: '0.25rem', textTransform: 'capitalize' }}>
                {settings.cost_method?.replace('_', ' ') || t('companysettings.weighted_average')}
              </div>
            </div>
            <div>
              <div className="kpi-title">{t('companysettings.max_users')}</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: '0.25rem' }}>{settings.max_users}</div>
            </div>
          </div>
        )}

        {/* Stock Alert Settings */}
        <div className="glass-card">
          <h3 style={{ marginBottom: '0.5rem', fontSize: '1.1rem' }}>📦 {t('companysettings.inventory_alerts')}</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
            {t('companysettings.alert_desc')}
          </p>

          <form onSubmit={handleSave}>
            {/* Block negative stock toggle */}
            <div className="glass-card" style={{
              marginBottom: '1.25rem', padding: '1rem 1.25rem',
              background: form.block_negative_stock ? 'rgba(16,185,129,0.05)' : 'rgba(239,68,68,0.05)',
              borderColor: form.block_negative_stock ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)',
            }}>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', cursor: 'pointer' }}>
                <div style={{ marginTop: '2px', flexShrink: 0 }}>
                  <input
                    type="checkbox"
                    id="block_negative_stock"
                    checked={form.block_negative_stock}
                    onChange={e => setForm({ ...form, block_negative_stock: e.target.checked })}
                    style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--success)' }}
                  />
                </div>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                    🔒 {t('companysettings.block_negative')}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {form.block_negative_stock
                      ? `✅ ${t('companysettings.block_enabled')}`
                      : `❌ ${t('companysettings.block_disabled')}`}
                  </div>
                </div>
              </label>
            </div>

            <div className="form-grid" style={{ marginBottom: '1.25rem' }}>
              {/* Threshold */}
              <div className="form-group">
                <label>{t('companysettings.threshold')}</label>
                <input
                  id="low_stock_threshold"
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.low_stock_threshold}
                  onChange={e => setForm({ ...form, low_stock_threshold: e.target.value })}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  {t('companysettings.threshold_hint')}
                </span>
              </div>
            </div>

            {/* Alert emails */}
            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label>{t('companysettings.alert_emails')}</label>
              <input
                id="alert_emails"
                type="text"
                placeholder={t('companysettings.alert_emails_placeholder')}
                value={form.alert_emails}
                onChange={e => setForm({ ...form, alert_emails: e.target.value })}
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem', display: 'block', lineHeight: 1.5 }}>
                {t('companysettings.alert_emails_hint')}
              </span>
            </div>

            {/* Preview of recipients */}
            {form.alert_emails && (
              <div style={{
                marginBottom: '1.5rem', padding: '0.875rem 1rem',
                background: 'rgba(79,70,229,0.08)', borderRadius: '8px',
                border: '1px solid rgba(79,70,229,0.25)',
              }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                  📧 {t('companysettings.will_send_to')}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {form.alert_emails.split(',').map(e => e.trim()).filter(Boolean).map((email, i) => (
                    <span key={i} style={{
                      padding: '0.2rem 0.625rem', borderRadius: '999px',
                      background: 'rgba(79,70,229,0.15)', fontSize: '0.8rem',
                      color: 'var(--primary-color)', fontWeight: 500,
                    }}>
                      {email}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={saving} style={{ minWidth: '160px' }}>
                {saving ? `⏳ ${t('companysettings.saving')}` : `💾 ${t('companysettings.save_settings')}`}
              </button>
            </div>
          </form>
        </div>

        {/* SMTP Note */}
        <div className="glass-card" style={{
          borderColor: 'rgba(245,158,11,0.3)',
          background: 'rgba(245,158,11,0.04)',
        }}>
          <h4 style={{ marginBottom: '0.5rem', color: 'var(--warning)', fontSize: '0.95rem' }}>
            ⚙️ {t('companysettings.smtp_title')}
          </h4>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.65 }}>
            {t('companysettings.smtp_desc')} <code>.env</code>
          </p>
          <pre style={{
            marginTop: '0.875rem', background: 'rgba(0,0,0,0.3)',
            borderRadius: '8px', padding: '0.875rem 1rem',
            fontSize: '0.78rem', lineHeight: 1.7, color: '#94a3b8', overflow: 'auto',
          }}>
{`SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourcompany.com
SMTP_FROM_NAME="ERP System"`}
          </pre>
        </div>
      </div>
    </div>
  );
}
