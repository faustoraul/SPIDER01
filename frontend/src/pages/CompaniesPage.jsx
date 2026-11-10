import { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function CompaniesPage() {
  const [companies, setCompanies] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const list = await api.get('/companies');
        const enriched = await Promise.all(
          list.map(async (c) => {
            const branches = await api.get(`/companies/${c.id}/branches`);
            return { ...c, branches };
          })
        );
        if (!cancelled) setCompanies(enriched);
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) return <p style={{ color: 'crimson' }}>Error: {error}</p>;

  return (
    <>
      <h2>Empresas ({companies.length})</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#eee' }}>
            <th style={th}>ID</th>
            <th style={th}>Nombre</th>
            <th style={th}>RNC</th>
            <th style={th}>Sucursales</th>
          </tr>
        </thead>
        <tbody>
          {companies.map((c) => (
            <tr key={c.id}>
              <td style={td}>{c.id}</td>
              <td style={td}>{c.name}</td>
              <td style={td}>{c.tax_id || '—'}</td>
              <td style={td}>
                {c.branches.length === 0 ? '—' : (
                  <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
                    {c.branches.map((b) => (
                      <li key={b.id}>{b.name} <span style={{ color: '#888' }}>({b.code})</span></li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

const th = { padding: 8, border: '1px solid #ccc', textAlign: 'left' };
const td = { padding: 8, border: '1px solid #ccc' };