import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [gameName, setGameName] = useState('');
  const [games, setGames] = useState([]);

  useEffect(() => {
    fetch('http://localhost:5000/games')
      .then(response => response.json())
      .then(data => setGames(data))
      .catch(error => console.error('Error fetching games:', error));
  }, []);

  const handleInputChange = (e) => {
    setGameName(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('http://localhost:5000/games/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name: gameName }),
    })
      .then(response => response.json())
      .then(data => {
        alert('Game added successfully');
        setGames([...games, { name: gameName }]);
        setGameName('');
      })
      .catch(error => console.error('Error adding game:', error));
  };

  const handleDelete = (gameName) => {
    fetch('http://localhost:5000/games/delete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name: gameName }),
    })
      .then(response => response.json())
      .then(data => {
        alert(data.message);
        if (data.message === "Game deleted successfully") {
          setGames(games.filter(game => game.name !== gameName));
        }
      })
      .catch(error => console.error('Error deleting game:', error));
  };

  return (
    <div className="App">
      <header className="App-header">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={gameName}
            onChange={handleInputChange}
            placeholder="Enter game name"
            required
          />
          <button type="submit">Add Game</button>
        </form>
        <h2>Games List</h2>
        <ul>
          {games.map((game, index) => (
            <li key={index}>
              {game.name} <button onClick={() => handleDelete(game.name)}>Delete</button>
            </li>
          ))}
        </ul>
      </header>
    </div>
  );
}

export default App;