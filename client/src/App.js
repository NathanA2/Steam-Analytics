import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

function App() {
  const [steamId, setSteamId] = useState('');
  const [games, setGames] = useState([]);

  const fetchRecentlyPlayed = () => {
    fetch(`http://localhost:5000/steam/games_genres/${steamId}`)
      .then(response => response.json())
      .then(data => {
        setGames(data);
      })
      .catch(error => console.error('Error fetching Steam games:', error));
  };

  const genreData = games.reduce((acc, game) => {
    game.genres.forEach(genre => {
      const found = acc.find(item => item.name === genre);
      if (found) {
        found.value += 1;
      } else {
        acc.push({ name: genre, value: 1 });
      }
    });
    return acc;
  }, []);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#9900FF'];

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
            <li key={game.appid}>{game.name} - Played {game.playtime_2weeks} minutes in last 2 weeks</li>
          ))}
        </ul>
        <h2>Most Played Genres</h2>
        <div className="Chart-container">
          <ResponsiveContainer width="100%" height={400}>
            <PieChart width={740} height={400}>
              <Pie dataKey="value" isAnimationActive={false} data={genreData} cx={370} cy={200} outerRadius={160} fill="#8884d8" label>
                {genreData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              {/* Legend component removed */}
            </PieChart>
          </ResponsiveContainer>
        </div>
      </header>
    </div>
  );
}

export default App;