import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Predictor from './pages/Predictor';
import BMICalculator from './pages/BMICalculator';
import Chatbot from './pages/Chatbot';
import Login from './pages/Login';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  return (
    <Router>
      <nav>
        <div className="logo">PredictAI</div>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/predict">Symptom predictor</Link>
          <Link to="/bmi">BMI & diet</Link>
          <Link to="/chatbot">Health chat</Link>
          {token ? (
            <button onClick={logout} className="btn-outline" style={{padding: '6px 12px'}}>Logout</button>
          ) : (
            <Link to="/login" className="btn-primary" style={{padding: '6px 12px'}}>Login</Link>
          )}
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/predict" element={<Predictor />} />
        <Route path="/bmi" element={<BMICalculator />} />
        <Route path="/chatbot" element={<Chatbot />} />
        <Route path="/login" element={<Login setToken={setToken} />} />
      </Routes>
    </Router>
  );
}

export default App;
