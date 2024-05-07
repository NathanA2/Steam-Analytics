import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [steamId, setSteamId] = useState('');
  const [games, setGames] = useState([]);

  const fetchRecentlyPlayed = () => {
    fetch(`http://localhost:5000/steam/recently_played/${steamId}`)
      .then(response => response.json())
      .then(data => setGames(data.response.games))
      .catch(error => console.error('Error fetching Steam games:', error));
  };

  return (
    <div className="App">
      <header className="App-header">
        <input
          type="text"
          value={steamId}
          onChange={e => setSteamId(e.target.value)}
          placeholder="Enter Steam ID"
        />
        <button onClick={fetchRecentlyPlayed}>Fetch Games</button>
        <h2>Recently Played Games</h2>
        <ul>
          {games.map(game => (
            <li key={game.appid}>
              {game.name} - Played {game.playtime_2weeks} minutes in last 2 weeks
            </li>
          ))}
        </ul>
      </header>
    </div>
  );
}

export default App;