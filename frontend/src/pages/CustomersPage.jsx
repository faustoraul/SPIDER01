import { useEffect, useState } from 'react';
import { api } from '../services/api';

const emptyForm = {
  customer_type: 'individual',
  identification: '',
  name: '',
  email: '',
  phone: '',
  address: '',
  notes: '',
};

export default function CustomersPage() {
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState('');
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [includeInactive, setIncludeInactive] = useState(false);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    api.get('/companies')
      .then((list) => {
        setCompanies(list);
        if (list.length > 0) setCompanyId(String(list[0].id));
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!companyId) return;
    let cancelled = false;
    const qs = new URLSearchParams();
    if (search) qs.set('search', search);
    if (includeInactive) qs.set('include_inactive', '1');
    api.get(`/companies/${companyId}/customers?${qs.toString()}`)
      .then((data) => {
        if (!cancelled) setCustomers(data.items);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [companyId, search, includeInactive]);

  const reload = async () => {
    const qs = new URLSearchParams();
    if (search) qs.set('search', search);
    if (includeInactive) qs.set('include_inactive', '1');
    const data = await api.get(`/companies/${companyId}/customers?${qs.toString()}`);
    setCustomers(data.items);
  };

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(false);
    setError(null);
  };

  const loadCustomer = (c) => {
    setForm({
      customer_type: c.customer_type,
      identification: c.identification || '',
      name: c.name,
      email: c.email || '',
      phone: c.phone || '',
      address: c.address || '',
      notes: c.notes || '',
    });
    setEditingId(c.id);
    setShowForm(true);
  };

  const submitForm = async (ev) => {
    ev.preventDefault();
    setError(null);
    const payload = {
      customer_type: form.customer_type,
      identification: form.identification || null,
      name: form.name,
      email: form.email || null,
      phone: form.phone || null,
      address: form.address || null,
      notes: form.notes || null,
    };
    try {
      if (editingId) {
        await api.put(`/companies/${companyId}/customers/${editingId}`, payload);
      } else {
        await api.post(`/companies/${companyId}/customers`, payload);
      }
      resetForm();
      await reload();
    } catch (err) {
      setError(err.message);
    }
  };

  const softDelete = async (c) => {
    if (!window.confirm(`¿Dar de baja a "${c.name}"?`)) return;
    try {
      await api.del(`/companies/${companyId}/customers/${c.id}`);
      await reload();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={input}>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Buscar por nombre, identificación o email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ ...input, flex: 1, minWidth: 260 }}
        />
        <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}>
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          Incluir inactivos
        </label>
        <button
          onClick={() => { resetForm(); setShowForm(true); }}
          style={{ ...input, background: '#0d6efd', color: 'white', border: 'none', cursor: 'pointer' }}
        >
          Nuevo cliente
        </button>
      </div>

      {error && <p style={{ color: 'crimson' }}>Error: {error}</p>}

      {showForm && (
        <form
          onSubmit={submitForm}
          style={{ background: '#f6f8fa', padding: '1rem', borderRadius: 6, marginBottom: '1rem' }}
        >
          <h3 style={{ marginTop: 0 }}>{editingId ? 'Editar cliente' : 'Nuevo cliente'}</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
            <Field label="Nombre *">
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={input} />
            </Field>
            <Field label="Tipo">
              <select value={form.customer_type} onChange={(e) => setForm({ ...form, customer_type: e.target.value })} style={input}>
                <option value="individual">Individual</option>
                <option value="company">Empresa</option>
              </select>
            </Field>
            <Field label="Identificación (cédula/RNC)">
              <input value={form.identification} onChange={(e) => setForm({ ...form, identification: e.target.value })} style={input} />
            </Field>
            <Field label="Email">
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={input} />
            </Field>
            <Field label="Teléfono">
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} style={input} />
            </Field>
            <Field label="Dirección">
              <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} style={input} />
            </Field>
            <Field label="Notas" full>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} style={{ ...input, minHeight: 60 }} />
            </Field>
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <button type="submit" style={{ ...input, background: '#198754', color: 'white', border: 'none', cursor: 'pointer' }}>
              {editingId ? 'Guardar cambios' : 'Crear cliente'}
            </button>
            <button type="button" onClick={resetForm} style={{ ...input, cursor: 'pointer' }}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#eee' }}>
            <th style={th}>ID</th>
            <th style={th}>Nombre</th>
            <th style={th}>Tipo</th>
            <th style={th}>Identificación</th>
            <th style={th}>Email</th>
            <th style={th}>Activo</th>
            <th style={th}>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((c) => (
            <tr key={c.id}>
              <td style={td}>{c.id}</td>
              <td style={td}>{c.name}</td>
              <td style={td}>{c.customer_type}</td>
              <td style={td}>{c.identification || '—'}</td>
              <td style={td}>{c.email || '—'}</td>
              <td style={td}>{c.is_active ? 'Sí' : 'No'}</td>
              <td style={td}>
                <button onClick={() => loadCustomer(c)} style={btn}>Editar</button>
                {c.is_active && (
                  <button onClick={() => softDelete(c)} style={{ ...btn, color: 'crimson' }}>
                    Dar de baja
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function Field({ label, children, full }) {
  return (
    <label style={{ gridColumn: full ? '1 / -1' : 'auto', display: 'flex', flexDirection: 'column', fontSize: 13 }}>
      <span style={{ marginBottom: 2 }}>{label}</span>
      {children}
    </label>
  );
}

const th = { padding: 8, border: '1px solid #ccc', textAlign: 'left' };
const td = { padding: 8, border: '1px solid #ccc' };
const input = { padding: '6px 8px', border: '1px solid #ccc', borderRadius: 4, font: 'inherit' };
const btn = { background: 'none', border: '1px solid #999', padding: '4px 8px', marginRight: 6, cursor: 'pointer' };