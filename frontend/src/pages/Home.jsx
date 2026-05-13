import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiUrl } from '../api';

function Home() {
  const [tip, setTip] = useState('');

  useEffect(() => {
    fetch(apiUrl('/api/health-tip'))
      .then((r) => r.json())
      .then((d) => setTip(d.tip || ''))
      .catch(() => setTip('Stay hydrated and seek professional care when symptoms are severe or unclear.'));
  }, []);

  return (
    <div className="container animate-fade-in">
      <div className="hero">
        <h1>
          PredictAI — <span className="logo">disease prediction using symptoms</span>
        </h1>
        <p>
          A clean B.Tech–style full-stack demo: type symptoms in natural language, map them to a dataset vocabulary, run a
          Random Forest classifier for the top three labels, explore BMI-based diet hints, and chat with a small rule-based
          assistant. Educational only — not for real diagnosis.
        </p>
        <Link to="/predict" className="btn-primary">
          Start symptom analysis
        </Link>
      </div>

      {tip && (
        <div className="glass-card daily-tip-card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>Daily health tip</h3>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>{tip}</p>
        </div>
      )}

      <div className="grid" style={{ marginTop: '40px' }}>
        <div className="glass-card">
          <div style={{ fontSize: '2rem', marginBottom: '16px' }}>01</div>
          <h3>Dynamic symptom text</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '10px' }}>
            Comma-separated phrases, aliases (e.g. “fever”), and fuzzy matching to the closest known symptom name before ML
            inference.
          </p>
        </div>
        <div className="glass-card">
          <div style={{ fontSize: '2rem', marginBottom: '16px' }}>02</div>
          <h3>Top 3 diseases + severity</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '10px' }}>
            Probabilities from the model, severity bands from symptom count, and a doctor warning when many symptoms are
            present.
          </p>
        </div>
        <div className="glass-card">
          <div style={{ fontSize: '2rem', marginBottom: '16px' }}>03</div>
          <h3>BMI, PDF report & history</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '10px' }}>
            BMI categories with eat / avoid lists, downloadable PDF summary, SQLite + localStorage history, and a keyword
            health chatbot.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Home;
