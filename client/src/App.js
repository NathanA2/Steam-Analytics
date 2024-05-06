import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch('http://localhost:5000/')
      .then(response => response.text())
      .then(message => setMessage(message));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <p>
          Message from the backend: {message}
        </p>
      </header>
    </div>
  );
}

export default App;