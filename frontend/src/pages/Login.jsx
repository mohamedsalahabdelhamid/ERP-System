import { useState } from 'react';
import { getMe, login, selectCompany } from '../api/client';
import './Login.css';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [token, setToken] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await login(email, password);
      const accessToken = res.data.access_token;
      localStorage.setItem('access_token', accessToken);

      const me = await getMe();
      const companies = me.data.companies || [];
      if (companies.length === 0) {
        setError('No company is linked to this account. Create one first.');
        localStorage.removeItem('access_token');
        setLoading(false);
        return;
      }
      if (companies.length === 1) {
        await pickCompany(accessToken, companies[0]);
      } else {
        setToken(accessToken);
        setCompanies(companies);
        setLoading(false);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.');
      localStorage.removeItem('access_token');
      setLoading(false);
    }
  };

  const pickCompany = async (accessToken, company) => {
    try {
      await selectCompany(company.id, company.branch_id);
      localStorage.setItem('company_id', company.id);
      if (company.branch_id) localStorage.setItem('branch_id', company.branch_id);
      onLogin();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to select company.');
      localStorage.removeItem('access_token');
      setLoading(false);
    }
  };

  if (companies.length > 0) {
    return (
      <div className="login-page">
        <div className="login-bg" />
        <div className="login-card glass-card">
          <div className="login-brand">ERP System</div>
          <p className="login-subtitle">Select a workspace</p>
          {error && <div className="login-error">{error}</div>}
          <div className="company-list">
            {companies.map((c) => (
              <button
                key={c.id}
                type="button"
                className="btn btn-primary"
                style={{ width: '100%', marginBottom: '0.5rem', textAlign: 'left' }}
                onClick={() => pickCompany(token, c)}
              >
                🏢 {c.name} <small>({c.code})</small>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-bg" />
      <div className="login-card glass-card">
        <div className="login-brand">ERP System</div>
        <p className="login-subtitle">Sign in to your workspace</p>
        {error && <div className="login-error">{error}</div>}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>Email Address</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.875rem' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
