import React, { useState } from 'react';
import { apiUrl } from '../api';

function Chatbot() {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hi! I am the PredictAI assistant. Ask about BMI, fever, cough, diet, hydration, or how the symptom predictor works.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { sender: 'bot', text: data.reply }]);
    } catch(err) {
      setMessages(prev => [...prev, { sender: 'bot', text: "Sorry, I'm having trouble connecting right now." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container animate-fade-in" style={{display: 'flex', flexDirection: 'column', height: 'calc(100vh - 150px)'}}>
      <div style={{textAlign: 'center', marginBottom: '20px'}}>
        <h2>PredictAI Health Assistant</h2>
        <p style={{color: 'var(--text-secondary)'}}>Rule-based answers for common questions (BMI, diet, symptoms). Not a replacement for a doctor.</p>
      </div>

      <div className="glass-card" style={{flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div style={{flexGrow: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px'}}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              background: msg.sender === 'user' ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))' : 'rgba(255,255,255,0.1)',
              padding: '12px 16px',
              borderRadius: '16px',
              borderBottomRightRadius: msg.sender === 'user' ? '4px' : '16px',
              borderBottomLeftRadius: msg.sender === 'bot' ? '4px' : '16px',
              maxWidth: '70%',
              boxShadow: '0 4px 15px rgba(0,0,0,0.1)'
            }}>
              {msg.text}
            </div>
          ))}
          {loading && (
            <div style={{alignSelf: 'flex-start', background: 'rgba(255,255,255,0.1)', padding: '12px 16px', borderRadius: '16px', borderBottomLeftRadius: '4px'}}>
              Thinking...
            </div>
          )}
        </div>

        <form onSubmit={sendMessage} style={{display: 'flex', gap: '10px', marginTop: '20px', paddingTop: '20px', borderTop: '1px solid var(--border-color)'}}>
          <input 
            type="text" 
            className="input-field" 
            style={{marginBottom: '0', flexGrow: 1}}
            placeholder="Type your health query..." 
            value={input} 
            onChange={e => setInput(e.target.value)} 
          />
          <button type="submit" className="btn-primary" disabled={loading}>Send</button>
        </form>
      </div>
    </div>
  );
}

export default Chatbot;
