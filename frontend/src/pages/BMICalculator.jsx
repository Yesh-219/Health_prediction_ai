import React, { useState } from 'react';
import { apiUrl } from '../api';

function BMICalculator() {
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const calculateBMI = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch(apiUrl('/api/bmi'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          weight_kg: parseFloat(weight),
          height_cm: parseFloat(height)
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setResult(data);
      sessionStorage.setItem(
        'predictai_last_bmi',
        JSON.stringify({
          value: data.bmi,
          category: data.category || data.status,
          tips: data.tips || data.health_suggestions || [],
          foods: data.foods || [],
          foods_avoid: data.foods_avoid || [],
        })
      );
    } catch(err) {
      setError(err.message);
    }
  };

  return (
    <div className="container animate-fade-in">
      <div style={{textAlign: 'center', marginBottom: '40px'}}>
        <h2>BMI & diet suggestions</h2>
        <p style={{color: 'var(--text-secondary)'}}>Get your BMI category, practical food ideas, and foods to limit — educational only, not medical advice.</p>
      </div>

      <div className="grid">
        <div className="glass-card">
          <h3>Enter Metrics</h3>
          <form onSubmit={calculateBMI} style={{marginTop: '20px'}}>
            <label style={{display: 'block', marginBottom: '8px', color: 'var(--text-secondary)'}}>Weight (kg)</label>
            <input 
              type="number" 
              className="input-field" 
              value={weight} 
              onChange={e => setWeight(e.target.value)} 
              required 
              min="10"
              step="0.1"
            />
            
            <label style={{display: 'block', marginBottom: '8px', color: 'var(--text-secondary)'}}>Height (cm)</label>
            <input 
              type="number" 
              className="input-field" 
              value={height} 
              onChange={e => setHeight(e.target.value)} 
              required 
              min="50"
            />
            
            {error && <div className="badge danger" style={{marginBottom: '10px'}}>{error}</div>}
            
            <button type="submit" className="btn-primary" style={{width: '100%'}}>Calculate Wellness Plan</button>
          </form>
        </div>

        {result && (
          <div className="glass-card animate-fade-in">
            <h3>Your Results</h3>
            <div style={{marginTop: '20px', textAlign: 'center'}}>
              <div style={{fontSize: '3rem', fontWeight: 'bold', color: 'var(--accent-primary)'}}>{result.bmi}</div>
              <div className={`badge ${
                (result.category || result.status) === 'Normal' ? 'success' :
                (result.category || result.status) === 'Underweight' ? 'warning' : 'warning'
              }`} style={{fontSize: '1rem', marginTop: '10px'}}>
                {result.category || result.status}
              </div>
              <p style={{marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.95rem'}}>
                {(result.category || result.status) === 'Underweight' && 'Focus on nutrient-dense meals and gradual weight gain with professional guidance if needed.'}
                {(result.category || result.status) === 'Normal' && 'Great baseline — keep balanced meals and regular movement.'}
                {(result.category || result.status) === 'Overweight' && 'Small sustainable changes in portions and activity usually work best.'}
                {(result.category || result.status) === 'Obese' && 'A clinician can help design a safe, long-term plan tailored to you.'}
              </p>
            </div>

            <div style={{marginTop: '30px'}}>
              <strong>Recommended Foods to Eat:</strong>
              <div style={{display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap'}}>
                {result.foods.map((f, i) => <span key={i} className="badge success">{f}</span>)}
              </div>
            </div>

            <div style={{marginTop: '20px'}}>
              <strong>Foods to limit / avoid:</strong>
              <div style={{display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap'}}>
                {(result.foods_avoid || []).map((f, i) => <span key={i} className="badge danger">{f}</span>)}
              </div>
            </div>

            <div style={{marginTop: '20px'}}>
              <strong>Health suggestions:</strong>
              <ul style={{marginTop: '8px', paddingLeft: '20px', color: 'var(--text-secondary)'}}>
                {(result.health_suggestions || result.tips || []).map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default BMICalculator;
