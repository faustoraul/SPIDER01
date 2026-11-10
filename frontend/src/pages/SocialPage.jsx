import { useEffect, useState } from 'react';
import { api } from '../services/api';

const PROVIDERS = ['facebook', 'instagram', 'whatsapp', 'messenger', 'tiktok', 'youtube', 'linkedin'];

const STATUS_COLORS = {
  processed: '#198754',
  pending: '#fd7e14',
  failed: '#dc3545',
};

export default function SocialPage() {
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState('');
  const [accounts, setAccounts] = useState([]);
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);

  // Estado del formulario de creación de cuenta
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [accountForm, setAccountForm] = useState({
    provider: 'facebook',
    external_account_id: '',
    access_token: '',
  });

  useEffect(() => {
    api.get('/companies')
      .then((list) => {
        setCompanies(list);
        if (list.length > 0) setCompanyId(String(list[0].id));
      })
      .catch((err) => setError(err.message));
  }, []);

  const loadData = async () => {
    if (!companyId) return;
    try {
      const [accountsData, eventsData] = await Promise.all([
        api.get(`/companies/${companyId}/social/accounts`),
        api.get(`/companies/${companyId}/social/webhooks`),
      ]);
      setAccounts(accountsData);
      setEvents(eventsData.items);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, [companyId]);

  const resetAccountForm = () => {
    setAccountForm({ provider: 'facebook', external_account_id: '', access_token: '' });
    setShowAccountForm(false);
  };

  const submitAccount = async (ev) => {
    ev.preventDefault();
    setError(null);
    try {
      await api.post(`/companies/${companyId}/social/accounts`, {
        provider: accountForm.provider,
        external_account_id: accountForm.external_account_id,
        access_token: accountForm.access_token || null,
      });
      resetAccountForm();
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteAccount = async (account) => {
    if (!window.confirm(`¿Eliminar la cuenta ${account.provider} (${account.external_account_id})?`)) return;
    try {
      await api.del(`/companies/${companyId}/social/accounts/${account.id}`);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const simulateWebhook = async (provider) => {
    // Simulación para pruebas desde el navegador
    const testPayload = {
      name: `Lead Simulado ${provider}`,
      email: `simulado-${provider}-${Date.now()}@test.local`,
      phone: '809-555-0000',
      message: 'Este lead fue simulado desde la interfaz.',
    };
    try {
      await api.post(`/companies/${companyId}/social/webhooks/${provider}`, testPayload);
      await loadData();
    } catch (err) {
      // Si falla, el evento igual se guardó
      await loadData();
      alert(`El webhook falló: ${err.message}`);
    }
  };

  return (
    <>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={input}>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <button
          onClick={() => { resetAccountForm(); setShowAccountForm(true); }}
          style={{ ...input, background: '#0d6efd', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
        >
          + Nueva Cuenta
        </button>
        <button
          onClick={() => simulateWebhook('facebook')}
          style={{ ...input, background: '#f8f9fa', border: '1px solid #ccc', cursor: 'pointer' }}
          title="Simula un webhook entrante de Facebook"
        >
          ⚡ Simular Webhook FB
        </button>
      </div>

      {error && <p style={{ color: 'crimson', fontWeight: 'bold' }}>Error: {error}</p>}

      {showAccountForm && (
        <form onSubmit={submitAccount} style={{ background: '#f6f8fa', padding: '1rem', borderRadius: 6, marginBottom: '1rem', border: '1px solid #ddd' }}>
          <h3 style={{ marginTop: 0 }}>Nueva Cuenta Social</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
            <Field label="Proveedor">
              <select value={accountForm.provider} onChange={(e) => setAccountForm({ ...accountForm, provider: e.target.value })} style={input}>
                {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="External Account ID *">
              <input required value={accountForm.external_account_id} onChange={(e) => setAccountForm({ ...accountForm, external_account_id: e.target.value })} style={input} placeholder="ej: page-123, wa-456..." />
            </Field>
            <Field label="Access Token (opcional)">
              <input type="password" value={accountForm.access_token} onChange={(e) => setAccountForm({ ...accountForm, access_token: e.target.value })} style={input} placeholder="Se guarda en backend" />
            </Field>
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <button type="submit" style={{ ...input, background: '#198754', color: 'white', border: 'none', cursor: 'pointer' }}>Crear cuenta</button>
            <button type="button" onClick={resetAccountForm} style={{ ...input, cursor: 'pointer' }}>Cancelar</button>
          </div>
        </form>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Panel Izquierdo: Cuentas */}
        <div>
          <h3>Cuentas Conectadas ({accounts.length})</h3>
          {accounts.length === 0 ? (
            <p style={{ color: '#888' }}>No hay cuentas conectadas.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#eee' }}>
                  <th style={th}>ID</th>
                  <th style={th}>Proveedor</th>
                  <th style={th}>External ID</th>
                  <th style={th}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((a) => (
                  <tr key={a.id}>
                    <td style={td}>{a.id}</td>
                    <td style={td}><strong>{a.provider}</strong></td>
                    <td style={td}><code>{a.external_account_id}</code></td>
                    <td style={td}>
                      <button onClick={() => deleteAccount(a)} style={{ ...btn, color: 'crimson' }}>Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Panel Derecho: Webhooks */}
        <div>
          <h3>Historial de Webhooks ({events.length})</h3>
          <p style={{ color: '#666', fontSize: '12px', marginTop: 0 }}>
            Cada intento de captación entrante (incluso si falla) se registra aquí.
          </p>
          {events.length === 0 ? (
            <p style={{ color: '#888' }}>No hay eventos registrados.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: '#eee' }}>
                  <th style={th}>ID</th>
                  <th style={th}>Proveedor</th>
                  <th style={th}>Estado</th>
                  <th style={th}>Detalle / Error</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id}>
                    <td style={td}>{e.id}</td>
                    <td style={td}>{e.provider}</td>
                    <td style={td}>
                      <span style={{ background: STATUS_COLORS[e.status] || '#999', color: 'white', padding: '2px 6px', borderRadius: 10, fontSize: '11px', fontWeight: 'bold' }}>
                        {e.status}
                      </span>
                    </td>
                    <td style={td}>
                      <div style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={e.error_message || e.payload}>
                        {e.error_message ? (
                          <span style={{ color: 'crimson' }}>{e.error_message}</span>
                        ) : (
                          <span style={{ color: '#666' }}>{e.payload.substring(0, 50)}...</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}

function Field({ label, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', fontSize: 13 }}>
      <span style={{ marginBottom: 2, fontWeight: 'bold' }}>{label}</span>
      {children}
    </label>
  );
}

const th = { padding: 6, border: '1px solid #ccc', textAlign: 'left' };
const td = { padding: 6, border: '1px solid #ccc' };
const input = { padding: '6px 8px', border: '1px solid #ccc', borderRadius: 4, font: 'inherit' };
const btn = { background: 'none', border: '1px solid #999', padding: '2px 6px', cursor: 'pointer', borderRadius: 3 };