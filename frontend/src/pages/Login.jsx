import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiUrl } from '../api';

function Login({ setToken }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const endpoint = isLogin ? '/api/login' : '/api/register';
    
    try {
      const res = await fetch(apiUrl(endpoint), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }
      
      if (isLogin) {
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        navigate('/');
      } else {
        setIsLogin(true); // Switch to login after register
        alert('Registered successfully! Please login.');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container animate-fade-in" style={{display: 'flex', justifyContent: 'center', marginTop: '100px'}}>
      <div className="glass-card form-container" style={{width: '100%'}}>
        <h2 style={{textAlign: 'center', marginBottom: '24px'}}>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
        
        {error && <div className="badge danger" style={{display: 'block', marginBottom: '16px', textAlign: 'center'}}>{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <input 
            type="text" 
            placeholder="Username" 
            className="input-field" 
            value={username} 
            onChange={e => setUsername(e.target.value)} 
            required 
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="input-field" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
            required 
          />
          
          <button type="submit" className="btn-primary" style={{width: '100%', marginTop: '8px'}}>
            {isLogin ? 'Login to Dashboard' : 'Register'}
          </button>
        </form>
        
        <div style={{textAlign: 'center', marginTop: '20px'}}>
          <p style={{color: 'var(--text-secondary)'}}>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <span 
              onClick={() => setIsLogin(!isLogin)} 
              style={{color: 'var(--accent-primary)', cursor: 'pointer', fontWeight: '500'}}
            >
              {isLogin ? 'Sign up' : 'Log in'}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
