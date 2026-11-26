import { useEffect, useState } from 'react';
import { api } from '../services/api';

const emptyForm = {
  name: '',
  email: '',
  phone: '',
  source: 'manual',
  status: 'new',
  notes: '',
};

const SOURCES = ['web', 'facebook', 'instagram', 'whatsapp', 'linkedin', 'manual', 'other'];
const STATUSES = ['new', 'contacted', 'qualified', 'converted', 'lost'];

const STATUS_COLORS = {
  new: '#0dcaf0',
  contacted: '#0d6efd',
  qualified: '#198754',
  converted: '#6c757d',
  lost: '#dc3545',
};

export default function LeadsPage() {
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState('');
  const [leads, setLeads] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  
  // Estado para el panel de actividades
  const [activeLead, setActiveLead] = useState(null);
  const [activities, setActivities] = useState([]);
  const [activityForm, setActivityForm] = useState({ activity_type: 'call', notes: '' });

  useEffect(() => {
    api.get('/companies')
      .then((list) => {
        setCompanies(list);
        if (list.length > 0) setCompanyId(String(list[0].id));
      })
      .catch((err) => setError(err.message));
  }, []);

  const loadLeads = async () => {
    if (!companyId) return;
    const qs = new URLSearchParams();
    if (search) qs.set('search', search);
    if (statusFilter) qs.set('status', statusFilter);
    if (sourceFilter) qs.set('source', sourceFilter);
    
    try {
      const data = await api.get(`/companies/${companyId}/leads?${qs.toString()}`);
      setLeads(data.items);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadLeads();
  }, [companyId, search, statusFilter, sourceFilter]);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(false);
    setError(null);
  };

  const loadLeadForEdit = (lead) => {
    setForm({
      name: lead.name,
      email: lead.email || '',
      phone: lead.phone || '',
      source: lead.source,
      status: lead.status,
      notes: lead.notes || '',
    });
    setEditingId(lead.id);
    setShowForm(true);
    setActiveLead(null);
  };

  const submitForm = async (ev) => {
    ev.preventDefault();
    setError(null);
    const payload = {
      name: form.name,
      email: form.email || null,
      phone: form.phone || null,
      source: form.source,
      status: form.status,
      notes: form.notes || null,
    };
    try {
      if (editingId) {
        await api.put(`/companies/${companyId}/leads/${editingId}`, payload);
      } else {
        await api.post(`/companies/${companyId}/leads`, payload);
      }
      resetForm();
      await loadLeads();
    } catch (err) {
      setError(err.message);
    }
  };

  const softDelete = async (lead) => {
    if (!window.confirm(`¿Dar de baja al lead "${lead.name}"?`)) return;
    try {
      await api.del(`/companies/${companyId}/leads/${lead.id}`);
      await loadLeads();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleConvert = async (lead) => {
    if (!window.confirm(`¿Convertir a "${lead.name}" en cliente?`)) return;
    try {
      await api.post(`/companies/${companyId}/leads/${lead.id}/convert`, {});
      await loadLeads();
      alert('Lead convertido a cliente exitosamente.');
    } catch (err) {
      setError(err.message);
    }
  };

  const openActivities = async (lead) => {
    setActiveLead(lead);
    try {
      const data = await api.get(`/companies/${companyId}/leads/${lead.id}`);
      setActivities(data.activities || []);
      setActivityForm({ activity_type: 'call', notes: '' });
    } catch (err) {
      setError(err.message);
    }
  };

  const submitActivity = async (ev) => {
    ev.preventDefault();
    try {
      await api.post(`/companies/${companyId}/leads/${activeLead.id}/activities`, activityForm);
      const data = await api.get(`/companies/${companyId}/leads/${activeLead.id}`);
      setActivities(data.activities || []);
      setActivityForm({ activity_type: 'call', notes: '' });
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={input}>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        
        <input
          type="text"
          placeholder="Buscar por nombre, email o teléfono..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ ...input, flex: 1, minWidth: 200 }}
        />

        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={input}>
          <option value="">Todos los estados</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} style={input}>
          <option value="">Todos los orígenes</option>
          {SOURCES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <button
          onClick={() => { resetForm(); setShowForm(true); }}
          style={{ ...input, background: '#0d6efd', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
        >
          + Nuevo Lead
        </button>
      </div>

      {error && <p style={{ color: 'crimson', fontWeight: 'bold' }}>Error: {error}</p>}

      {showForm && (
        <form onSubmit={submitForm} style={{ background: '#f6f8fa', padding: '1rem', borderRadius: 6, marginBottom: '1rem', border: '1px solid #ddd' }}>
          <h3 style={{ marginTop: 0 }}>{editingId ? 'Editar Lead' : 'Nuevo Lead'}</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
            <Field label="Nombre *">
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={input} />
            </Field>
            <Field label="Email">
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={input} />
            </Field>
            <Field label="Teléfono">
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} style={input} />
            </Field>
            <Field label="Origen">
              <select value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} style={input}>
                {SOURCES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Estado">
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} style={input}>
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Notas" full>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} style={{ ...input, minHeight: 60 }} />
            </Field>
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <button type="submit" style={{ ...input, background: '#198754', color: 'white', border: 'none', cursor: 'pointer' }}>
              {editingId ? 'Guardar cambios' : 'Crear lead'}
            </button>
            <button type="button" onClick={resetForm} style={{ ...input, cursor: 'pointer' }}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {activeLead && (
        <div style={{ background: '#fff3cd', padding: '1rem', borderRadius: 6, marginBottom: '1rem', border: '1px solid #ffc107' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h3 style={{ marginTop: 0 }}>Actividades de: {activeLead.name}</h3>
            <button onClick={() => setActiveLead(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem' }}>✖</button>
          </div>
          
          <ul style={{ paddingLeft: '1.2rem', marginBottom: '1rem' }}>
            {activities.length === 0 ? <li>No hay actividades registradas.</li> : activities.map(a => (
              <li key={a.id}>
                <strong>{a.activity_type.toUpperCase()}</strong> - {a.notes} <span style={{ color: '#666', fontSize: '0.85em' }}>({a.created_at.substring(0, 10)})</span>
              </li>
            ))}
          </ul>

          <form onSubmit={submitActivity} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
            <select value={activityForm.activity_type} onChange={(e) => setActivityForm({ ...activityForm, activity_type: e.target.value })} style={input}>
              <option value="call">Llamada</option>
              <option value="email">Email</option>
              <option value="meeting">Reunión</option>
              <option value="note">Nota</option>
            </select>
            <input required placeholder="Detalle de la actividad..." value={activityForm.notes} onChange={(e) => setActivityForm({ ...activityForm, notes: e.target.value })} style={{ ...input, flex: 1 }} />
            <button type="submit" style={{ ...input, background: '#0dcaf0', color: 'white', border: 'none', cursor: 'pointer' }}>Añadir</button>
          </form>
        </div>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
        <thead>
          <tr style={{ background: '#eee' }}>
            <th style={th}>ID</th>
            <th style={th}>Nombre</th>
            <th style={th}>Origen</th>
            <th style={th}>Estado</th>
            <th style={th}>Contacto</th>
            <th style={th}>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((l) => (
            <tr key={l.id}>
              <td style={td}>{l.id}</td>
              <td style={td}><strong>{l.name}</strong></td>
              <td style={td}>{l.source}</td>
              <td style={td}>
                <span style={{ background: STATUS_COLORS[l.status] || '#ccc', color: 'white', padding: '2px 8px', borderRadius: 12, fontSize: '12px', fontWeight: 'bold' }}>
                  {l.status}
                </span>
              </td>
              <td style={td}>
                <div>{l.email || '—'}</div>
                <div style={{ color: '#666', fontSize: '12px' }}>{l.phone || '—'}</div>
              </td>
              <td style={td}>
                <button onClick={() => loadLeadForEdit(l)} style={btn}>Editar</button>
                <button onClick={() => openActivities(l)} style={{ ...btn, color: '#0d6efd' }}>Actividades</button>
                {l.status !== 'converted' && l.status !== 'lost' && l.is_active && (
                  <button onClick={() => handleConvert(l)} style={{ ...btn, color: '#198754' }}>Convertir</button>
                )}
                {l.is_active && (
                  <button onClick={() => softDelete(l)} style={{ ...btn, color: 'crimson' }}>Baja</button>
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
      <span style={{ marginBottom: 2, fontWeight: 'bold' }}>{label}</span>
      {children}
    </label>
  );
}

const th = { padding: 8, border: '1px solid #726c6c', textAlign: 'left' };
const td = { padding: 8, border: '1px solid #ccc' };
const input = { padding: '6px 8px', border: '1px solid #ccc', borderRadius: 4, font: 'inherit' };
const btn = { background: 'none', border: '1px solid #999', padding: '4px 8px', marginRight: 4, cursor: 'pointer', borderRadius: 3 };