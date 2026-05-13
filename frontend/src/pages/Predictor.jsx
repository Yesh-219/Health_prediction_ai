import React, { useState, useEffect, useRef } from 'react';
import { apiUrl } from '../api';

const HISTORY_KEY = 'predictai_recent';
const LOADING_STEPS = ['Analyzing symptoms…', 'Matching to medical vocabulary…', 'Running ML model…', 'Preparing diet hints…'];

function loadLocalHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveLocalHistory(entry) {
  const prev = loadLocalHistory();
  const next = [entry, ...prev.filter((e) => e.symptom_text !== entry.symptom_text)].slice(0, 5);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

function Predictor() {
  const [symptomText, setSymptomText] = useState('');
  const [allSymptoms, setAllSymptoms] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadStep, setLoadStep] = useState(0);
  const [error, setError] = useState(null);
  const [localHistory, setLocalHistory] = useState(loadLocalHistory);
  const [serverHistory, setServerHistory] = useState([]);
  const timerRef = useRef(null);

  useEffect(() => {
    fetch(apiUrl('/api/symptoms'))
      .then((res) => res.json())
      .then((data) => {
        const list = Array.isArray(data) ? data : data.symptoms || [];
        setAllSymptoms(list);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch(apiUrl('/api/history?limit=5'))
      .then((r) => r.json())
      .then((d) => setServerHistory(d.items || []))
      .catch(() => {});
  }, [results]);

  useEffect(() => {
    if (!loading) {
      setLoadStep(0);
      if (timerRef.current) clearInterval(timerRef.current);
      return undefined;
    }
    timerRef.current = setInterval(() => {
      setLoadStep((s) => (s + 1) % LOADING_STEPS.length);
    }, 900);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [loading]);

  const appendChip = (sym) => {
    const label = sym.replaceAll('_', ' ');
    setSymptomText((t) => {
      const trimmed = t.trim();
      if (!trimmed) return label;
      if (trimmed.endsWith(',')) return `${trimmed} ${label}`;
      return `${trimmed}, ${label}`;
    });
  };

  const handlePredict = async () => {
    if (!symptomText.trim()) {
      setError('Describe at least one symptom (e.g. fever, headache, vomiting).');
      return;
    }
    setError(null);
    setLoading(true);
    setResults(null);

    try {
      const response = await fetch(apiUrl('/api/predict'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptom_text: symptomText.trim(), symptoms: [] }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Prediction failed');
      setResults(data);
      saveLocalHistory({
        time: new Date().toISOString(),
        symptom_text: data.symptom_text || symptomText.trim(),
        predictions: data.predictions,
        severity: data.severity,
      });
      setLocalHistory(loadLocalHistory());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSymptomText('');
    setResults(null);
    setError(null);
    setLoading(false);
  };

  const downloadPdf = async () => {
    if (!results) return;
    let bmi = null;
    try {
      const raw = sessionStorage.getItem('predictai_last_bmi');
      if (raw) bmi = JSON.parse(raw);
    } catch {
      bmi = null;
    }

    const diet = {
      foods_eat: results.foods || [],
      foods_avoid: results.foods_avoid || [],
    };

    const payload = {
      symptom_text: results.symptom_text || symptomText,
      matched_symptoms: results.matched_symptoms || [],
      predictions: results.predictions || [],
      severity: results.severity,
      doctor_warning: results.doctor_warning,
      bmi: bmi
        ? { value: bmi.value, category: bmi.category, tips: bmi.tips }
        : { value: null, category: 'Not recorded (use BMI page first)', tips: [] },
      diet,
      suggestions: results.suggestions || [],
    };

    const res = await fetch(apiUrl('/api/report/pdf'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      alert('Could not generate PDF.');
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'predictai_health_report.pdf';
    a.click();
    URL.revokeObjectURL(url);
  };

  const severityClass =
    results?.severity === 'Mild' ? 'success' : results?.severity === 'Moderate' ? 'warning' : 'danger';

  return (
    <div className="container">
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2>PredictAI — disease prediction</h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '640px', margin: '0 auto' }}>
          Type symptoms in your own words. We map them to dataset columns (keywords + fuzzy matching), run a Random Forest
          model, and show the top three labels with demo probabilities — for learning only, not diagnosis.
        </p>
      </div>

      <div className="glass-card">
        <h3>Your symptoms</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '8px' }}>
          Example: <em>fever, headache, vomiting, cough</em>
        </p>
        <textarea
          className="input-field"
          rows={4}
          style={{ resize: 'vertical', minHeight: '100px', fontFamily: 'inherit' }}
          placeholder="Describe how you feel…"
          value={symptomText}
          onChange={(e) => setSymptomText(e.target.value)}
        />

        {allSymptoms.length > 0 && (
          <div style={{ marginTop: '8px' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Quick add:</span>
            <div
              style={{
                marginTop: '8px',
                display: 'flex',
                flexWrap: 'wrap',
                gap: '8px',
                maxHeight: '120px',
                overflowY: 'auto',
              }}
            >
              {allSymptoms.slice(0, 40).map((sym) => (
                <button
                  key={sym}
                  type="button"
                  onClick={() => appendChip(sym)}
                  className="btn-outline"
                  style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  {sym.replaceAll('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && <p className="badge danger" style={{ display: 'block', marginTop: '12px' }}>{error}</p>}

        <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
          <button type="button" className="btn-primary" style={{ flex: '1 1 160px' }} onClick={handlePredict} disabled={loading}>
            {loading ? 'Working…' : 'Analyze symptoms'}
          </button>
          <button type="button" className="btn-outline" onClick={handleReset} disabled={loading}>
            Reset
          </button>
        </div>

        {loading && (
          <div className="loading-panel">
            <div className="loading-dots" aria-hidden />
            <p className="loading-text">{LOADING_STEPS[loadStep]}</p>
          </div>
        )}
      </div>

      {(localHistory.length > 0 || serverHistory.length > 0) && (
        <div className="glass-card" style={{ marginTop: '24px' }}>
          <h3>Recent predictions</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '6px' }}>
            Last 5 on this device (localStorage) and last entries saved by the API (SQLite).
          </p>
          {localHistory.length > 0 && (
            <ul style={{ marginTop: '12px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
              {localHistory.map((h, i) => (
                <li key={i} style={{ marginBottom: '8px' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>{h.symptom_text}</strong> —{' '}
                  {(h.predictions || []).map((p) => p.disease).join(', ') || '—'} ({h.severity})
                </li>
              ))}
            </ul>
          )}
          {serverHistory.length > 0 && (
            <>
              <h4 style={{ marginTop: '16px', fontSize: '1rem' }}>From server</h4>
              <ul style={{ marginTop: '8px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
                {serverHistory.map((h) => (
                  <li key={h.id} style={{ marginBottom: '8px' }}>
                    {(h.matched_symptoms || []).map((s) => s.replaceAll('_', ' ')).join(', ')} →{' '}
                    {(h.predictions || []).map((p) => p.disease).join(', ')}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {results && (
        <div style={{ marginTop: '24px' }} className="animate-fade-in">
          {results.doctor_warning && (
            <div className="glass-card alert-doctor">
              <strong>Please consult a doctor immediately.</strong> You entered many symptoms at once; this may indicate a
              serious condition that needs in-person evaluation.
            </div>
          )}

          {results.did_you_mean?.length > 0 && (
            <div className="glass-card" style={{ marginTop: '16px' }}>
              <h3>Did you mean?</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '6px' }}>
                We corrected close spellings to the nearest known symptom:
              </p>
              <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
                {results.did_you_mean.map((d, i) => (
                  <li key={i}>
                    “{d.typed}” → <strong>{d.suggestion}</strong>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {results.unmatched_tokens?.length > 0 && (
            <div className="glass-card" style={{ marginTop: '16px', borderColor: 'rgba(245, 158, 11, 0.4)' }}>
              <h3>Not recognized</h3>
              <p style={{ color: 'var(--text-secondary)' }}>These phrases were not mapped: {results.unmatched_tokens.join(', ')}</p>
            </div>
          )}

          <div className="glass-card" style={{ marginTop: '16px' }}>
            <h3>Mapped symptoms</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
              {(results.matched_symptoms || []).map((s) => (
                <span key={s} className="badge success">
                  {s.replaceAll('_', ' ')}
                </span>
              ))}
            </div>
            <p style={{ marginTop: '16px' }}>
              <strong>Severity (by count):</strong>{' '}
              <span className={`badge ${severityClass}`}>{results.severity}</span>{' '}
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                (1–2 mild, 3–4 moderate, 5+ severe)
              </span>
            </p>
          </div>

          <div className="glass-card" style={{ marginTop: '16px' }}>
            <h3>Top 3 predicted conditions</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '6px' }}>Percentages from model outputs (demo).</p>
            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {(results.predictions || []).map((p, i) => (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>{p.disease}</span>
                    <strong>{Number(p.probability).toFixed(1)}%</strong>
                  </div>
                  <div className="prob-bar">
                    <div className="prob-bar-fill" style={{ width: `${Math.min(100, p.probability)}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <button type="button" className="btn-outline" style={{ marginTop: '20px' }} onClick={downloadPdf}>
              Download health report (PDF)
            </button>
          </div>

          <div className="glass-card" style={{ marginTop: '16px' }}>
            <h3>Diet & recovery hints</h3>
            <h4 style={{ marginTop: '12px', fontSize: '0.95rem' }}>Possible deficiencies (educational)</h4>
            <ul style={{ marginTop: '8px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
              {(results.deficiencies || []).map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
            <h4 style={{ marginTop: '16px', fontSize: '0.95rem' }}>Foods to emphasize</h4>
            <ul style={{ marginTop: '8px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
              {(results.foods || []).map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
            <h4 style={{ marginTop: '16px', fontSize: '0.95rem' }}>Foods to limit / avoid</h4>
            <ul style={{ marginTop: '8px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
              {(results.foods_avoid || []).map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
            <h4 style={{ marginTop: '16px', fontSize: '0.95rem' }}>Suggestions</h4>
            <ul style={{ marginTop: '8px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
              {(results.suggestions || []).map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default Predictor;
